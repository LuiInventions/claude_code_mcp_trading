from typing import Optional
from fastmcp import FastMCP
from client import BitunixClient

_client = BitunixClient()


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_trading_pairs(symbols: Optional[str] = None) -> dict:
        """
        Get available trading pairs on BitUnix Futures.
        symbols: optional comma-separated list, e.g. "BTCUSDT,ETHUSDT". Omit for all pairs.
        """
        try:
            return {"data": await _client.get_trading_pairs(symbols)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_tickers(symbols: Optional[str] = None) -> dict:
        """
        Get real-time price tickers for futures symbols.
        symbols: optional comma-separated list, e.g. "BTCUSDT,ETHUSDT". Omit for all.
        Returns last price, bid/ask, 24h volume, funding rate, etc.
        """
        try:
            return {"data": await _client.get_tickers(symbols)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_order_book(symbol: str, limit: int = 20) -> dict:
        """
        Get the order book (depth) for a futures symbol.
        symbol: e.g. "BTCUSDT"
        limit: number of price levels to return (default 20)
        """
        try:
            return {"data": await _client.get_depth(symbol, limit)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_kline(
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict:
        """
        Get candlestick (OHLCV) data for a futures symbol.
        symbol: e.g. "BTCUSDT"
        interval: one of 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        limit: number of candles (default 100)
        start_time: start timestamp in milliseconds (optional)
        end_time: end timestamp in milliseconds (optional)
        """
        try:
            return {"data": await _client.get_kline(symbol, interval, limit, start_time, end_time)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_funding_rate(symbol: str) -> dict:
        """
        Get current and next funding rate for a futures symbol.
        symbol: e.g. "BTCUSDT"
        """
        try:
            return {"data": await _client.get_funding_rate(symbol)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_batch_funding_rate(symbols: Optional[str] = None) -> dict:
        """
        Get funding rates for multiple futures symbols at once.
        symbols: optional comma-separated list, e.g. "BTCUSDT,ETHUSDT". Omit for all.
        """
        try:
            return {"data": await _client.get_batch_funding_rate(symbols)}
        except Exception as e:
            return {"error": str(e)}
