import os
from google.cloud import vision
import io
import re
import math

# ✅ 自動判斷環境，確保本地端與雲端皆可運作
if os.getenv("RENDER") == "true":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcloud-key.json"
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Jack/PycharmProjects/PythonProject/mypython-449619-947c8f434081.json"

def process_image(image_path):
    """ 使用 Google Cloud Vision API 進行 OCR """
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description  # 取得 OCR 解析的文字

    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **🔹 判斷是否來自 Godzilla Store**
    if "godzilla.store" in raw_text.lower() or "ゴジラ・ストア" in raw_text:
        return extract_godzilla_data(raw_text)
    else:
        return {"status": "error", "message": "這不是 Godzilla Store 網站的資料"}

def extract_godzilla_data(text):
    """ 從 Godzilla Store OCR 結果中提取商品名稱與價格 """
    lines = text.split("\n")

    # **🔹 提取商品名稱**
    product_name = "未找到商品名稱"
    for i, line in enumerate(lines):
        if "円" in line and i > 0:
            product_name = lines[i - 1].strip()
            break

    # **🔹 提取價格**
    price_jpy = extract_price(text)

    # **🔹 計算台幣報價**
    price_twd = math.ceil(price_jpy * 0.35) if price_jpy > 0 else "N/A"

    return {
        "status": "done",
        "商品名稱": product_name,
        "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy > 0 else "N/A",
        "台幣報價": f"{price_twd} 元" if price_jpy > 0 else "N/A"
    }

def extract_price(text):
    """ 從 OCR 文字中提取價格 """
    price_jpy = 0

    # **匹配 "￥" 之後的數字**
    price_match = re.search(r"￥\s*([\d,]+)", text)
    if price_match:
        price_jpy = int(price_match.group(1).replace(",", ""))

    return price_jpy
