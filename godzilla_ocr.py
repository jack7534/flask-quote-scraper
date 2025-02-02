import os
import io
import re
import math
from google.cloud import vision

# ✅ 設定 Google Cloud API JSON 憑證
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcloud-key.json"

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

    # **提取商品名稱**
    lines = raw_text.split("\n")
    product_name = lines[0] if len(lines) > 0 else "未找到商品名稱"

    # **提取價格**
    price_jpy = 0
    price_match = re.search(r"￥\s*([\d,]+)", raw_text)
    if price_match:
        price_jpy = int(price_match.group(1).replace(",", ""))  # ✅ 去除千分位逗號

    # **計算台幣報價**
    price_twd = math.ceil(price_jpy * 0.35) if price_jpy > 0 else "N/A"

    return {
        "status": "done",
        "商品名稱": product_name,
        "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy > 0 else "N/A",
        "台幣報價": f"{price_twd} 元" if price_jpy > 0 else "N/A"
    }
