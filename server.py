from flask import Flask, jsonify, send_file, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
import os

app = Flask(__name__)
CORS(app)

last_data = {
    "alis": "0",
    "satis": "0",
    "source": "empty"
}

def clean_price(text):
    if not text:
        return None

    text = text.strip()
    match = re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2}|\d+", text)

    if not match:
        return None

    return match.group(0)

def connect_chrome():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Chrome(options=options)

driver = connect_chrome()

def read_price():
    global last_data

    selectors = [
        ("alis__ALTIN", "satis__ALTIN"),
        ("priceAlis", "priceSatis"),
        ("alis_ALTIN", "satis_ALTIN"),
        ("priceBuy", "priceSatis"),
    ]

    try:
        if "haremaltin.com" not in driver.current_url:
            driver.get("https://www.haremaltin.com")
            time.sleep(4)

        for alis_id, satis_id in selectors:
            try:
                alis_text = driver.find_element(By.ID, alis_id).text
                satis_text = driver.find_element(By.ID, satis_id).text

                alis = clean_price(alis_text)
                satis = clean_price(satis_text)

                if alis and satis:
                    last_data = {
                        "alis": alis,
                        "satis": satis,
                        "source": f"{alis_id}/{satis_id}"
                    }
                    return last_data
            except:
                pass

        page = driver.find_element(By.TAG_NAME, "body").text
        numbers = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", page)

        if len(numbers) >= 2:
            last_data = {
                "alis": numbers[0],
                "satis": numbers[1],
                "source": "body-text"
            }
            return last_data

        return last_data

    except Exception as e:
        return {
            "alis": last_data["alis"],
            "satis": last_data["satis"],
            "source": "last-cache",
            "error": str(e)
        }

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/gold")
def gold():
    data = read_price()
    return jsonify(data)

@app.route("/icons/<path:filename>")
def icons(filename):
    return send_from_directory("icons", filename)

@app.route("/Logo.png")
def logo():
    return send_file("Logo.png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
