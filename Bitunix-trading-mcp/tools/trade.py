from typing import Optional
from fastmcp import FastMCP
from client import BitunixClient

_client = BitunixClient()


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def place_order(
        symbol: str,
        side: str,
        trade_side: str,
        order_type: str,
        qty: str,
        leverage: Optional[int] = None,
        margin_mode: Optional[str] = None,
        price: str = "",
        position_id: str = "",
        reduce_only: bool = False,
        effect: str = "GTC",
        client_id: str = "",
        tp_price: str = "",
        tp_stop_type: str = "",
        tp_order_type: str = "",
        tp_order_price: str = "",
        sl_price: str = "",
        sl_stop_type: str = "",
        sl_order_type: str = "",
        sl_order_price: str = "",
    ) -> dict:
        """
        Place a futures order on BitUnix. Supports leverage setting before order.

        symbol: trading pair, e.g. "BTCUSDT"
        side: "BUY" or "SELL"
          - BUY = open Long or close Short
          - SELL = open Short or close Long
        trade_side: "OPEN" or "CLOSE"
        order_type: "MARKET" or "LIMIT"
        qty: quantity in base asset as string, e.g. "0.01" for 0.01 BTC
        leverage: if provided, sets leverage BEFORE placing the order (1-125)
        margin_mode: if provided alongside leverage, also sets margin mode ("ISOLATED" or "CROSSED")
        price: required for LIMIT orders, e.g. "60000"
        position_id: optional, close a specific position by ID
        reduce_only: if True, only reduces existing position
        effect: order time-in-force — "GTC" (default), "IOC", or "FOK"
        client_id: optional custom order ID for tracking
        tp_price: take profit trigger price, e.g. "65000"
        tp_stop_type: "MARK" or "LAST_PRICE"
        tp_order_type: "MARKET" or "LIMIT"
        tp_order_price: limit price for TP if tp_order_type=LIMIT
        sl_price: stop loss trigger price, e.g. "55000"
        sl_stop_type: "MARK" or "LAST_PRICE"
        sl_order_type: "MARKET" or "LIMIT"
        sl_order_price: limit price for SL if sl_order_type=LIMIT

        Examples:
          Open 10x Long (ISOLATED): side=BUY, trade_side=OPEN, leverage=10, margin_mode="ISOLATED"
          Open 20x Short (ISOLATED): side=SELL, trade_side=OPEN, leverage=20, margin_mode="ISOLATED"
          Close Long: side=SELL, trade_side=CLOSE
          Close Short: side=BUY, trade_side=CLOSE
        """
        try:
            # leverage MUST be set first; change_margin_mode is skipped (always error 10002)
            if leverage is not None:
                await _client.change_leverage(symbol, leverage)
            # Mandate ISOLATED mode for new positions per policy
            target_mode = margin_mode or ("ISOLATED" if trade_side == "OPEN" else None)
            if target_mode:
                try:
                    await _client.change_margin_mode(symbol, target_mode)
                except Exception as e:
                    if target_mode == "ISOLATED":
                        # If we specifically wanted ISOLATED and it failed, we should know why, 
                        # but we still try to place the order if it's a known restricted account.
                        pass 
                    else:
                        raise e
            result = await _client.place_order(
                symbol=symbol,
                side=side,
                trade_side=trade_side,
                order_type=order_type,
                qty=qty,
                price=price,
                position_id=position_id,
                reduce_only=reduce_only,
                effect=effect,
                client_id=client_id,
                tp_price=tp_price,
                tp_stop_type=tp_stop_type,
                tp_order_type=tp_order_type,
                tp_order_price=tp_order_price,
                sl_price=sl_price,
                sl_stop_type=sl_stop_type,
                sl_order_type=sl_order_type,
                sl_order_price=sl_order_price,
            )
            return {"data": result}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def batch_order(symbol: str, order_list: list) -> dict:
        """
        Place up to 5 futures orders for the SAME symbol simultaneously.

        IMPORTANT: symbol is required at TOP LEVEL — do NOT include symbol inside each order.
        All orders in order_list must be for the same symbol.

        symbol: trading pair, e.g. "BTCUSDT"
        order_list: list of order objects. Each order has:
          - side: "BUY" or "SELL" (required)
          - tradeSide: "OPEN" or "CLOSE" (required in hedge mode)
          - orderType: "MARKET" or "LIMIT" (required)
          - qty: base asset quantity as string, e.g. "0.01" (required)
          - price: limit price as string — required if orderType=LIMIT
          - positionId: position ID — required if tradeSide=CLOSE
          - effect: "GTC" (default), "IOC", "FOK", "POST_ONLY" — for LIMIT orders
          - clientId: optional custom order ID
          - tpPrice, tpStopType, tpOrderType: optional TP fields
          - slPrice, slStopType, slOrderType: optional SL fields

        Example — two market orders on BTCUSDT:
          symbol="BTCUSDT"
          order_list=[
            {"side":"BUY","tradeSide":"OPEN","orderType":"MARKET","qty":"0.01"},
            {"side":"SELL","tradeSide":"OPEN","orderType":"LIMIT","qty":"0.01","price":"80000","effect":"GTC"}
          ]
        """
        try:
            return {"data": await _client.batch_order(symbol, order_list)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_orders(symbol: str, order_ids: list) -> dict:
        """
        Cancel one or more open orders by order ID.
        symbol: e.g. "BTCUSDT"
        order_ids: list of order ID strings to cancel, e.g. ["orderId1", "orderId2"]
        """
        try:
            return {"data": await _client.cancel_orders(symbol, order_ids)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_all_orders(symbol: Optional[str] = None) -> dict:
        """
        Cancel all open orders. Optionally filter by symbol.
        symbol: e.g. "BTCUSDT". Omit to cancel orders for ALL symbols.
        """
        try:
            return {"data": await _client.cancel_all_orders(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def modify_order(
        order_id: str,
        symbol: str,
        price: str = "",
        qty: str = "",
        tp_price: str = "",
        tp_stop_type: str = "",
        tp_order_type: str = "",
        tp_order_price: str = "",
    ) -> dict:
        """
        Modify an existing open order's price, quantity, or take-profit settings.
        order_id: the order ID to modify
        symbol: e.g. "BTCUSDT"
        price: new limit price (optional)
        qty: new quantity (optional)
        tp_price: new take profit trigger price (optional)
        tp_stop_type: "MARK" or "LAST_PRICE"
        tp_order_type: "MARKET" or "LIMIT"
        tp_order_price: limit price for TP execution
        """
        try:
            return {"data": await _client.modify_order(order_id, symbol, price, qty, tp_price, tp_stop_type, tp_order_type, tp_order_price)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def flash_close_position(symbol: str, position_id: str) -> dict:
        """
        Immediately close a specific position at market price.
        symbol: e.g. "BTCUSDT"
        position_id: the position ID to close instantly
        Use this for fast emergency exits.
        """
        try:
            return {"data": await _client.flash_close_position(symbol, position_id)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def close_all_positions(symbol: Optional[str] = None) -> dict:
        """
        Close all open positions at market price.
        symbol: e.g. "BTCUSDT" to close only that symbol. Omit to close ALL positions.
        Warning: this closes every open position immediately at market price.
        """
        try:
            return {"data": await _client.close_all_positions(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_pending_orders(symbol: Optional[str] = None) -> dict:
        """
        Get all currently open (pending) orders.
        symbol: filter by symbol e.g. "BTCUSDT". Omit to get orders for all symbols.
        """
        try:
            return {"data": await _client.get_pending_orders(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_history_orders(
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        """
        Get historical (filled, cancelled, expired) orders.
        symbol: filter by symbol e.g. "BTCUSDT". Omit for all.
        start_time: start timestamp in milliseconds (optional)
        end_time: end timestamp in milliseconds (optional)
        limit: max records (default 100)
        """
        try:
            return {"data": await _client.get_history_orders(symbol, start_time, end_time, limit)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_history_trades(
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        """
        Get historical trade executions (fills).
        symbol: filter by symbol e.g. "BTCUSDT". Omit for all.
        start_time: start timestamp in milliseconds (optional)
        end_time: end timestamp in milliseconds (optional)
        limit: max records (default 100)
        """
        try:
            return {"data": await _client.get_history_trades(symbol, start_time, end_time, limit)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_order_detail(order_id: str = "", client_id: str = "") -> dict:
        """
        Get details for a specific order by order ID or custom client ID.
        order_id: the BitUnix order ID (provide this OR client_id)
        client_id: your custom order ID if set when placing the order
        """
        try:
            return {"data": await _client.get_order_detail(order_id, client_id)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def set_leverage_and_margin_mode(
        symbol: str,
        leverage: int,
        margin_mode: str = "ISOLATED",
        margin_coin: str = "USDT",
    ) -> dict:
        """
        Convenience tool: set both leverage and margin mode for a symbol in one call.
        Use this before placing a series of leveraged trades to pre-configure the symbol.
        symbol: e.g. "BTCUSDT"
        leverage: 1-125 (max depends on symbol)
        margin_mode: "ISOLATED" (required per policy) or "CROSSED"
        margin_coin: settlement currency, default "USDT"
        """
        try:
            mode_result = await _client.change_margin_mode(symbol, margin_mode, margin_coin)
            lev_result = await _client.change_leverage(symbol, leverage, margin_coin)
            return {
                "data": {
                    "margin_mode": mode_result,
                    "leverage": lev_result,
                    "symbol": symbol,
                    "configured_leverage": leverage,
                    "configured_margin_mode": margin_mode,
                }
            }
        except Exception as e:
            return {"error": str(e)}
