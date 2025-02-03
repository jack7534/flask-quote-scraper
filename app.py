# 增加 PC 判定式 版本
import os
import io
import json
import math
import re
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import vision
from dotenv import load_dotenv

# **載入環境變數**
load_dotenv()

# **初始化 Flask**
app = Flask(__name__)
CORS(app)

# **讀取 Google Cloud API JSON 憑證**
cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
cred_path = "/opt/render/project/.creds/google_api.json"

if not cred_json:
    raise ValueError("❌ 找不到 Google Cloud 憑證")

# **寫入憑證 JSON 檔案**
os.makedirs(os.path.dirname(cred_path), exist_ok=True)
with open(cred_path, "w") as f:
    f.write(cred_json)

# **設置 GOOGLE_APPLICATION_CREDENTIALS**
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path


@app.route("/upload", methods=["POST"])
def upload_file():
    """上傳圖片並進行 OCR 分析"""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "沒有檔案"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "沒有選擇檔案"}), 400

    try:
        result = process_image(file)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500


def process_image(image_file):
    """使用 Google Cloud Vision API 進行 OCR 並提取商品名稱 & 價格"""
    client = vision.ImageAnnotatorClient()
    content = image_file.read()
    if not content:
        return {"status": "error", "message": "圖片讀取失敗"}

    image = vision.Image(content=content)
    time.sleep(1)  # **確保完整讀取**

    response = client.text_detection(image=image)

    if response.error.message:
        return {"status": "error", "message": f"Google Vision API 錯誤: {response.error.message}"}

    texts = response.text_annotations
    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description  # ✅ **OCR 解析結果**
    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **從 OCR 文字中提取商品名稱 & 價格**
    extracted_data = extract_price_and_name(raw_text)

    # **✅ 確保返回完整的數據**
    extracted_data["ocr_text"] = raw_text
    return extracted_data


def extract_price_and_name(ocr_text):
    """從 OCR 文字中提取商品名稱 & 價格"""
    lines = ocr_text.split("\n")
    product_name = "未知商品"
    price_jpy = "N/A"
    price_twd = "N/A"

    # **🔍 嘗試抓取商品名稱 (手機版 & PC 版)**
    for line in lines:
        clean_line = line.strip()
        if len(clean_line) > 6 and not re.search(r"(税込|税抜|購入|お気に入り|ポイント|送料無料|条件|カート)",
                                                 clean_line):
            if "http" not in clean_line and "colorDisplayCode" not in clean_line:
                product_name = clean_line
                break

    # **🔍 優先抓取含稅價格**
    tax_price_match = re.search(r"¥\s*([\d,]+)\s*\(税込\)", ocr_text)
    normal_price_match = re.search(r"¥\s*([\d,]+)", ocr_text)

    # **🔍 其他價格顯示格式 (樂天、Amazon)**
    alt_price_match = re.search(r"([\d,]+)\s*円", ocr_text)

    if tax_price_match:
        price_jpy = tax_price_match.group(1).replace(",", "")  # **含稅價格**
    elif normal_price_match:
        price_jpy = normal_price_match.group(1).replace(",", "")  # **未標明含稅價格**
    elif alt_price_match:
        price_jpy = alt_price_match.group(1).replace(",", "")  # **一般日幣價格**

    if price_jpy != "N/A":
        price_twd = str(math.ceil(int(price_jpy) * 0.35))  # **台幣換算**

    return {
        "status": "done",
        "商品名稱": product_name,
        "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy != "N/A" else "N/A",
        "台幣報價": f"{price_twd} 元" if price_twd != "N/A" else "N/A"
    }

# **啟動 Flask**
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)