import os
import io
import re
import math
import json
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import vision
from dotenv import load_dotenv

# **載入環境變數**
load_dotenv()

# **初始化 Flask**
app = Flask(__name__)
CORS(app)

# **設定 Google Cloud API JSON 憑證**
cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")  # 環境變數應該存放 JSON 字符串
cred_path = "/opt/render/project/.creds/google_api.json"  # 指定安全存放位置

if cred_json:
    os.makedirs(os.path.dirname(cred_path), exist_ok=True)
    with open(cred_path, "w") as f:
        f.write(cred_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
else:
    raise ValueError("❌ Google API Key 未設置，請確認環境變數")

# **讀取 OpenAI API Key**
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("❌ OpenAI API Key 未設置，請確認環境變數")


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

    請從這些文本中提取：
    1. 商品名稱
    2. 商品價格（日幣）
    3. 若無價格，則標示 "N/A"

    回應 JSON 格式如下：
    {{"商品名稱": "...", "商品日幣價格 (含稅)": "...", "台幣報價": "..."}}
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

        # **轉換台幣報價**
        if price_jpy != "N/A":
            price_jpy = int(price_jpy.replace(",", ""))  # 去除千分位逗號
            price_twd = f"{math.ceil(price_jpy * 0.35)} 元"
        else:
            price_twd = "N/A"

        return {
            "status": "done",
            "商品名稱": ai_data.get("商品名稱", "N/A"),
            "商品日幣價格 (含稅)": f"{price_jpy} 円" if price_jpy != "N/A" else "N/A",
            "台幣報價": price_twd
        }
    except Exception as e:
        return {"status": "error", "message": f"OpenAI 解析失敗: {str(e)}"}


# **Render 需要這行來啟動 Flask**
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
