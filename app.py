import os
import io
import re
import math
from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ 加入 CORS
from google.cloud import vision

# **初始化 Flask**
app = Flask(__name__)
CORS(app)  # ✅ 允許跨域請求 (CodePen 才能正常請求)

# **設定 Google Cloud API JSON 憑證**
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "mypython-449619-947c8f434081.json")
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"找不到 Google API 憑證: {cred_path}")

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
    """使用 Google Cloud Vision API 進行 OCR"""
    client = vision.ImageAnnotatorClient()

    # **確保圖片格式正確**
    content = io.BytesIO(image_file.read())  # ✅ 修正 IO 問題
    image = vision.Image(content=content.getvalue())
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description  # 取得 OCR 解析的文字
    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **判斷是否來自 Godzilla Store**
    if "godzilla.store" in raw_text.lower() or "ゴジラ・ストア" in raw_text:
        return extract_godzilla_data(raw_text)
    else:
        return {"status": "error", "message": "這不是 Godzilla Store 網站的資料"}


def extract_godzilla_data(text):
    """從 Godzilla Store OCR 結果中提取商品名稱與價格"""
    lines = text.split("\n")

    # **提取商品名稱**
    product_name = extract_product_name(lines)

    # **提取價格**
    price_jpy = extract_price(text)

    # **計算台幣報價**
    price_twd = math.ceil(price_jpy * 0.35) if price_jpy > 0 else "N/A"

    return {
        "status": "done",
        "商品名稱": product_name,
        "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy > 0 else "N/A",  # ✅ 確保前端可讀取
        "台幣報價": f"{price_twd} 元" if price_jpy > 0 else "N/A"
    }


def extract_product_name(lines):
    """從 OCR 結果中提取商品名稱"""
    product_name = "未找到商品名稱"

    for i, line in enumerate(lines):
        if "円" in line and i > 0:
            product_name = lines[i - 1].strip()
            break

    if product_name == "未找到商品名稱":
        for line in lines:
            if "ゴジラ・ストア" in line:
                index = lines.index(line)
                if index + 1 < len(lines):
                    product_name = lines[index + 1].strip()
                break

    return product_name


def extract_price(text):
    """從 OCR 文字中提取價格"""
    price_jpy = 0

    # **匹配 "￥" 或 "円" 之後的數字**
    price_match = re.search(r"[￥円]\s*([\d,]+)", text)
    if price_match:
        price_jpy = int(price_match.group(1).replace(",", ""))  # ✅ 去除千分位逗號

    return price_jpy


# **Render 需要這行來啟動 Flask**
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # ✅ 確保 Render 正確執行
