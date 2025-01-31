from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)  # 確保 CORS 啟用

# ✅ 新增這個函數來測試 Flask 是否運行成功
@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json  # 接收 JSON 格式的請求
    url = data.get("url", "").strip()  # 取得傳入的 URL，並去除前後空格

    if not url:
        return jsonify({"status": "error", "message": "請提供商品網址"}), 400

    # 判斷來源
    if "amazon" in url:
        script = "quote_scraper.py"
    else:
        return jsonify({"status": "error", "message": "不支援的網站"}), 400

    # 執行爬蟲腳本
    try:
        result = subprocess.run(["python", script, url], capture_output=True, text=True, check=True)
        return jsonify({"status": "done", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": "爬蟲執行失敗", "error": e.stderr}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)  # 改成適當的 Port
