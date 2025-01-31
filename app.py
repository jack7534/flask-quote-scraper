from flask import Flask, request, jsonify
from flask_cors import CORS
from quote_scraper import get_quotation  # ✅ 直接匯入函數，避免 subprocess 問題

app = Flask(__name__)
CORS(app)  # 確保 CORS 啟用

# 測試 Flask 是否運行成功
@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json  # 接收 JSON 格式的請求
    url = data.get("url", "").strip()  # 取得傳入的 URL，並去除前後空格

    if not url:
        return jsonify({"status": "error", "message": "請提供商品網址"}), 400

    # 直接調用 `get_quotation(url)` 來處理爬蟲
    result = get_quotation(url)

    if "錯誤" in result:
        return jsonify({"status": "error", "message": result["錯誤"]}), 400

    return jsonify({"status": "done", "data": result})  # ✅ 直接回傳 JSON 結果

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)  # 改成適當的 Port
