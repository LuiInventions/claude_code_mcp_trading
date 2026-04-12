from typing import Optional
from fastmcp import FastMCP
from client import BitunixClient

_client = BitunixClient()


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_pending_positions(symbol: Optional[str] = None) -> dict:
        """
        Get all currently open (pending) futures positions.
        symbol: filter by symbol e.g. "BTCUSDT". Omit to get all open positions.
        Returns position size, entry price, unrealized PnL, margin, leverage, etc.
        """
        try:
            return {"data": await _client.get_pending_positions(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_history_positions(
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        """
        Get closed/historical positions.
        symbol: filter by symbol e.g. "BTCUSDT". Omit for all symbols.
        start_time: start timestamp in milliseconds (optional)
        end_time: end timestamp in milliseconds (optional)
        limit: max records to return (default 100)
        """
        try:
            return {"data": await _client.get_history_positions(symbol, start_time, end_time, limit)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_position_tiers(symbol: str) -> dict:
        """
        Get position tier/bracket information for a symbol.
        symbol: e.g. "BTCUSDT"
        Returns max position size, maintenance margin rate, and max leverage per tier.
        """
        try:
            return {"data": await _client.get_position_tiers(symbol)}
        except Exception as e:
            return {"error": str(e)}
