from flask import Flask, jsonify, send_from_directory
import requests
from datetime import datetime, timezone

app = Flask(__name__, static_folder="frontend")


# -----------------------------
# Frontend
# -----------------------------
@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")


# -----------------------------
# Backend status
# -----------------------------
@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "message": "ODVUT Backend is working!",
        "server_time": datetime.now(timezone.utc).isoformat()
    })


# -----------------------------
# Binance price
# -----------------------------
def get_binance_price():
    urls = [
        "https://api.binance.com/api/v3/ticker/price",
        "https://api-gcp.binance.com/api/v3/ticker/price",
        "https://api1.binance.com/api/v3/ticker/price",
        "https://api2.binance.com/api/v3/ticker/price",
        "https://api3.binance.com/api/v3/ticker/price",
        "https://api4.binance.com/api/v3/ticker/price"
    ]

    last_error = None

    for url in urls:
        try:
            print(f"[BINANCE] Trying: {url}")

            response = requests.get(
                url,
                params={"symbol": "BTCUSDT"},
                timeout=8
            )

            print(
                f"[BINANCE] HTTP {response.status_code} "
                f"from {url}"
            )

            if response.status_code != 200:
                print(
                    f"[BINANCE] Response: "
                    f"{response.text[:300]}"
                )
                last_error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )
                continue

            data = response.json()

            if "price" not in data:
                last_error = f"Unexpected response: {data}"
                continue

            return {
                "price": float(data["price"]),
                "source": "Binance",
                "symbol": "BTC/USDT"
            }

        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            print(f"[BINANCE] Timeout: {url}")

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            print(f"[BINANCE] Request error: {e}")

        except Exception as e:
            last_error = str(e)
            print(f"[BINANCE] Unknown error: {e}")

    return None, last_error


# -----------------------------
# Bybit fallback
# -----------------------------
def get_bybit_price():
    url = "https://api.bybit.com/v5/market/tickers"

    try:
        print("[BYBIT] Trying BTCUSDT...")

        response = requests.get(
            url,
            params={
                "category": "spot",
                "symbol": "BTCUSDT"
            },
            timeout=8
        )

        print(f"[BYBIT] HTTP {response.status_code}")

        if response.status_code != 200:
            print(
                f"[BYBIT] Response: "
                f"{response.text[:300]}"
            )

            return None, (
                f"HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

        data = response.json()

        if data.get("retCode") != 0:
            error = data.get("retMsg", "Unknown Bybit error")
            print(f"[BYBIT] API error: {error}")
            return None, error

        ticker_list = data.get("result", {}).get("list", [])

        if not ticker_list:
            return None, "No ticker data returned"

        price = ticker_list[0].get("lastPrice")

        if not price:
            return None, "lastPrice missing"

        return {
            "price": float(price),
            "source": "Bybit",
            "symbol": "BTC/USDT"
        }, None

    except requests.exceptions.Timeout:
        print("[BYBIT] Timeout")
        return None, "Request timeout"

    except requests.exceptions.RequestException as e:
        print(f"[BYBIT] Request error: {e}")
        return None, str(e)

    except Exception as e:
        print(f"[BYBIT] Unknown error: {e}")
        return None, str(e)


# -----------------------------
# BTC price API
# -----------------------------
@app.route("/api/price")
def price():

    # 1. Try Binance
    binance_result, binance_error = get_binance_price()

    if binance_result:
        return jsonify({
            "status": "success",
            **binance_result
        })

    print(
        f"[PRICE] Binance failed: "
        f"{binance_error}"
    )

    # 2. Try Bybit
    bybit_result, bybit_error = get_bybit_price()

    if bybit_result:
        return jsonify({
            "status": "success",
            **bybit_result,
            "fallback": True,
            "binance_error": binance_error
        })

    print(
        f"[PRICE] Bybit failed: "
        f"{bybit_error}"
    )

    # Both failed
    return jsonify({
        "status": "error",
        "message": "All price APIs failed",
        "binance_error": binance_error,
        "bybit_error": bybit_error
    }), 502


# -----------------------------
# Run locally
# -----------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
