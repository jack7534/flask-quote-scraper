from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json  # 接收 JSON 格式的請求
    url = data.get("url", "")  # 取得網址
    if not url:
        return jsonify({"status": "error", "message": "請提供商品網址"}), 400

    # 根據網址判斷要使用哪個爬蟲
    if "amazon" in url:
        script = "amazon_scraper.py"
    elif "tmall" in url:
        script = "tmall_scraper.py"
    elif "yahoo" in url:
        script = "yahoo_scraper.py"
    else:
        return jsonify({"status": "error", "message": "不支援的網站"}), 400

    # 執行對應的爬蟲
    result = subprocess.run(["python", script, url], capture_output=True, text=True)

    return jsonify({"status": "done", "output": result.stdout})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
