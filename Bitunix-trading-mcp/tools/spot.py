import asyncio
from fastmcp import FastMCP
from client import SpotClient, BitunixClient

_client = SpotClient()
_futures = BitunixClient()


def _get_spot_balance(spot_data, coin: str) -> float:
    """Extract available balance for a coin from get_spot_account response."""
    if isinstance(spot_data, list):
        for entry in spot_data:
            if entry.get("coin") == coin:
                return float(entry.get("balance", 0) or 0)
    return 0.0


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_spot_account() -> dict:
        """
        Get all spot wallet balances (separate from futures account).
        Returns available and locked amounts for every coin in the spot wallet.
        """
        try:
            data = await _client.get_spot_account()
            if not data:
                return {"data": [], "note": "Spot wallet is empty"}
            return {"data": data}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def funds_transfer(transfer_type: str, coin: str, amount: str) -> dict:
        """
        Transfer funds between the Spot wallet and the Futures wallet.
        Spot and Futures are SEPARATE accounts — this transfer is required for currency conversion.

        transfer_type:
          "futures_spot" — move coin FROM futures TO spot wallet
          "spot_futures" — move coin FROM spot TO futures wallet

        coin:   e.g. "USDT", "USDC", "BTC"
        amount: quantity as string, e.g. "13.5"

        Example — move 13 USDC from futures to spot before converting:
          transfer_type="futures_spot"  coin="USDC"  amount="13"

        Example — move 13 USDT from spot back to futures after converting:
          transfer_type="spot_futures"  coin="USDT"  amount="13"
        """
        if transfer_type not in ("futures_spot", "spot_futures"):
            return {"error": "transfer_type must be 'futures_spot' or 'spot_futures'"}
        try:
            result = await _client.funds_transfer(transfer_type, coin, amount)
            direction = "Futures -> Spot" if transfer_type == "futures_spot" else "Spot -> Futures"
            return {"success": True, "transferred": f"{amount} {coin}", "direction": direction, "data": result}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def convert_currency(
        from_coin: str,
        to_coin: str,
        amount: str,
        wallet: str = "futures",
    ) -> dict:
        """
        Convert one currency to another within Bitunix.

        IMPORTANT: Spot and Futures are separate wallets. This tool:
          1. Transfers from_coin from futures to spot  (if wallet="futures")
          2. Sells from_coin for to_coin via spot MARKET order
          3. Gets received to_coin balance from spot
          4. Transfers to_coin back to futures          (if wallet="futures")
          On any failure after step 1, automatically transfers from_coin back to futures.

        from_coin: coin to sell, e.g. "USDC"
        to_coin:   coin to receive, e.g. "USDT"
        amount:    quantity of from_coin, e.g. "13"
        wallet:    "futures" (default) or "spot"

        Supported: USDC<->USDT, BTC<->USDT, ETH<->USDT, BTC<->USDC

        Example — convert all USDC to USDT, funds in futures:
          from_coin="USDC"  to_coin="USDT"  amount="14"  wallet="futures"
        """
        return await convert_currency_impl(from_coin, to_coin, amount, wallet)


async def convert_currency_impl(
    from_coin: str,
    to_coin: str,
    amount: str,
    wallet: str = "futures",
) -> dict:
    log = []

    # Resolve spot symbol and side
    # side 1 = Sell base coin, side 2 = Buy base coin
    PAIRS = {
        ("USDC", "USDT"): ("USDCUSDT", 1),  # Sell USDC -> get USDT
        ("USDT", "USDC"): ("USDCUSDT", 2),  # Buy USDC with USDT
        ("BTC",  "USDT"): ("BTCUSDT",  1),
        ("USDT", "BTC"):  ("BTCUSDT",  2),
        ("ETH",  "USDT"): ("ETHUSDT",  1),
        ("USDT", "ETH"):  ("ETHUSDT",  2),
        ("BTC",  "USDC"): ("BTCUSDC",  1),
        ("USDC", "BTC"):  ("BTCUSDC",  2),
    }
    key = (from_coin.upper(), to_coin.upper())
    if key not in PAIRS:
        return {"error": f"Unsupported pair {from_coin}/{to_coin}. Supported: USDC/USDT, BTC/USDT, ETH/USDT, BTC/USDC"}

    symbol, side = PAIRS[key]
    transferred = False
    final_amount = amount

    try:
        # ── Step 1: Handle Futures -> Spot Transfer ───────────────────
        if wallet == "futures":
            log.append(f"[1] Checking futures {from_coin} balance")
            acc = await _futures.get_account(from_coin)
            # 'transfer' is the amount actually movable without closing positions
            movable = float(acc.get("transfer", acc.get("available", 0)) or 0)
            available = float(acc.get("available", 0) or 0)
            
            req_amount = float(amount)
            if req_amount > movable:
                log.append(f"    WARNING: Requested {req_amount}, but only {movable} is transferable (Available: {available})")
                if movable <= 0:
                    raise RuntimeError(f"No transferable {from_coin} found in futures account. Check your open positions/margin.")
                final_amount = str(movable)
                log.append(f"    Adjusting transfer to {final_amount}")
            
            # Truncate to 4 decimals for the transfer API safety
            final_amount = f"{float(final_amount):.4f}".rstrip("0").rstrip(".")
            log.append(f"    Transferring {final_amount} {from_coin}: futures -> spot")
            await _client.funds_transfer("futures_spot", from_coin, final_amount)
            transferred = True
            log.append(f"    OK")
            # Wait for balance to settle
            await asyncio.sleep(1.5)

        # ── Step 2: Verify spot balance before ordering ───────────────
        spot_data = await _client.get_spot_account()
        spot_available = _get_spot_balance(spot_data, from_coin)
        log.append(f"[2] Spot {from_coin} available: {spot_available}")

        if spot_available <= 0:
            # One retry if balance hasn't updated
            await asyncio.sleep(2)
            spot_data = await _client.get_spot_account()
            spot_available = _get_spot_balance(spot_data, from_coin)
            if spot_available <= 0:
                raise RuntimeError(f"No {from_coin} found in spot wallet after transfer/check")

        # BUG FIX: Use safer precision (2 decimals) for USDC/USDT volume to avoid rejection.
        # Most spot pairs on BitUnix handle 2-4 decimals for volume.
        trade_amount = f"{spot_available:.2f}"
        log.append(f"    Trade amount (refined precision): {trade_amount}")

        # ── Step 3: Spot MARKET order ─────────────────────────────────
        action = "Sell" if side == 1 else "Buy"
        log.append(f"[3] Spot MARKET {action} {trade_amount} {from_coin} on {symbol}")
        order = await _client.spot_place_order(
            symbol=symbol,
            side=side,
            order_type=2,  # MARKET
            volume=trade_amount,
            price="0",
        )
        
        # Extract order ID (spot might use orderId or order_id)
        # The client now raises RuntimeError for internal engine failures (placeCode != 0),
        # so if we reach here, the order was likely accepted.
        order_id = order.get("orderId") or order.get("order_id") or "unknown"
        log.append(f"    OK: orderId={order_id}")
        
        # If for some reason we still have unknown orderId, check if it was actually accepted
        if order_id == "unknown" and order.get("placeCode") is not None:
            log.append(f"    Warning: Order returned success but no orderId. Status: {order.get('placeStatus')}")

        transferred = False  # order succeeded, no rollback of from_coin needed

        # ── Step 4: Get received amount (with polling) ───────────────
        received = 0.0
        for attempt in range(3):
            await asyncio.sleep(1 + attempt)  # 1s, then 2s, then 3s
            spot_after = await _client.get_spot_account()
            received = _get_spot_balance(spot_after, to_coin)
            if received > 0:
                break
        
        log.append(f"[4] Received {received} {to_coin} in spot")

        # ── Step 5: Transfer to_coin back to futures ──────────────────
        if wallet == "futures" and received > 0:
            # Use 4 decimals for transfer back to capture most value while staying safe for the API.
            recv_str = f"{received:.4f}".rstrip("0").rstrip(".")
            log.append(f"[5] Transferring {recv_str} {to_coin}: spot -> futures")
            await _client.funds_transfer("spot_futures", to_coin, recv_str)
            log.append(f"    OK")

        return {
            "success": True,
            "converted": f"{trade_amount} {from_coin} -> {received} {to_coin}",
            "order_id": order_id,
            "log": log,
        }

    except Exception as e:
        log.append(f"ERROR: {e}")
        # ── Rollback: transfer from_coin back to futures if stuck in spot ──
        if transferred and wallet == "futures":
            log.append(f"[ROLLBACK] Returning {final_amount} {from_coin} from spot -> futures")
            try:
                await _client.funds_transfer("spot_futures", from_coin, final_amount)
                log.append("    Rollback OK — funds returned to futures")
            except Exception as rb_err:
                log.append(f"    Rollback FAILED: {rb_err} — check spot wallet manually!")
        return {"error": str(e), "log": log}
