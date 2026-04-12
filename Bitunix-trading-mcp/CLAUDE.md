# Bitunix MCP Server — Claude Instructions

---

## ORDER PLACEMENT — Exact Rules

### Step 1 — Set Leverage (always first, always separate)
```
change_leverage
  symbol:   "BTCUSDT"
  leverage: 10
```

### Step 2 — Ensure ISOLATED Margin Mode
- ✅ **ALWAYS** use **ISOLATED** margin mode. NEVER use CROSS.
- If not already set, call `change_margin_mode(symbol, margin_mode="ISOLATED")`.
- *Note: If this fails with 10002, the user must change it manually on Bitunix.com or close all positions/orders first.*

### Step 3 — Place the order
```
place_order
  symbol:     "BTCUSDT"
  side:       "BUY"        ← see direction table
  trade_side: "OPEN"
  order_type: "MARKET"     ← or "LIMIT"
  qty:        "0.001"      ← string, base asset, min 0.0001 BTC
```
- LIMIT orders: add `price: "95000"`
- ❌ NEVER include `leverage` or `margin_mode` inside `place_order` → error 10002

### Direction Reference (Hedge Mode)
| Action | side | trade_side |
|--------|------|------------|
| Open Long | BUY | OPEN |
| Open Short | SELL | OPEN |
| Close Long | SELL | CLOSE |
| Close Short | BUY | CLOSE |

### Closing a position
1. `get_pending_positions` → get `position_id` and `qty`
2. `place_order` with opposite side, `trade_side: "CLOSE"`, same `qty`, include `position_id`

---

### TP/SL — Exact Rules

### Fixed tools:
- ✅ `batch_order(symbol, order_list)` — symbol at top level, orders must NOT include symbol
- ✅ `modify_position_tpsl_order` — path fixed to `/tpsl/position/modify_order`
- ✅ `place_position_tpsl_order` — path fixed to `/tpsl/position/place_order`
- ✅ `modify_tpsl_order` — fixed via internal Cancel + Re-place workaround

### Setting TP/SL — ONLY use `place_tpsl_order`
1. `get_pending_positions` → get `position_id` and `qty`
2. Call:
```
place_tpsl_order
  symbol:        "BTCUSDT"
  position_id:   "<from get_pending_positions>"
  tp_price:      "95000"
  tp_stop_type:  "MARK"      ← REQUIRED ("MARK" or "LAST_PRICE")
  tp_order_type: "MARKET"    ← REQUIRED ("MARKET" or "LIMIT")
  tp_qty:        "0.001"     ← REQUIRED: full position size as string
  sl_price:      "88000"
  sl_stop_type:  "MARK"      ← REQUIRED
  sl_order_type: "MARKET"    ← REQUIRED
  sl_qty:        "0.001"     ← REQUIRED: full position size as string
```
- TP only: omit all sl_ fields. SL only: omit all tp_ fields.

### Modifying TP/SL — 3 steps
1. `get_pending_tpsl_orders` with `symbol: "BTCUSDT"` → get order IDs
   - ❌ NEVER call without symbol → error 2
   - Empty result → no TP/SL exists, skip to step 3
   - Multiple positions: call once per symbol separately
2. `cancel_tpsl_order` with `symbol` + `tpsl_ids: ["id1", "id2"]`
3. `place_tpsl_order` with new prices

---

## Emergency Exit
```
flash_close_position
  symbol:      "BTCUSDT"
  position_id: "<from get_pending_positions>"
```
Close everything: `close_all_positions` (optionally pass symbol)

---

## Currency Conversion — Spot Tools

Spot and Futures are **separate wallets**. Transfers are required.

### Tools added (tools/spot.py, SpotClient in client.py):
| Tool | What it does |
|------|-------------|
| `convert_currency` | Full auto-flow: transfer out → spot order → transfer back |
| `funds_transfer` | Move funds between spot and futures wallet |
| `get_spot_account` | Check spot wallet balances |

### convert_currency — exact call
```
convert_currency
  from_coin: "USDC"
  to_coin:   "USDT"
  amount:    "13"
  wallet:    "futures"   ← "futures" or "spot"
```

### funds_transfer — direction values
- `"futures_spot"` = futures → spot
- `"spot_futures"` = spot → futures

### Spot API details
- Base URL: `https://openapi.bitunix.com`
- Auth: same double SHA-256 as futures API
- Spot `place_order` uses integers: `side` 1=Sell / 2=Buy, `type` 1=Limit / 2=Market
- Field name for quantity: `volume` (not `qty`)

---

| Tool | Problem | Workaround |
|------|---------|------------|
| `change_margin_mode` | Fails if positions open | Mandatory: Only use ISOLATED mode. |

| Tool | Root Cause | Fix Applied |
|------|-----------|-------------|
| `batch_order` | `symbol` was missing from top-level body | Now sends `{"symbol":…,"orderList":[…]}` |
| `modify_position_tpsl_order` | Wrong path `/tpsl/modify_position_tp_sl_order` | Now uses `/tpsl/position/modify_order` |
| `place_position_tpsl_order` | Wrong path and empty parameter validation | Now uses `/tpsl/position/place_order` and filters payload |
| `modify_tpsl_order` | Bitunix API endpoint broken (30006) | Fixed via Cancel + Re-place internal flow |

## Fixes applied in client.py

| Function | What was wrong | Fix |
|----------|---------------|-----|
| `get_pending_tpsl_orders` | Wrong endpoint path | Now uses `/tpsl/get_pending_orders` |
| `get_history_tpsl_orders` | Wrong endpoint path | Now uses `/tpsl/get_history_orders` |
| `cancel_tpsl_order` | Wrong path + field (`tpslIds`) | Now uses `/tpsl/cancel_order` with `orderId`, loops per ID |
| `cancel_orders` | Wrong body format | Now uses `{"orderList": [{"symbol":…,"orderId":…}]}` |
| `batch_order` | `symbol` missing from top level | Now sends `{"symbol":…,"orderList":[…]}` |
| `modify_position_tpsl_order` | Wrong path | Now uses `/tpsl/position/modify_order` |
