# ccxt-trade-checker

Minimal pre-trade health check for crypto perpetuals using Python + ccxt.  
Pulls live fees/funding/orderbook and estimates if a $10k **taker** trade beats costs.  

## What it checks
- Fees (bps): maker/taker
- Funding rate (bps per 8h)
- Bid–ask spread (bps)
- API latency (ms)
- Impact/slippage (bps) for $10k
- Decision: `TRADE` if `expected > total_cost` and `risk == OK`, else `SKIP`  
  (Demo uses funding as `expected`; replace with your own edge.)

## Example output
Ex=bybit  Sym=BTC/USDT:USDT  mid=110123.75  
fee mk/tk = 1.00/5.00 bps   funding = 1.00 bps/8h  
spread = 0.01 bps   latency = 178 ms   risk=OK  
impact = 0.00 bps  notional=$10000  
--- decision ---  
expected = 1.00   total_cost = 5.00   after_cost = -4.00 bps  
Action: SKIP

## Quickstart (Windows PowerShell)
`cd $HOME\quant-edge` → `python -m venv .venv` → `.\.venv\Scripts\Activate.ps1` → `pip install -U pip ccxt` → `python .\edge_live.py`

## Configure (edit `edge_live.py`)
`EXCHANGE="bybit"| "okx" | "binance"`, `SYMBOL="BTC/USDT"`, `NOTIONAL_USD=10000`, `MAX_SPREAD_BPS=3.0`, `MAX_LATENCY_MS=200`.  
Simulate short: change `impact_bps(...,"buy",...)` to `"sell"`.

## Notes
- 1 bps = 0.01% (on $10k, ≈ $1).  
- You pay **maker OR taker** per fill; funding is paid **between longs/shorts**, not to the exchange.

Built with ccxt: https://github.com/ccxt/ccxt
