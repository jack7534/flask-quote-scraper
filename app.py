#GPT說可以抓取我網站價格跟名字 2
import os

import re
import math
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
    extracted_data["ocr_text"] = raw_text  # **✅ 確保返回完整的數據**
    return extracted_data

def extract_price_and_name(ocr_text):
    """從 OCR 文字中提取商品名稱 & 價格"""
    lines = ocr_text.split("\n")
    product_name = "未知商品"
    price_jpy = "N/A"
    price_twd = "N/A"

    # **🔍 嘗試抓取商品名稱 (通常在頂部)**
    for line in lines:
        if len(line) > 5 and not re.search(r"(税込|税抜|購入|お気に入り|ポイント|送料無料|セール|カート|条件)", line):
            if "http" not in line and "colorDisplayCode" not in line:
                product_name = line.strip()
                break

    # **🔍 嘗試抓取價格**
    tax_price_match = re.search(r"[¥]?\s*([\d,]+)\s*円?\s*\(税込\)", ocr_text)  # **直接含稅價格**
    tax_rate_match = re.search(r"税率\s*(\d+)%\s*([\d,]+)円", ocr_text)  # **稅率與未稅價格**
    base_price_match = re.search(r"([\d,]+)\s*円\s*\(税抜\)", ocr_text)  # **未稅價格**
    tmall_price_match = re.search(r"[¥]?\s*([\d,]+)\s*円(?:\s*送料無料)?", ocr_text)  # **天貓格式**
    yahoo_price_match = re.search(r"[¥]?\s*([\d,]+)\s*円(?:\s*\(税\s*\d+\s*円\))?", ocr_text)  # **奇摩格式**
    uniqlo_price_match = re.search(r"¥\s*([\d,]+)", ocr_text)  # **UNIQLO 價格 (¥1290 這種格式)**

    if tax_price_match:
        price_jpy = tax_price_match.group(1).replace(",", "")  # **直接使用含稅價格**
    elif base_price_match and tax_rate_match:
        base_price = int(base_price_match.group(1).replace(",", ""))
        tax_rate = int(tax_rate_match.group(1)) / 100
        price_jpy = str(math.ceil(base_price * (1 + tax_rate)))  # **計算含稅價格**
    elif tmall_price_match:
        price_jpy = tmall_price_match.group(1).replace(",", "")  # **天貓格式**
    elif yahoo_price_match:
        price_jpy = yahoo_price_match.group(1).replace(",", "")  # **奇摩格式**
    elif uniqlo_price_match:
        price_jpy = uniqlo_price_match.group(1).replace(",", "")  # **UNIQLO 格式 (¥1290)**
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
