# 🚀 Claude Trading Suite

Welcome to the **Claude Trading Suite** — a powerful, AI-driven trading environment that connects **Claude Code** directly to your **TradingView Desktop** and **BitUnix Exchange**. 

This suite transforms Claude from a coding assistant into a professional trading partner that can analyze charts, manage watchlists, and execute orders with human-like reasoning and machine precision.

---

## ✨ Features

### 📊 Advanced Charting (via TradingView MCP)
*   **Morning Brief**: Scan your entire watchlist and get a structured session bias in seconds.
*   **Chart Intelligence**: Claude can "see" your indicators (RSI, Moving Averages, etc.) and read custom Pine Script labels/drawings.
*   **Automation**: Multi-pane layout control, automated symbol switching, and screenshot analysis.
*   **Replay Trading**: Practice your strategies with bar-by-bar historical replay.

### 📈 Precision Execution (via BitUnix MCP)
*   **Hedge Mode Trading**: Full support for simultaneous Long/Short positions.
*   **Advanced TP/SL**: Precise protection logic with an internal "Cancel + Re-place" workaround for maximum reliability.
*   **Smart Conversion**: Integrated tools to move and convert funds between Spot and Futures wallets (USDC ↔ USDT).
*   **Batch Ordering**: Execute complex multi-order strategies in a single command.

---

## 🛠️ Prerequisites

*   **Claude Code**: Must be installed globally (`npm install -g @anthropic-ai/claude-code`).
*   **TradingView Desktop**: The official desktop app (required for CDP support).
*   **Python 3.10+**: For the BitUnix core logic.
*   **Node.js 18+**: For the MCP bridge architecture.

---

## 🚀 Installation & Setup

Log in to your BitUnix account and go to: https://www.bitunix.com/account/apiManagement
to get your api key, so the agent can acces your trading account

Tradingview mcp uses your local Tradingview (install at: https://de.tradingview.com/desktop/)
to analyze charts and use strategies

### Open a PowerShell terminal in the project directory and run:

### 1. Clone the Suite
```powershell
git clone https://github.com/LuiInventions/claude_code_mcp_trading
```
Go to main Folder
```powershell
cd claude_code_mcp_trading
```

### 2. Run the Automated Setup (Initial Setup Only)
```powershell
.\setup.ps1
```
The setup script will:
- 📦 **Dependencies**: Automatically install missing Node.js, Python, and package libraries.
- 🔍 **TradingView**: Automatically find your TradingView installation (Microsoft Store, Portable, or Desktop).
- 🔑 **API Keys**: Prompt you for your BitUnix API Keys and save them securely to `.env`.
- 🛠️ **Launcher**: Generate your personalized `start-trading.bat` file.

### 3. Connect to Claude Code
Add the suite to your Claude Code configuration (`.mcp.json`):

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "node",
      "args": ["./tradingview-mcp-jackson/src/server.js"]
    },
    "bitunix": {
      "command": "node",
      "args": ["./Bitunix-trading-mcp/index.js"]
    }
  }
}
```

---

## 🔄 Daily Workflow

1.  **Launch**: Run your generated `start-trading.bat`. This starts TradingView in debug mode and opens your BitUnix dashboard.
2.  **Analyze**: Ask Claude: `"Run my morning brief and give me my session bias for BTC and ETH."`
3.  **Execute**: Once you have your bias, ask: `"Place a long market order for BTC with 10x leverage and a 2% Stop Loss."`

---

## 📜 Credits & Disclaimer

### Credits
*   **TradingView MCP Jackson**: The charting component is an improved fork of the original work by **[LewisWJackson](https://github.com/LewisWJackson/tradingview-mcp-jackson)**. This suite integrates his excellent work to provide professional-grade chart interaction.
*   **BitUnix MCP**: Developed specifically for this suite to provide high-performance exchange connectivity.

### Disclaimer
**Use at your own risk.** Trading involves significant risk of loss. This software is for educational and research purposes. We are not responsible for any financial losses or account consequences. Always test strategies in a safe environment first.

---

## 📄 License
MIT
