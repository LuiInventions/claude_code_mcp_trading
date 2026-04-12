# BitUnix Trading MCP Server

A powerful Model Context Protocol (MCP) server that provides a bridge between Claude Code and the BitUnix Exchange API. It supports both Futures and Spot trading with advanced order management.

## ✨ Features

### 📈 Futures Trading
- **Order Placement**: Market and Limit orders with hedge mode support.
- **Leverage & Margin**: Set leverage and margin mode (Isolated/Cross) per symbol.
- **Position Management**: Close positions, flash-close (emergency exit), and monitor PnL.
- **Batch Orders**: Execute up to 5 orders for the same symbol in a single call.

### 🛡️ Advanced TP/SL
- **Precise Control**: Set Take Profit and Stop Loss with specific trigger types (Mark/Last Price).
- **Modification Workaround**: Includes an internal "Cancel + Re-place" logic to bypass BitUnix API limitations, ensuring reliable TP/SL updates.

### 💰 Spot Trading & Conversion
- **Spot Wallet**: Full access to spot balances and trading pairs.
- **Auto-Conversion**: A unique `convert_currency` tool that automates the transfer between Futures and Spot wallets to convert assets (e.g., USDC ↔ USDT) in one step.

## 🛠️ Installation

### Prerequisites
- **Node.js**: Used for the MCP bridge wrapper.
- **Python 3.10+**: Used for the core logic (FastMCP).
- **BitUnix API Keys**: Required for private operations.

### Setup
1. Open the `.env` file and enter your API keys.
   - **Where to get keys?** Log in to your BitUnix account and go to: [https://www.bitunix.com/account/apiManagement](https://www.bitunix.com/account/apiManagement)
   - *Manual path: Hover over your Profile Icon (top-right) -> Click "API"*
2. Enter your `BITUNIX_API_KEY` and `BITUNIX_SECRET_KEY` in the file.
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### Claude Code Configuration
Add the server to your `.mcp.json` file. Ensure the path to `index.js` is correct:

```json
{
  "mcpServers": {
    "bitunix": {
      "command": "node",
      "args": ["./Bitunix-trading-mcp/index.js"]
    }
  }
}
```

### Manual Startup (for Testing)
You can start the server manually to verify it's working:
```bash
node index.js
```
Upon startup, the server will output its status to `stderr`, including the Python path and process ID. It will then wait for MCP JSON-RPC messages on `stdin`.

### Key Tools & Examples
- `get_account`: Check your available balance.
- `place_order`: Open a new position.
- `place_tpsl_order`: Set protection for an open position.
- `convert_currency`: Move and convert funds between wallets.

**Example Tool Call (JSON-RPC):**
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_account",
    "arguments": { "margin_coin": "USDT" }
  }
}
```

## ⚙️ How it Works (Architecture)
The server uses a **dual-layer architecture**:
1. **Node.js Wrapper (`index.js`)**: Acts as the entry point for Claude Code. It searches for a valid Python executable on your system, loads environment variables from `.env`, and spawns the Python process.
2. **Python Core (`main.py`)**: Uses the `FastMCP` framework to define and register trading tools. It handles the actual API communication with BitUnix using the `BitunixClient` class.

## ❓ Troubleshooting

### 1. Python not found
The Node wrapper tries to find `python3`, `python`, or `py`. If it fails, ensure Python is in your system's PATH. You can check what the server is using by looking at the terminal output:
`Python: C:\Path\To\python.exe`

### 2. API Errors (Code 2, 10002, etc.)
- **Error 10002**: Often caused by trying to set leverage/margin *inside* an order call. The server requires you to set these separately first.
- **Error 2**: Usually means a required parameter is missing or formatted incorrectly.

### 3. Connection Issues
Ensure your `.env` file is in the `Bitunix-trading-mcp` directory and contains valid keys. The server will output a warning if the `.env` file cannot be read.

## 🔒 Security
- **Environment Variables**: Sensitive keys are loaded from `.env` and are excluded from Git via `.gitignore`.
- **Hedge Mode**: The server defaults to Hedge Mode (separate Long/Short) as required by professional trading standards.

## 📄 License
MIT
