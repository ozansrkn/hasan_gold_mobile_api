from flask import Flask, jsonify
from flask_cors import CORS
import os
import re
import time
import requests

app = Flask(__name__)
CORS(app)

last_data = {
    "alis": "0",
    "satis": "0",
    "source": "empty",
    "updated_at": None,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/json,text/plain,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

def to_float(value):
    if value is None:
        return 0.0
    value = str(value).strip()
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    return float(value)

def format_tr(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def find_prices_fast(text):
    nums = re.findall(r"\d{4,6}[,.]\d{2}|\d{1,3}\.\d{3},\d{2}", text or "")
    values = []
    for n in nums[:300]:
        try:
            v = to_float(n)
            if 1000 <= v <= 20000:
                values.append(v)
        except Exception:
            pass

    unique = []
    for v in values:
        if all(abs(v - x) > 0.5 for x in unique):
            unique.append(v)

    unique.sort()
    if len(unique) >= 2:
        return unique[0], unique[1]
    raise RuntimeError("Fiyat bulunamadı")

def fetch_price():
    urls = [
        "https://www.haremaltin.com",
        "https://haremaltin.com",
    ]

    last_error = None
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            r.raise_for_status()
            buy, sell = find_prices_fast(r.text)
            return {
                "alis": format_tr(buy),
                "satis": format_tr(sell),
                "source": url,
            }
        except Exception as e:
            last_error = e

    raise RuntimeError(str(last_error))

def read_price():
    global last_data
    try:
        data = fetch_price()
        last_data = {
            "alis": data["alis"],
            "satis": data["satis"],
            "source": data["source"],
            "updated_at": int(time.time()),
        }
        return last_data
    except Exception as e:
        cached = dict(last_data)
        cached["source"] = "last-cache"
        cached["error"] = str(e)
        return cached

@app.route("/")
def home():
    return jsonify({
        "ok": True,
        "service": "Hasan Gold Mobile API",
        "endpoint": "/gold"
    })

@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/gold")
def gold():
    return jsonify(read_price())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
