from typing import Optional
from fastmcp import FastMCP
from client import BitunixClient

_client = BitunixClient()


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def place_tpsl_order(
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
        """
        Place a standalone take-profit and/or stop-loss order for a position.
        Can set TP only, SL only, or both at once.

        symbol: e.g. "BTCUSDT"
        position_id: the position to attach this TP/SL to (optional)
        tp_price: take profit trigger price, e.g. "65000"
        tp_stop_type: "MARK" or "LAST_PRICE"
        tp_order_type: "MARKET" or "LIMIT"
        tp_order_price: execution price if tp_order_type=LIMIT
        tp_qty: quantity for TP order (partial TP), e.g. "0.5"
        sl_price: stop loss trigger price, e.g. "55000"
        sl_stop_type: "MARK" or "LAST_PRICE"
        sl_order_type: "MARKET" or "LIMIT"
        sl_order_price: execution price if sl_order_type=LIMIT
        sl_qty: quantity for SL order (partial SL), e.g. "0.5"
        """
        try:
            return {"data": await _client.place_tpsl_order(
                symbol=symbol, position_id=position_id,
                tp_price=tp_price, tp_stop_type=tp_stop_type,
                tp_order_type=tp_order_type, tp_order_price=tp_order_price, tp_qty=tp_qty,
                sl_price=sl_price, sl_stop_type=sl_stop_type,
                sl_order_type=sl_order_type, sl_order_price=sl_order_price, sl_qty=sl_qty,
            )}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def place_position_tpsl_order(
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
        """
        Place TP/SL for an entire position (position-level TP/SL).
        Closes the full position when price hits TP or SL.

        symbol: e.g. "BTCUSDT"
        position_id: the position ID (get from get_pending_positions)
        tp_price: take profit trigger price
        tp_stop_type: "MARK" or "LAST_PRICE"
        tp_order_type: "MARKET" or "LIMIT"
        tp_order_price: limit execution price if tp_order_type=LIMIT
        sl_price: stop loss trigger price
        sl_stop_type: "MARK" or "LAST_PRICE"
        sl_order_type: "MARKET" or "LIMIT"
        sl_order_price: limit execution price if sl_order_type=LIMIT
        """
        try:
            return {"data": await _client.place_position_tpsl_order(
                symbol=symbol, position_id=position_id,
                tp_price=tp_price, tp_stop_type=tp_stop_type,
                tp_order_type=tp_order_type, tp_order_price=tp_order_price, tp_qty=tp_qty,
                sl_price=sl_price, sl_stop_type=sl_stop_type,
                sl_order_type=sl_order_type, sl_order_price=sl_order_price, sl_qty=sl_qty,
            )}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def modify_tpsl_order(
        tpsl_id: str,
        symbol: str,
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
        Modify an existing standalone TP/SL order.
        NOTE: This performs a Cancel + Re-place operation internally as the 
        BitUnix modification endpoint is currently broken.

        tpsl_id: the TP/SL order ID to modify
        symbol: e.g. "BTCUSDT"
        tp_price: new take profit price (optional)
        sl_price: new stop loss price (optional)
        Other fields are optional and only sent if provided.
        """
        try:
            return {"data": await _client.modify_tpsl_order(
                tpsl_id=tpsl_id, symbol=symbol,
                tp_price=tp_price, tp_stop_type=tp_stop_type,
                tp_order_type=tp_order_type, tp_order_price=tp_order_price,
                sl_price=sl_price, sl_stop_type=sl_stop_type,
                sl_order_type=sl_order_type, sl_order_price=sl_order_price,
            )}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def modify_position_tpsl_order(
        position_id: str,
        symbol: str,
        tp_price: str = "",
        tp_stop_type: str = "",
        sl_price: str = "",
        sl_stop_type: str = "",
    ) -> dict:
        """
        Modify the TP/SL trigger prices for an open position (position-level modify).
        Uses endpoint: POST /tpsl/position/modify_order

        position_id: the position ID (get from get_pending_positions)
        symbol: e.g. "BTCUSDT"
        tp_price: new take profit trigger price (optional, omit to keep current)
        tp_stop_type: "MARK_PRICE" or "LAST_PRICE" (required if tp_price set)
        sl_price: new stop loss trigger price (optional, omit to keep current)
        sl_stop_type: "MARK_PRICE" or "LAST_PRICE" (required if sl_price set)

        At least one of tp_price or sl_price must be provided.

        NOTE: This only changes trigger prices. To change order type or qty,
        use cancel_tpsl_order + place_tpsl_order instead.
        """
        try:
            return {"data": await _client.modify_position_tpsl_order(
                position_id=position_id, symbol=symbol,
                tp_price=tp_price, tp_stop_type=tp_stop_type,
                sl_price=sl_price, sl_stop_type=sl_stop_type,
            )}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_tpsl_order(symbol: str, tpsl_ids: list) -> dict:
        """
        Cancel one or more TP/SL orders.
        symbol: e.g. "BTCUSDT"
        tpsl_ids: list of TP/SL order ID strings to cancel, e.g. ["id1", "id2"]
        """
        try:
            return {"data": await _client.cancel_tpsl_order(symbol, tpsl_ids)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_pending_tpsl_orders(symbol: Optional[str] = None) -> dict:
        """
        Get all active (pending) TP/SL orders.
        symbol: filter by symbol e.g. "BTCUSDT". Omit for all symbols.
        """
        try:
            return {"data": await _client.get_pending_tpsl_orders(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_history_tpsl_orders(
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        """
        Get historical (triggered or cancelled) TP/SL orders.
        symbol: filter by symbol e.g. "BTCUSDT". Omit for all.
        start_time: start timestamp in milliseconds (optional)
        end_time: end timestamp in milliseconds (optional)
        limit: max records (default 100)
        """
        try:
            return {"data": await _client.get_history_tpsl_orders(symbol, start_time, end_time, limit)}
        except Exception as e:
            return {"error": str(e)}
