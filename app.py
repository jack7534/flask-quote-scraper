#GPT說可以正常運作不知道真的假的
import os
import io
import json
import math
import openai
import sys
import time
import re
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
    print("\u274c GOOGLE_APPLICATION_CREDENTIALS 環境變數未設置", file=sys.stderr)
    raise ValueError("\u274c 找不到 Google Cloud 憑證")

# **寫入憑證 JSON 檔案**
os.makedirs(os.path.dirname(cred_path), exist_ok=True)
with open(cred_path, "w") as f:
    f.write(cred_json)

# **設置 GOOGLE_APPLICATION_CREDENTIALS**
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
print("\u2705 Google Cloud 憑證已設置", file=sys.stderr)

# **讀取 OpenAI API Key**
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("\u274c OPENAI_API_KEY 環境變數未設置", file=sys.stderr)
    raise ValueError("\u274c OpenAI API Key 未設置")

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
        print(f"\u274c 伺服器錯誤: {str(e)}", file=sys.stderr)
        return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500

def process_image(image_file):
    """使用 Google Cloud Vision API 進行 OCR"""
    client = vision.ImageAnnotatorClient()

    content = image_file.stream.read()
    if not content:
        return {"status": "error", "message": "圖片讀取失敗"}

    image = vision.Image(content=content)
    time.sleep(1)

    response = client.text_detection(image=image)

    if response.error.message:
        return {"status": "error", "message": f"Google Vision API 錯誤: {response.error.message}"}

    texts = response.text_annotations
    if not texts:
        return {"status": "error", "message": "OCR 無法識別文字"}

    raw_text = texts[0].description
    print("\n🔍 OCR 解析結果：")
    print(raw_text)

    # **使用 OpenAI GPT 解析**
    extracted_data = extract_with_openai(raw_text)
    extracted_data["ocr_text"] = raw_text  # ✅ 確保回傳 OCR 文字

    return extracted_data

def extract_with_openai(text):
    """使用 OpenAI 解析 OCR 結果"""
    prompt = f"""
    以下是從圖片 OCR 解析出的日文文本：
    {text}

    請提取：
    1. 商品名稱
    2. 商品價格（日幣，未稅）
    3. 商品價格（日幣，含稅，若無則回傳 "N/A"）
    4. 台幣報價（無條件進位：日幣價格 * 0.35）

    回應 JSON 格式：
    {{"商品名稱": "...", "商品日幣價格 (含稅)": "...", "台幣報價": "..."}}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "你是一個商品價格解析助手"},
                      {"role": "user", "content": prompt}]
        )

        ai_result = response["choices"][0]["message"]["content"]
        ai_data = json.loads(ai_result)

        price_jpy = ai_data.get("商品日幣價格 (含稅)", "N/A")
        if price_jpy != "N/A":
            price_jpy = int(price_jpy.replace(",", ""))
            price_twd = math.ceil(price_jpy * 0.35)
        else:
            price_twd = "N/A"

        return {
            "status": "done",
            "商品名稱": ai_data.get("商品名稱", "N/A"),
            "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy != "N/A" else "N/A",
            "台幣報價": f"{price_twd} 元" if price_twd != "N/A" else "N/A"
        }
    except Exception as e:
        return {"status": "error", "message": f"OpenAI 解析失敗: {str(e)}"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
