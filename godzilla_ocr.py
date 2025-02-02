import os
import io
import openai
from google.cloud import vision

# ✅ 設定 OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def process_image(image_path):
    """ 使用 Google Cloud Vision API 進行 OCR 並用 GPT 解析數據 """
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description  # 取得 OCR 解析的文字

    # ✅ 用 GPT-4 解析商品名稱、日圓價格、台幣價格
    product_info = analyze_text_with_gpt(raw_text)

    return {
        "status": "done",
        "OCR 文字": raw_text,
        "GPT 判讀結果": product_info
    }

def analyze_text_with_gpt(text):
    """ 使用 GPT API 來分析 OCR 讀取的文字，提取商品名稱與價格 """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一個專業的價格分析助手，請從以下文字中提取商品名稱、日圓價格（日幣價格 或 含稅價格）、台幣報價。"},
            {"role": "user", "content": text}
        ]
    )
    return response["choices"][0]["message"]["content"]
