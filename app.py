from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timezone
import requests

app = Flask(__name__, static_folder="frontend", static_url_path="")

@app.get("/")
def home():
    return send_from_directory("frontend", "index.html")

@app.get("/api/status")
def status():
    return jsonify({
        "status": "online",
        "message": "ODVUT Backend is working!",
        "server_time": datetime.now(timezone.utc).isoformat()
    })

@app.get("/api/price")
def btc_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        return jsonify({
            "symbol": data["symbol"],
            "price_usdt": float(data["price"]),
            "source": "Binance",
            "server_time": datetime.now(timezone.utc).isoformat()
        })
    except requests.RequestException as e:
        return jsonify({"error": "Could not fetch BTC price", "details": str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
