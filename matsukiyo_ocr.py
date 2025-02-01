import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import math
import os

# 設定 Tesseract-OCR 執行檔路徑
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# **🔹 OCR 圖像處理函數**
def process_image(image_path):
    img = Image.open(image_path)

    # **影像預處理**
    img = img.convert("L")  # 灰階處理
    img = img.filter(ImageFilter.SHARPEN)  # 銳化
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # 增強對比度
    img = img.point(lambda x: 0 if x < 150 else 255)  # 二值化

    # **OCR 文字識別**
    raw_text = pytesseract.image_to_string(img, lang="jpn+chi_sim+eng")

    # **列印 OCR 輸出內容，方便除錯**
    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **判斷是否來自 Matsukiyo 網站**
    if "matsukiyo" in raw_text.lower():
        lines = raw_text.split("\n")

        # **🔹 提取商品名稱**
        product_name = "未找到商品名稱"
        for i, line in enumerate(lines):
            if "matsukiyo" in line.lower():
                possible_name = line.split("matsukiyo")[-1].strip()  # 嘗試抓取 `matsukiyo` 後的內容
                if possible_name:
                    product_name = possible_name
                elif i + 1 < len(lines):
                    product_name = lines[i + 1].strip()  # 若 `matsukiyo` 後無內容，則抓取下一行
                break

        # **🔹 提取價格 (優先 "税込")**
        price_jpy = 0
        price_match = re.findall(r"([\d,\.]+)\s*円?\s*\(税込\)", raw_text)  # `2,934円 (税込)`
        if price_match:
            price_jpy = int(price_match[0].replace(",", "").replace(".", ""))
        else:
            # **如果找不到 `税込`，則找 `(税抜)` 並手動計算稅**
            base_price_match = re.findall(r"([\d,\.]+)\s*円?\s*\(税抜\)", raw_text)  # `税抜`
            tax_rate_match = re.findall(r"(\d+)%", raw_text)  # `税率 10%`
            if base_price_match:
                base_price = int(base_price_match[0].replace(",", "").replace(".", ""))
                tax_rate = 0.0
                if tax_rate_match:
                    tax_rate = int(tax_rate_match[0]) / 100  # 轉換 10% -> 0.10
                price_jpy = int(base_price * (1 + tax_rate)) if tax_rate > 0 else base_price  # 計算含稅價格

        # **計算台幣報價**
        price_twd = math.ceil(price_jpy * 0.35)

        # **✅ 回傳 JSON 格式**
        result = {
            "status": "done",
            "商品名稱": product_name,
            "商品日幣價格 (含稅)": f"{price_jpy} 円",
            "台幣報價": f"{price_twd} 元"
        }
        return result

    else:
        return {"status": "error", "message": "這不是 Matsukiyo 網站的資料"}

# **測試執行 (僅當手動運行時執行)**
if __name__ == "__main__":
    image_path = r"C:\Users\Jack\Downloads\99494_0.jpg"
    result = process_image(image_path)
    print(result)
