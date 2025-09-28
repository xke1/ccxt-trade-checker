import time, ccxt

EXCHANGE = "bybit"
SYMBOL   = "BTC/USDT"
NOTIONAL_USD = 10000

MAX_SPREAD_BPS = 3.0
MAX_LATENCY_MS = 200

def load_exchange(name):
    if name=="bybit":
        ex = ccxt.bybit({"options":{"defaultType":"swap"}}); perp="BTC/USDT:USDT"
    elif name=="okx":
        ex = ccxt.okx({"options":{"defaultType":"swap"}});  perp="BTC-USDT-SWAP"
    elif name=="binance":
        ex = ccxt.binance({"options":{"defaultType":"future"}}); perp="BTC/USDT"
    else:
        raise ValueError("unsupported exchange")
    return ex, perp

def fees_bps(ex, sym):
    try:
        f = ex.fetch_trading_fee(sym)
        mk = (f.get("maker",0) or 0.0001) * 1e4
        tk = (f.get("taker",0) or 0.0005) * 1e4
        return mk, tk
    except:
        return 1.0, 5.0

def funding_bps(ex, sym):
    try:
        fr = ex.fetch_funding_rate(sym)
        r  = fr.get("fundingRate", 0.0) or fr.get("info",{}).get("fundingRate",0.0)
        return float(r) * 1e4
    except:
        return 0.0

def orderbook_latency(ex, sym, depth=50):
    t0 = time.time()
    ob = ex.fetch_order_book(sym, limit=depth)
    lat = (time.time()-t0)*1000.0
    return ob, lat

def spread_bps(ob):
    bid = ob["bids"][0][0]; ask = ob["asks"][0][0]
    mid = (bid+ask)/2
    return bid, ask, mid, (ask-bid)/mid*1e4

def impact_bps(ob, notional_usd, side, mid):
    book = ob["asks"] if side=="buy" else ob["bids"]
    remaining = notional_usd; qty=0.0; cost=0.0
    for price, size in book:
        take_value = min(remaining, price*size)
        q = take_value/price; qty += q; cost += q*price
        remaining -= take_value
        if remaining <= 1e-9: break
    if remaining > 1e-6:
        return 9999.0
    vwap = cost/qty
    return max(0.0, (vwap-mid)/mid*1e4 if side=="buy" else (mid-vwap)/mid*1e4)

def main():
    ex, perp = load_exchange(EXCHANGE)
    mk, tk   = fees_bps(ex, perp)
    frbps    = funding_bps(ex, perp)
    ob, lat  = orderbook_latency(ex, perp, depth=50)
    bid, ask, mid, spd = spread_bps(ob)

    gates=[]
    if spd > MAX_SPREAD_BPS: gates.append(f"PAUSE spread {spd:.1f}bps")
    if lat > MAX_LATENCY_MS: gates.append(f"PAUSE latency {lat:.0f}ms")
    risk = "OK" if not gates else " | ".join(gates)

    imp = impact_bps(ob, NOTIONAL_USD, "buy", mid)

    expected   = max(frbps, 0.0)
    total_cost = tk + imp
    after_cost = expected - total_cost

    print(f"Ex={EXCHANGE}  Sym={perp}  mid={mid:.2f}")
    print(f"fee mk/tk = {mk:.2f}/{tk:.2f} bps   funding = {frbps:.2f} bps/8h")
    print(f"spread    = {spd:.2f} bps           latency = {lat:.0f} ms  risk={risk}")
    print(f"impact    = {imp:.2f} bps  notional=${NOTIONAL_USD}")
    print('--- decision ---')
    print(f"expected  = {expected:.2f}  total_cost = {total_cost:.2f}  after_cost = {after_cost:.2f} bps")
    print('Action:', 'TRADE' if (after_cost>0 and risk=='OK') else 'SKIP')

if __name__ == '__main__':
    main()
