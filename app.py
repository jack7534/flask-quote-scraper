from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import matsukiyo_ocr
import biccamera_ocr
from werkzeug.utils import secure_filename

# ✅ 設定 Google Cloud API 金鑰
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcloud-key.json"

# ✅ 建立 Flask App
app = Flask(__name__)
CORS(app)  # 確保 CORS 啟用

# ✅ Render 無法寫入根目錄，使用 /tmp 作為可寫入目錄
UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保目錄存在

# **🔹 測試 Flask 是否運行成功**
@app.route("/")
def home():
    return "Hello, Flask!"

# **🔹 檢查允許的檔案格式**
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

# **🔹 圖片上傳並自動選擇 OCR 處理方式**
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "沒有檔案"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "沒有選擇檔案"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)  # ✅ 確保檔案被儲存

        try:
            print(f"📂 正在處理檔案: {filepath}")  # Debug 記錄

            # **🔹 先用 BicCamera OCR 解析**
            result = biccamera_ocr.process_image(filepath)

            # **如果 BicCamera 失敗，換 Matsukiyo OCR 嘗試**
            if result.get("status") == "error":
                print("⚠️ BicCamera OCR 失敗，改用 Matsukiyo OCR")
                result = matsukiyo_ocr.process_image(filepath)

            # **如果都失敗，回傳錯誤**
            if result.get("status") == "error":
                return jsonify({"status": "error", "message": "OCR 解析失敗，可能是無法識別的網站"}), 400

            print("✅ OCR 解析成功")
            return jsonify(result)

        except Exception as e:
            print(f"❌ 伺服器錯誤: {str(e)}")
            return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500

    return jsonify({"status": "error", "message": "不支援的檔案格式"}), 400

# **🔹 啟動 Flask 服務**
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 預設使用 Render 給的 PORT
    app.run(host="0.0.0.0", port=port, debug=True)
