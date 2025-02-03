#傳遞 OCR 結果給 OpenAI GPT 來提取商品名稱 & 價格
import os
import io
import json
import math
import openai
import sys
import time
import re  # ✅ 新增正則表達式來提取數據
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
cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # 讀取 JSON 內容
cred_path = "/opt/render/project/.creds/google_api.json"  # 指定存放路徑

if not cred_json:
    print("\u274c GOOGLE_APPLICATION_CREDENTIALS 環境變數未設置", file=sys.stderr)
    raise ValueError("\u274c 找不到 Google Cloud 憑證，請確認 GOOGLE_APPLICATION_CREDENTIALS 環境變數")

# **確保 JSON 格式正確**
try:
    json.loads(cred_json)
except json.JSONDecodeError as e:
    print(f"\u274c GOOGLE_APPLICATION_CREDENTIALS 格式錯誤: {e}", file=sys.stderr)
    raise ValueError("\u274c GOOGLE_APPLICATION_CREDENTIALS 格式錯誤，請確認環境變數內容")

# **寫入憑證 JSON 檔案**
os.makedirs(os.path.dirname(cred_path), exist_ok=True)
with open(cred_path, "w") as f:
    f.write(cred_json)

# **設置 GOOGLE_APPLICATION_CREDENTIALS 讓 Google Cloud SDK 能讀取**
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
print("\u2705 Google Cloud 憑證已設置", file=sys.stderr)

# **讀取 OpenAI API Key**
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("\u274c OPENAI_API_KEY 環境變數未設置", file=sys.stderr)
    raise ValueError("\u274c OpenAI API Key 未設置，請確認環境變數 OPENAI_API_KEY")


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

    extracted_data = extract_with_openai(raw_text)

    extracted_data["ocr_text"] = raw_text  # ✅ 回傳完整的 OCR 文字給前端

    return extracted_data


def extract_with_openai(text):
    """使用 OpenAI 來解析 OCR 結果並提取關鍵資訊"""
    prompt = f"""
    以下是從圖片 OCR 解析出的日文文本：
    {text}

    請從這些文本中提取：
    1. 商品名稱
    2. 商品價格（日幣，含稅，如果沒有則回傳 "N/A"）
    3. 台幣報價（台幣約為日幣價格 * 0.35，結果應該無條件進位）

    回應 JSON 格式如下：
    {{"商品名稱": "...", "商品日幣價格 (含稅)": "...", "台幣報價": "..."}}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "你是一個專業的商品資料解析助手"},
                      {"role": "user", "content": prompt}]
        )

        ai_result = response["choices"][0]["message"]["content"]
        ai_data = json.loads(ai_result)

        price_jpy = ai_data.get("商品日幣價格 (含稅)", "N/A")
        price_jpy = int(price_jpy.replace(",", "")) if price_jpy != "N/A" else "N/A"
        price_twd = math.ceil(price_jpy * 0.35) if price_jpy != "N/A" else "N/A"

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
