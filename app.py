from flask import Flask, jsonify, send_from_directory
import os, time, requests
from datetime import datetime, timezone

app = Flask(__name__, static_folder="frontend")
TIMEOUT = 10

def req(name, url, params=None, headers=None):
    started = time.perf_counter()
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        result = {"http_status": r.status_code,
                  "latency_ms": round((time.perf_counter()-started)*1000)}
        if r.status_code != 200:
            result.update(ok=False, error=r.text[:500])
            return result
        return r, result
    except requests.exceptions.Timeout:
        return {"ok": False, "http_status": None, "latency_ms": round((time.perf_counter()-started)*1000), "error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "http_status": None, "latency_ms": round((time.perf_counter()-started)*1000), "error": str(e)}

def test_coingecko():
    x=req("CoinGecko","https://api.coingecko.com/api/v3/simple/price",{"ids":"bitcoin","vs_currencies":"usd"},{"User-Agent":"ODVUT-API-Test/1.0"})
    if not isinstance(x, tuple): return x
    r,m=x; m.update(ok=True,price=r.json()["bitcoin"]["usd"]); return m

def test_coinpaprika():
    x=req("CoinPaprika","https://api.coinpaprika.com/v1/tickers/btc-bitcoin",headers={"User-Agent":"ODVUT-API-Test/1.0"})
    if not isinstance(x, tuple): return x
    r,m=x; m.update(ok=True,price=r.json()["quotes"]["USD"]["price"]); return m

def test_kraken():
    x=req("Kraken","https://api.kraken.com/0/public/Ticker",{"pair":"XBTUSD"},{"User-Agent":"ODVUT-API-Test/1.0"})
    if not isinstance(x, tuple): return x
    r,m=x; d=r.json()
    if d.get("error"): m.update(ok=False,error=str(d["error"])); return m
    m.update(ok=True,price=float(next(iter(d["result"].values()))["c"][0])); return m

def test_coinbase():
    x=req("Coinbase","https://api.exchange.coinbase.com/products/BTC-USD/ticker",headers={"User-Agent":"ODVUT-API-Test/1.0"})
    if not isinstance(x, tuple): return x
    r,m=x; m.update(ok=True,price=float(r.json()["price"])); return m

def test_cmc():
    key=os.getenv("CMC_API_KEY")
    if not key: return {"ok":None,"http_status":None,"latency_ms":0,"error":"CMC_API_KEY is not configured"}
    x=req("CoinMarketCap","https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
          {"symbol":"BTC","convert":"USD"},
          {"X-CMC_PRO_API_KEY":key,"Accepts":"application/json","User-Agent":"ODVUT-API-Test/1.0"})
    if not isinstance(x, tuple): return x
    r,m=x; m.update(ok=True,price=r.json()["data"]["BTC"]["quote"]["USD"]["price"]); return m

TESTS={"CoinGecko":test_coingecko,"CoinPaprika":test_coinpaprika,"Kraken":test_kraken,"Coinbase":test_coinbase,"CoinMarketCap":test_cmc}

@app.route("/")
def home(): return send_from_directory("frontend","index.html")

@app.route("/api/status")
def status():
    return jsonify(status="online",message="ODVUT Backend is working!",server_time=datetime.now(timezone.utc).isoformat())

@app.route("/api/test-apis")
def test_apis():
    results={}
    for name,fn in TESTS.items():
        print(f"[API TEST] {name}: testing...")
        try: results[name]=fn()
        except Exception as e: results[name]={"ok":False,"http_status":None,"error":str(e)}
        print(f"[API TEST] {name}: {results[name]}")
    working=[n for n,v in results.items() if v.get("ok") is True]
    return jsonify(server_time=datetime.now(timezone.utc).isoformat(),render_test=True,
                   working_count=len(working),working_apis=working,results=results)

if __name__=="__main__": app.run(host="0.0.0.0",port=5000)
