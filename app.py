from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/scrape/quotes")
def scrape_quotes():
    result = subprocess.run(["python", "quote_scraper.py"], capture_output=True, text=True)
    return jsonify({"status": "done", "output": result.stdout})

@app.route("/scrape/japan")
def scrape_japan():
    result = subprocess.run(["python", "japan_scraper.py"], capture_output=True, text=True)
    return jsonify({"status": "done", "output": result.stdout})

@app.route("/scrape/pchome")
def scrape_pchome():
    result = subprocess.run(["python", "pchome_scraper.py"], capture_output=True, text=True)
    return jsonify({"status": "done", "output": result.stdout})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
