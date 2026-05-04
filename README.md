# 🚀 Claude Trading Suite

<div align="center">

[![Stars](https://img.shields.io/github/stars/LuiInventions/claude_code_mcp_trading?style=for-the-badge&color=yellow)](https://github.com/LuiInventions/claude_code_mcp_trading/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![JavaScript](https://img.shields.io/badge/JavaScript-Node.js-F7DF1E?style=for-the-badge&logo=javascript)](https://nodejs.org)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Claude](https://img.shields.io/badge/Powered%20by-Claude%20Code-orange?style=for-the-badge)](https://claude.ai/code)

**Give Claude Code access to your TradingView charts and BitUnix exchange — and let it trade like a professional.**

[🚀 Quick Start](#-installation--setup) · [✨ Features](#-features) · [📄 Daily Workflow](#-daily-workflow)

> ⭐ **If this saves you time, please star the repo — it helps the project grow!**

</div>

---

## 🤔 What Is This?

The **Claude Trading Suite** connects **Claude Code** (Anthropic’s AI coding agent) directly to your **TradingView Desktop** and **BitUnix Exchange** via the Model Context Protocol (MCP). Instead of hardcoded rules, Claude reads your actual charts, interprets indicators, and places real orders — with human-level reasoning.

Think of it as hiring an AI trading assistant that actually sees what you see.

---

## ✨ Features

### 📊 Advanced Charting (via TradingView MCP)
- **Morning Brief** — Scan your full watchlist and get a structured session bias in seconds
- **Chart Intelligence** — Claude reads your RSI, MAs, and custom Pine Script labels/drawings
- **Automation** — Multi-pane layout control, symbol switching, screenshot analysis
- **Replay Trading** — Practice strategies with bar-by-bar historical replay

### 📈 Precision Execution (via BitUnix MCP)
- **Hedge Mode** — Full support for simultaneous Long/Short positions
- **Advanced TP/SL** — Reliable internal "Cancel + Re-place" workaround
- **Smart Conversion** — Move and convert funds between Spot and Futures (USDC ↔ USDT)
- **Batch Ordering** — Execute complex multi-order strategies in one command

---

## 🛠️ Prerequisites

| Requirement | Note |
|-------------|------|
| [Claude Code](https://claude.ai/code) | `npm install -g @anthropic-ai/claude-code` |
| [TradingView Desktop](https://de.tradingview.com/desktop/) | Required for CDP/MCP chart access |
| Python 3.10+ | For BitUnix core logic |
| Node.js 18+ | For the MCP bridge |

---

## 🚀 Installation & Setup

### 1. Clone the repository
```powershell
git clone https://github.com/LuiInventions/claude_code_mcp_trading
cd claude_code_mcp_trading
```

### 2. Run the automated setup (first time only)
```powershell
.\setup.ps1
```

The script will:
- 📦 Install missing Node.js, Python, and all package dependencies
- 🔍 Detect your TradingView installation (Microsoft Store, Portable, or Desktop)
- 🔑 Prompt for your [BitUnix API Keys](https://www.bitunix.com/account/apiManagement) and save to `.env`
- 🛠️ Generate your personalized `start-trading.bat` launcher

### 3. Start trading
```
Double-click: start-trading.bat
```

Test MCP connections anytime with `/mcp` inside Claude.

---

## 🔄 Daily Workflow

1. **Launch** — Run `start-trading.bat` (starts TradingView in debug mode + opens BitUnix)
2. **Analyze** — *"Run my morning brief and give me session bias for BTC and ETH."*
3. **Execute** — *"Place a long market order for BTC with 10x leverage and a 2% Stop Loss."*

---

## 📜 Credits

- **TradingView MCP** — Improved fork of [LewisWJackson/tradingview-mcp-jackson](https://github.com/LewisWJackson/tradingview-mcp-jackson)
- **BitUnix MCP** — Built specifically for this suite

---

## ⚠️ Disclaimer

Trading involves significant risk of loss. This software is for educational and research purposes only. Always test in a safe environment first. Use at your own risk.

---

## 📄 License

MIT

---

<div align="center">

**Useful? Drop a ⭐ — takes 2 seconds and helps others find this project.**

</div>
