import os
from google.cloud import vision
import io
import re
import math

# 設定 Google Cloud API JSON 憑證
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

    print("Google Cloud Vision API 回傳的完整結果：", response)  # ✅ 確保 API 回傳內容

    # **判斷是否來自 Godzilla Store**
    if "godzilla.store" in raw_text.lower() or "ゴジラ・ストア" in raw_text:
        return extract_godzilla_data(raw_text)
    else:
        return {"status": "error", "message": "這不是 Godzilla Store 網站的資料"}

def extract_godzilla_data(text):
    """ 從 Godzilla Store OCR 結果中提取商品名稱與價格 """
    lines = text.split("\n")

    # **提取商品名稱**
    product_name = extract_product_name(lines)

    # **提取價格**
    price_jpy = extract_price(text)  # ✅ 更新為新的 `extract_price()`

    # **計算台幣報價**
    price_twd = math.ceil(price_jpy * 0.35) if price_jpy > 0 else "N/A"

    return {
        "status": "done",
        "商品名稱": product_name,
        "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy > 0 else "N/A",
        "台幣報價": f"{price_twd} 元" if price_jpy > 0 else "N/A"
    }

def extract_product_name(lines):
    """ 從 OCR 結果中提取商品名稱 """
    product_name = "未找到商品名稱"

    for i, line in enumerate(lines):
        if "円" in line and i > 0:
            # 商品名稱通常在價格的上方
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
    """ 從 OCR 文字中提取價格 """
    price_jpy = 0

    # **匹配 "￥" 之後的數字，確保不含千分位逗號**
    price_match = re.search(r"￥\s*([\d,]+)", text)
    if price_match:
        price_jpy = int(price_match.group(1).replace(",", ""))  # ✅ 去除千分位逗號

    return price_jpy
