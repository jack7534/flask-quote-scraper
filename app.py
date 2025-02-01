from flask import Flask, request, jsonify
from flask_cors import CORS
from quote_scraper import get_quotation  # ✅ 保持爬蟲功能
import os
import matsukiyo_ocr
import biccamera_ocr
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # ✅ 確保 CORS 啟用

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# **🔹 測試 Flask 是否運行成功**
@app.route("/")
def home():
    return "Hello, Flask!"

# **🔹 爬蟲 API (/scrape)**
@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"status": "error", "message": "請提供商品網址"}), 400

    result = get_quotation(url)
    if "錯誤" in result:
        return jsonify({"status": "error", "message": result["錯誤"]}), 400

    return jsonify({"status": "done", "data": result})

# **🔹 圖片上傳 API (/upload)**
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "沒有檔案"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "沒有選擇檔案"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # **🔸 根據文件名稱判斷 OCR 類型**
        if "matsukiyo" in filename.lower():
            result = matsukiyo_ocr.process_image(filepath)
        elif "biccamera" in filename.lower():
            result = biccamera_ocr.process_image(filepath)
        else:
            result = {"status": "error", "message": "無法識別的網站"}

        return jsonify(result)

    return jsonify({"status": "error", "message": "不支援的檔案格式"}), 400

# **🔹 啟動 Flask 服務**
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
