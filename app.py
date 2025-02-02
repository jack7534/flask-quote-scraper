# **ai判讀版**
import os
import io
import json
import math
import openai
import sys
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

# **讀取 OpenAI API Key**
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("❌ OPENAI_API_KEY 環境變數未設置", file=sys.stderr)
    raise ValueError("❌ OpenAI API Key 未設置")

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
        print(f"❌ 伺服器錯誤: {str(e)}", file=sys.stderr)
        return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500

def process_image(image_file):
    """使用 Google Cloud Vision API 進行 OCR 並用 OpenAI 解析數據"""
    client = vision.ImageAnnotatorClient()

    # **等待 1 秒確保完整讀取**
    time.sleep(1)

    # **OCR 讀取**
    content = io.BytesIO(image_file.read())
    image = vision.Image(content=content.getvalue())
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description  # 取得 OCR 解析的文字
    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **使用 OpenAI 分析 OCR 結果**
    extracted_data = extract_with_openai(raw_text)

    return extracted_data

def extract_with_openai(text):
    """使用 OpenAI 來解析 OCR 結果並提取關鍵資訊"""
    prompt = f"""
    以下是從圖片 OCR 解析出的日文文本：
    {text}

    你的任務是分析這段文字並提取：
    1. 商品名稱
    2. 商品價格（日幣，未稅）
    3. 商品價格（日幣，含稅），如果沒有則填 "N/A"
    4. 台幣報價（台幣 = 日幣價格 * 0.35，結果應該無條件進位）

    **請忽略數字中的 `,` 和 `.`，確保能正確讀取價格。**

    **回應 JSON 格式如下：**
    {{
        "商品名稱": "...",
        "商品日幣價格 (未稅)": "...",
        "商品日幣價格 (含稅)": "...",
        "台幣報價": "..."
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "你是一個專業的商品資料解析助手"},
                  {"role": "user", "content": prompt}]
    )

    ai_result = response["choices"][0]["message"]["content"]

    # **確保 JSON 結構正確**
    try:
        ai_data = json.loads(ai_result)  # ✅ 使用 json.loads() 解析 JSON
        price_jpy = ai_data.get("商品日幣價格 (含稅)", "N/A")

        # **修正價格格式**：移除 `,` 和 `.`，確保數字正確
        price_jpy = int(price_jpy.replace(",", "").replace(".", "")) if price_jpy not in ["N/A", ""] else "N/A"

        # **台幣報價換算**：日幣 * 0.35 **無條件進位**
        price_twd = math.ceil(price_jpy * 0.35) if price_jpy != "N/A" else "N/A"

        return {
            "status": "done",
            "商品名稱": ai_data.get("商品名稱", "N/A"),
            "商品日幣價格 (未稅)": ai_data.get("商品日幣價格 (未稅)", "N/A"),
            "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy != "N/A" else "N/A",
            "台幣報價": f"{price_twd} 元" if price_twd != "N/A" else "N/A"
        }
    except Exception as e:
        return {"status": "error", "message": f"OpenAI 解析失敗: {str(e)}"}

# **Render 需要這行來啟動 Flask**
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # 預設為 10000，Render 會提供 PORT
    app.run(host="0.0.0.0", port=port)
