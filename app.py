from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timezone

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
