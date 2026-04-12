from typing import Optional
from fastmcp import FastMCP
from client import BitunixClient

_client = BitunixClient()


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_account(margin_coin: str = "ALL") -> dict:
        """
        Get futures account balance and margin information.
        margin_coin: settlement currency to query. Default "ALL" — queries USDT, USDC, and BTC.
          Use "USDT", "USDC", or "BTC" to query a single currency.
        Returns available balance, margin used, unrealized PnL per currency.

        IMPORTANT: Always use the default "ALL" unless the user explicitly specifies one currency.
        This ensures balances in all currencies are always shown.
        """
        try:
            if margin_coin == "ALL":
                results = {}
                for coin in ["USDT", "USDC", "BTC"]:
                    try:
                        data = await _client.get_account(coin)
                        # Only include if account has any balance
                        balance = 0
                        if isinstance(data, dict):
                            balance = float(data.get("available", 0) or data.get("availableBalance", 0) or 0)
                        if balance != 0 or coin == "USDT":  # always show USDT even if 0
                            results[coin] = data
                    except Exception:
                        pass
                return {"data": results}
            return {"data": await _client.get_account(margin_coin)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_leverage_margin_mode(symbol: str, margin_coin: str = "USDT") -> dict:
        """
        Get current leverage and margin mode settings for a symbol.
        symbol: e.g. "BTCUSDT"
        margin_coin: settlement currency, default "USDT"
        Returns leverage value and margin mode (ISOLATED or CROSSED).
        """
        try:
            return {"data": await _client.get_leverage_margin_mode(symbol, margin_coin)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def change_leverage(symbol: str, leverage: int, margin_coin: str = "USDT") -> dict:
        """
        Change the leverage for a futures symbol.
        symbol: e.g. "BTCUSDT"
        leverage: integer between 1 and 125 (max depends on symbol)
        margin_coin: settlement currency, default "USDT"
        """
        try:
            return {"data": await _client.change_leverage(symbol, leverage, margin_coin)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def change_margin_mode(symbol: str, margin_mode: str = "ISOLATED", margin_coin: str = "USDT") -> dict:
        """
        Switch between ISOLATED and CROSSED margin mode for a symbol.
        Mandatory per policy: Use ISOLATED mode.
        symbol: e.g. "BTCUSDT"
        margin_mode: "ISOLATED" (default) or "CROSSED"
        margin_coin: settlement currency, default "USDT"
        Note: cannot change margin mode when a position is open.
        """
        try:
            return {"data": await _client.change_margin_mode(symbol, margin_mode, margin_coin)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def change_position_mode(position_mode: str, margin_coin: str = "USDT") -> dict:
        """
        Switch between ONE_WAY and HEDGE position mode.
        position_mode: "ONE_WAY" (default, long+short net out) or "HEDGE" (separate long/short)
        margin_coin: settlement currency, default "USDT"
        Note: cannot switch modes while positions or orders are open.
        """
        try:
            return {"data": await _client.change_position_mode(position_mode, margin_coin)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def adjust_position_margin(
        symbol: str,
        position_id: str,
        amount: str,
        type: int,
        margin_coin: str = "USDT",
    ) -> dict:
        """
        Add or remove margin from an isolated position.
        symbol: e.g. "BTCUSDT"
        position_id: the position ID to adjust
        amount: margin amount as string, e.g. "100"
        type: 1 = add margin, 2 = remove margin
        margin_coin: settlement currency, default "USDT"
        """
        try:
            return {"data": await _client.adjust_position_margin(symbol, position_id, amount, type, margin_coin)}
        except Exception as e:
            return {"error": str(e)}
