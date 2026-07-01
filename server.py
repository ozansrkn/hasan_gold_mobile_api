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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

def clean_price(text):
    if not text:
        return None
    text = str(text).strip()
    match = re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2}|\d+", text)
    return match.group(0) if match else None

def normalize_to_float(price):
    if not price:
        return 0.0
    price = str(price).strip()
    if "," in price:
        price = price.replace(".", "").replace(",", ".")
    return float(price)

def format_tr(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fetch_from_harem():
    url = "https://www.haremaltin.com"
    response = requests.get(url, headers=HEADERS, timeout=12)
    response.raise_for_status()
    html = response.text

    patterns = [
        r'id=["\']alis__ALTIN["\'][^>]*>(.*?)<.*?id=["\']satis__ALTIN["\'][^>]*>(.*?)<',
        r'id=["\']priceAlis["\'][^>]*>(.*?)<.*?id=["\']priceSatis["\'][^>]*>(.*?)<',
        r'alis__ALTIN.*?(\d{1,3}(?:\.\d{3})*,\d{2}).*?satis__ALTIN.*?(\d{1,3}(?:\.\d{3})*,\d{2})',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.S | re.I)
        if m:
            alis = clean_price(m.group(1))
            satis = clean_price(m.group(2))
            if alis and satis:
                return {"alis": alis, "satis": satis, "source": "haremaltin"}

    # Son çare: sayfadaki 5 haneli/virgüllü fiyatları yakala
    nums = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", html)
    values = []
    for n in nums:
        try:
            v = normalize_to_float(n)
            if 1000 <= v <= 20000:
                values.append((n, v))
        except Exception:
            pass

    if len(values) >= 2:
        values = sorted(values, key=lambda x: x[1])
        return {
            "alis": values[0][0],
            "satis": values[1][0],
            "source": "haremaltin-body",
        }

    raise RuntimeError("Harem Altın fiyat bulunamadı")

def read_price():
    global last_data

    try:
        data = fetch_from_harem()
        alis_v = normalize_to_float(data["alis"])
        satis_v = normalize_to_float(data["satis"])

        if alis_v > 0 and satis_v > 0:
            last_data = {
                "alis": format_tr(alis_v),
                "satis": format_tr(satis_v),
                "source": data.get("source", "web"),
                "updated_at": int(time.time()),
            }
            return last_data

        raise RuntimeError("Geçersiz fiyat")

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
