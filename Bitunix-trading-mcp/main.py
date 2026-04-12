from fastmcp import FastMCP
from tools import market, account, trade, position, tpsl, spot

mcp = FastMCP("bitunix-futures")

market.register(mcp)
account.register(mcp)
trade.register(mcp)
position.register(mcp)
tpsl.register(mcp)
spot.register(mcp)

if __name__ == "__main__":
    mcp.run()
