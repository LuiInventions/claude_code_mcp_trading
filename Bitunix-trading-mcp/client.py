import hashlib
import json
import os
import time
import uuid
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://fapi.bitunix.com"
BASE_PATH = "/api/v1/futures"
SPOT_BASE_URL = "https://openapi.bitunix.com"
SPOT_BASE_PATH = "/api/spot/v1"
TIMEOUT = 10.0


class BitunixClient:
    def __init__(self):
        self.api_key = os.environ.get("BITUNIX_API_KEY", "")
        self.secret_key = os.environ.get("BITUNIX_SECRET_KEY", "")
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)

    # ------------------------------------------------------------------ #
    # Auth helpers                                                         #
    # ------------------------------------------------------------------ #

    def _build_query_string(self, params: dict) -> str:
        """Concatenate key+value pairs without & or = (signing format)."""
        return "".join(f"{k}{v}" for k, v in params.items())

    def _generate_headers(self, query_str: str = "", body_str: str = "") -> dict:
        nonce = uuid.uuid4().hex
        timestamp = str(int(time.time() * 1000))

        digest_input = nonce + timestamp + self.api_key + query_str + body_str
        digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()

        sign_input = digest + self.secret_key
        sign = hashlib.sha256(sign_input.encode("utf-8")).hexdigest()

        return {
            "api-key": self.api_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": sign,
            "Content-Type": "application/json",
            "language": "en-US",
        }

    # ------------------------------------------------------------------ #
    # HTTP helpers                                                          #
    # ------------------------------------------------------------------ #

    def _handle_response(self, response: httpx.Response) -> Any:
        response.raise_for_status()
        data = response.json()
        code = data.get("code", -1)
        if code != 0:
            msg = data.get("msg", "Unknown error")
            raise RuntimeError(f"BitUnix API error {code}: {msg}")
        return data.get("data", data)

    async def _get_public(self, path: str, params: Optional[dict] = None) -> Any:
        resp = await self._http.get(path, params=params or {})
        return self._handle_response(resp)

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        query_str = self._build_query_string(params)
        headers = self._generate_headers(query_str=query_str)
        resp = await self._http.get(path, params=params, headers=headers)
        return self._handle_response(resp)

    async def _post(self, path: str, body: Optional[dict] = None) -> Any:
        body = {k: v for k, v in (body or {}).items() if v is not None and v != "" and v is not False or k in ("reduceOnly",)}
        body_str = json.dumps(body, separators=(",", ":"))
        headers = self._generate_headers(body_str=body_str)
        resp = await self._http.post(path, content=body_str, headers=headers)
        return self._handle_response(resp)

    async def _post_raw(self, path: str, body: dict) -> Any:
        """POST with full body as-is (no filtering), for batch/complex payloads."""
        body_str = json.dumps(body, separators=(",", ":"))
        headers = self._generate_headers(body_str=body_str)
        resp = await self._http.post(path, content=body_str, headers=headers)
        return self._handle_response(resp)

    # ------------------------------------------------------------------ #
    # PUBLIC — Market Data                                                 #
    # ------------------------------------------------------------------ #

    async def get_trading_pairs(self, symbols: Optional[str] = None) -> Any:
        params = {}
        if symbols:
            params["symbols"] = symbols
        return await self._get_public(f"{BASE_PATH}/market/trading_pairs", params)

    async def get_tickers(self, symbols: Optional[str] = None) -> Any:
        params = {}
        if symbols:
            params["symbols"] = symbols
        return await self._get_public(f"{BASE_PATH}/market/tickers", params)

    async def get_depth(self, symbol: str, limit: int = 20) -> Any:
        return await self._get_public(f"{BASE_PATH}/market/depth", {"symbol": symbol, "limit": limit})

    async def get_kline(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Any:
        params: dict = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._get_public(f"{BASE_PATH}/market/kline", params)

    async def get_funding_rate(self, symbol: str) -> Any:
        return await self._get_public(f"{BASE_PATH}/market/funding_rate", {"symbol": symbol})

    async def get_batch_funding_rate(self, symbols: Optional[str] = None) -> Any:
        params = {}
        if symbols:
            params["symbols"] = symbols
        return await self._get_public(f"{BASE_PATH}/market/batch_funding_rate", params)

    # ------------------------------------------------------------------ #
    # PRIVATE — Account                                                    #
    # ------------------------------------------------------------------ #

    async def get_account(self, margin_coin: str = "USDT") -> Any:
        return await self._get(f"{BASE_PATH}/account", {"marginCoin": margin_coin})

    async def get_leverage_margin_mode(self, symbol: str, margin_coin: str = "USDT") -> Any:
        return await self._get(
            f"{BASE_PATH}/account/get_leverage_margin_mode",
            {"symbol": symbol, "marginCoin": margin_coin},
        )

    async def change_leverage(self, symbol: str, leverage: int, margin_coin: str = "USDT") -> Any:
        return await self._post(
            f"{BASE_PATH}/account/change_leverage",
            {"symbol": symbol, "leverage": leverage, "marginCoin": margin_coin},
        )

    async def change_margin_mode(self, symbol: str, margin_mode: str, margin_coin: str = "USDT") -> Any:
        return await self._post(
            f"{BASE_PATH}/account/change_margin_mode",
            {"symbol": symbol, "marginCoin": margin_coin, "marginMode": margin_mode},
        )

    async def change_position_mode(self, position_mode: str, margin_coin: str = "USDT") -> Any:
        return await self._post(
            f"{BASE_PATH}/account/change_position_mode",
            {"positionMode": position_mode, "marginCoin": margin_coin},
        )

    async def adjust_position_margin(
        self,
        symbol: str,
        position_id: str,
        amount: str,
        type_: int,
        margin_coin: str = "USDT",
    ) -> Any:
        return await self._post(
            f"{BASE_PATH}/account/adjust_position_margin",
            {
                "symbol": symbol,
                "positionId": position_id,
                "amount": amount,
                "type": type_,
                "marginCoin": margin_coin,
            },
        )

    # ------------------------------------------------------------------ #
    # PRIVATE — Position                                                   #
    # ------------------------------------------------------------------ #

    async def get_pending_positions(self, symbol: Optional[str] = None) -> Any:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._get(f"{BASE_PATH}/position/get_pending_positions", params)

    async def get_history_positions(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> Any:
        params: dict = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._get(f"{BASE_PATH}/position/get_history_positions", params)

    async def get_position_tiers(self, symbol: str) -> Any:
        return await self._get(f"{BASE_PATH}/position/get_position_tiers", {"symbol": symbol})

    # ------------------------------------------------------------------ #
    # PRIVATE — Trade                                                      #
    # ------------------------------------------------------------------ #

    async def place_order(
        self,
        symbol: str,
        side: str,
        trade_side: str,
        order_type: str,
        qty: str,
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
    ) -> Any:
        body: dict = {
            "symbol": symbol,
            "side": side,
            "tradeSide": trade_side,
            "orderType": order_type,
            "qty": qty,
        }
        if price:
            body["price"] = price
        if position_id:
            body["positionId"] = position_id
        if reduce_only:
            body["reduceOnly"] = reduce_only
        if effect and effect != "GTC":
            body["effect"] = effect
        if client_id:
            body["clientId"] = client_id
        if tp_price:
            body["tpPrice"] = tp_price
        if tp_stop_type:
            body["tpStopType"] = tp_stop_type
        if tp_order_type:
            body["tpOrderType"] = tp_order_type
        if tp_order_price:
            body["tpOrderPrice"] = tp_order_price
        if sl_price:
            body["slPrice"] = sl_price
        if sl_stop_type:
            body["slStopType"] = sl_stop_type
        if sl_order_type:
            body["slOrderType"] = sl_order_type
        if sl_order_price:
            body["slOrderPrice"] = sl_order_price
        return await self._post_raw(f"{BASE_PATH}/trade/place_order", body)

    async def batch_order(self, symbol: str, order_list: list) -> Any:
        # symbol is required at TOP LEVEL — individual orders do NOT include symbol
        # Official format: {"symbol": "BTCUSDT", "orderList": [{side, tradeSide, orderType, qty, ...}]}
        return await self._post_raw(f"{BASE_PATH}/trade/batch_order", {"symbol": symbol, "orderList": order_list})

    async def cancel_orders(self, symbol: str, order_ids: list) -> Any:
        # API requires {"orderList": [{"symbol": ..., "orderId": ...}]}
        order_list = [{"symbol": symbol, "orderId": oid} for oid in order_ids]
        return await self._post_raw(
            f"{BASE_PATH}/trade/cancel_orders",
            {"orderList": order_list},
        )

    async def cancel_all_orders(self, symbol: Optional[str] = None) -> Any:
        body = {}
        if symbol:
            body["symbol"] = symbol
        return await self._post_raw(f"{BASE_PATH}/trade/cancel_all_orders", body)

    async def modify_order(
        self,
        order_id: str,
        symbol: str,
        price: str = "",
        qty: str = "",
        tp_price: str = "",
        tp_stop_type: str = "",
        tp_order_type: str = "",
        tp_order_price: str = "",
    ) -> Any:
        body: dict = {"orderId": order_id, "symbol": symbol}
        if price:
            body["price"] = price
        if qty:
            body["qty"] = qty
        if tp_price:
            body["tpPrice"] = tp_price
        if tp_stop_type:
            body["tpStopType"] = tp_stop_type
        if tp_order_type:
            body["tpOrderType"] = tp_order_type
        if tp_order_price:
            body["tpOrderPrice"] = tp_order_price
        return await self._post_raw(f"{BASE_PATH}/trade/modify_order", body)

    async def flash_close_position(self, symbol: str, position_id: str) -> Any:
        return await self._post_raw(
            f"{BASE_PATH}/trade/flash_close_position",
            {"symbol": symbol, "positionId": position_id},
        )

    async def close_all_positions(self, symbol: Optional[str] = None) -> Any:
        body = {}
        if symbol:
            body["symbol"] = symbol
        return await self._post_raw(f"{BASE_PATH}/trade/close_all_position", body)

    async def get_pending_orders(self, symbol: Optional[str] = None) -> Any:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._get(f"{BASE_PATH}/trade/get_pending_orders", params)

    async def get_history_orders(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> Any:
        params: dict = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._get(f"{BASE_PATH}/trade/get_history_orders", params)

    async def get_history_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> Any:
        params: dict = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._get(f"{BASE_PATH}/trade/get_history_trades", params)

    async def get_order_detail(self, order_id: str = "", client_id: str = "") -> Any:
        params = {}
        if order_id:
            params["orderId"] = order_id
        if client_id:
            params["clientId"] = client_id
        return await self._get(f"{BASE_PATH}/trade/get_order_detail", params)

    # ------------------------------------------------------------------ #
    # PRIVATE — TP/SL                                                      #
    # ------------------------------------------------------------------ #

    def _build_tpsl_body(
        self,
        symbol: str,
        position_id: str = "",
        tp_price: str = "",
        tp_stop_type: str = "",
        tp_order_type: str = "",
        tp_order_price: str = "",
        tp_qty: str = "",
        sl_price: str = "",
        sl_stop_type: str = "",
        sl_order_type: str = "",
        sl_order_price: str = "",
        sl_qty: str = "",
    ) -> dict:
        body: dict = {"symbol": symbol}
        if position_id:
            body["positionId"] = position_id
        if tp_price:
            body["tpPrice"] = tp_price
        if tp_stop_type:
            body["tpStopType"] = tp_stop_type
        if tp_order_type:
            body["tpOrderType"] = tp_order_type
        # Only send tpOrderPrice if it's a LIMIT order and price is set (filter "0")
        if tp_order_type == "LIMIT" and tp_order_price and tp_order_price != "0":
            body["tpOrderPrice"] = tp_order_price
        if tp_qty and tp_qty != "0":
            body["tpQty"] = tp_qty
        if sl_price:
            body["slPrice"] = sl_price
        if sl_stop_type:
            body["slStopType"] = sl_stop_type
        if sl_order_type:
            body["slOrderType"] = sl_order_type
        # Only send slOrderPrice if it's a LIMIT order and price is set (filter "0")
        if sl_order_type == "LIMIT" and sl_order_price and sl_order_price != "0":
            body["slOrderPrice"] = sl_order_price
        if sl_qty and sl_qty != "0":
            body["slQty"] = sl_qty
        return body

    async def place_tpsl_order(self, **kwargs) -> Any:
        body = self._build_tpsl_body(**kwargs)
        return await self._post(f"{BASE_PATH}/tpsl/place_order", body)

    async def place_position_tpsl_order(self, **kwargs) -> Any:
        # Use /tpsl/position/place_order and _post (to filter empty params like tpQty/slQty which cause error 2)
        body = self._build_tpsl_body(**kwargs)
        return await self._post(f"{BASE_PATH}/tpsl/position/place_order", body)

    async def modify_tpsl_order(
        self,
        tpsl_id: str,
        symbol: str,
        **kwargs
    ) -> Any:
        # The /tpsl/modify_order endpoint is broken on BitUnix (Error 30006).
        # We implement a "Cancel + Re-place" workaround to fix this functionality.
        
        # 1. Fetch current pending TP/SL orders for this symbol
        pending = await self.get_pending_tpsl_orders(symbol)
        
        # 2. Find the requested order
        # Response items use 'id' as order identifier
        order = next((o for o in pending if str(o.get('id')) == str(tpsl_id)), None)
        
        if not order:
            raise RuntimeError(f"TP/SL Order {tpsl_id} not found for {symbol}. It may have been triggered or already cancelled.")

        # 3. Merge current state with requested changes
        # Map response fields to tool parameters
        params = {
            "symbol": symbol,
            "position_id": order.get("positionId", ""),
            "tp_price": kwargs.get("tp_price") or str(order.get("tpPrice", "")),
            "tp_stop_type": kwargs.get("tp_stop_type") or order.get("tpStopType", ""),
            "tp_order_type": kwargs.get("tp_order_type") or order.get("tpOrderType", ""),
            "tp_order_price": kwargs.get("tp_order_price") or str(order.get("tpOrderPrice", "")),
            "tp_qty": kwargs.get("tp_qty") or str(order.get("tpQty", "")),
            "sl_price": kwargs.get("sl_price") or str(order.get("slPrice", "")),
            "sl_stop_type": kwargs.get("sl_stop_type") or order.get("slStopType", ""),
            "sl_order_type": kwargs.get("sl_order_type") or order.get("slOrderType", ""),
            "sl_order_price": kwargs.get("sl_order_price") or str(order.get("slOrderPrice", "")),
            "sl_qty": kwargs.get("sl_qty") or str(order.get("slQty", "")),
        }
        
        # 4. Cancel the old order
        await self.cancel_tpsl_order(symbol, [tpsl_id])
        
        # 5. Place the new modified order
        return await self.place_tpsl_order(**params)

    async def modify_position_tpsl_order(
        self,
        position_id: str,
        symbol: str,
        tp_price: str = "",
        tp_stop_type: str = "",
        tp_order_type: str = "",
        tp_order_price: str = "",
        sl_price: str = "",
        sl_stop_type: str = "",
        sl_order_type: str = "",
        sl_order_price: str = "",
    ) -> Any:
        body: dict = {"positionId": position_id, "symbol": symbol}
        if tp_price:
            body["tpPrice"] = tp_price
        if tp_stop_type:
            body["tpStopType"] = tp_stop_type
        if tp_order_type:
            body["tpOrderType"] = tp_order_type
        if tp_order_price:
            body["tpOrderPrice"] = tp_order_price
        if sl_price:
            body["slPrice"] = sl_price
        if sl_stop_type:
            body["slStopType"] = sl_stop_type
        if sl_order_type:
            body["slOrderType"] = sl_order_type
        if sl_order_price:
            body["slOrderPrice"] = sl_order_price
        # Correct documented path: /tpsl/position/modify_order
        return await self._post(f"{BASE_PATH}/tpsl/position/modify_order", body)

    async def cancel_tpsl_order(self, symbol: str, tpsl_ids: list) -> Any:
        # API only accepts one cancellation at a time; field is "orderId" not "tpslIds"
        results = []
        for tpsl_id in tpsl_ids:
            result = await self._post_raw(
                f"{BASE_PATH}/tpsl/cancel_order",
                {"symbol": symbol, "orderId": tpsl_id},
            )
            results.append(result)
        return results

    async def get_pending_tpsl_orders(self, symbol: Optional[str] = None) -> Any:
        # Correct endpoint is /tpsl/get_pending_orders (not /tpsl/get_pending_tp_sl_order)
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._get(f"{BASE_PATH}/tpsl/get_pending_orders", params)

    async def get_history_tpsl_orders(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> Any:
        params: dict = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        # Correct endpoint is /tpsl/get_history_orders (not /tpsl/get_history_tp_sl_order)
        return await self._get(f"{BASE_PATH}/tpsl/get_history_orders", params)


# ======================================================================== #
# Spot Client — https://openapi.bitunix.com                                 #
# Same signing algorithm as BitunixClient, different base URL               #
# ======================================================================== #

class SpotClient:
    """Client for the Bitunix Spot REST API (openapi.bitunix.com)."""

    def __init__(self):
        self.api_key    = os.environ.get("BITUNIX_API_KEY", "")
        self.secret_key = os.environ.get("BITUNIX_SECRET_KEY", "")
        self._http = httpx.AsyncClient(base_url=SPOT_BASE_URL, timeout=TIMEOUT)

    # ------------------------------------------------------------------ #
    # Auth helpers (identical algorithm to futures)                        #
    # ------------------------------------------------------------------ #

    def _generate_headers(self, query_str: str = "", body_str: str = "") -> dict:
        nonce     = uuid.uuid4().hex
        timestamp = str(int(time.time() * 1000))
        digest    = hashlib.sha256((nonce + timestamp + self.api_key + query_str + body_str).encode()).hexdigest()
        sign      = hashlib.sha256((digest + self.secret_key).encode()).hexdigest()
        return {
            "api-key": self.api_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": sign,
            "Content-Type": "application/json",
            "language": "en-US",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        response.raise_for_status()
        try:
            data = response.json()
        except Exception:
            raise RuntimeError(f"BitUnix Spot API returned non-JSON response: {response.text[:200]}")

        # Spot API returns code as string "0", not integer 0 — compare as string
        code = str(data.get("code", "-1"))
        if code != "0":
            msg = data.get("msg", "Unknown error")
            raise RuntimeError(f"BitUnix Spot API error {code}: {msg}")
        
        # Return the 'data' field, or the whole object if 'data' is missing
        result = data.get("data")
        if result is None:
            # For some endpoints, 'data' might be null but the request succeeded
            return data
            
        # BUG FIX: Spot orders can return code 0 but have an internal failure in placeCode
        if isinstance(result, dict):
            place_code = result.get("placeCode")
            if place_code is not None and str(place_code) != "0":
                place_msg = result.get("placeMsg") or "Engine rejection"
                raise RuntimeError(f"BitUnix Spot Engine error {place_code}: {place_msg}")
                
        return result

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        params    = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        qs        = "".join(f"{k}{v}" for k, v in params.items())
        headers   = self._generate_headers(query_str=qs)
        resp      = await self._http.get(path, params=params, headers=headers)
        return self._handle_response(resp)

    async def _post(self, path: str, body: dict) -> Any:
        body_str  = json.dumps(body, separators=(",", ":"))
        headers   = self._generate_headers(body_str=body_str)
        resp      = await self._http.post(path, content=body_str, headers=headers)
        return self._handle_response(resp)

    # ------------------------------------------------------------------ #
    # Spot Account                                                         #
    # ------------------------------------------------------------------ #

    async def get_spot_account(self) -> Any:
        """Returns list of {coin, balance, balanceLocked} for all spot coins."""
        return await self._get(f"{SPOT_BASE_PATH}/user/account")

    # ------------------------------------------------------------------ #
    # Spot Trading                                                         #
    # ------------------------------------------------------------------ #

    async def spot_place_order(
        self,
        symbol: str,
        side: int,
        order_type: int,
        volume: str,
        price: str = "0",
    ) -> Any:
        """
        Place a spot order.
        side:       1 = Sell  |  2 = Buy
        order_type: 1 = Limit |  2 = Market
        volume:     quantity in base coin as string
        price:      limit price, or "0" for market orders
        """
        return await self._post(f"{SPOT_BASE_PATH}/order/place_order", {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "volume": volume,
            "price": price,
        })

    # ------------------------------------------------------------------ #
    # Funds Transfer (Spot <-> Futures)                                    #
    # ------------------------------------------------------------------ #

    async def funds_transfer(self, transfer_type: str, coin: str, amount: str) -> Any:
        """
        Transfer funds between spot and futures wallets.
        transfer_type: "spot_futures" (spot -> futures) | "futures_spot" (futures -> spot)
        coin:   e.g. "USDT", "USDC", "BTC"
        amount: quantity as string, e.g. "100"
        """
        return await self._post(f"{SPOT_BASE_PATH}/funds_transfer", {
            "type": transfer_type,
            "coin": coin,
            "amount": amount,
        })
