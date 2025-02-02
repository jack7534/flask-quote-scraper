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


    # **判斷是否來自 Matsukiyo 網站**
    if "matsukiyo" in raw_text.lower():
        lines = raw_text.split("\n")

        # **提取商品名稱**
        product_name = "未找到商品名稱"
        for i, line in enumerate(lines):
            if "matsukiyo" in line.lower():
                possible_name = line.split("matsukiyo")[-1].strip()
                if possible_name:
                    product_name = possible_name
                elif i + 1 < len(lines):
                    product_name = lines[i + 1].strip()
                break

        # **提取價格**
        price_jpy = 0
        price_match = re.findall(r"([\d,\.]+)\s*円?\s*\(税込\)", raw_text)
        if price_match:
            price_jpy = int(price_match[0].replace(",", "").replace(".", ""))
        else:
            base_price_match = re.findall(r"([\d,\.]+)\s*円?\s*\(税抜\)", raw_text)
            tax_rate_match = re.findall(r"(\d+)%", raw_text)
            if base_price_match:
                base_price = int(base_price_match[0].replace(",", "").replace(".", ""))
                tax_rate = 0.0
                if tax_rate_match:
                    tax_rate = int(tax_rate_match[0]) / 100
                price_jpy = int(base_price * (1 + tax_rate)) if tax_rate > 0 else base_price

        price_twd = math.ceil(price_jpy * 0.35)

        return {
            "status": "done",
            "商品名稱": product_name,
            "商品日幣價格 (含稅)": f"{price_jpy} 円",
            "台幣報價": f"{price_twd} 元"
        }

    else:
        return {"status": "error", "message": "這不是 Matsukiyo 網站的資料"}
