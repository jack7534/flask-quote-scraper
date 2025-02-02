import os
import io
import json
import math
import sys
import time  # ✅ 增加等待機制
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import vision
from dotenv import load_dotenv
import openai  # ✅ 確保 OpenAI 正確使用

# **載入環境變數**
load_dotenv()

# **初始化 Flask**
app = Flask(__name__)
CORS(app)

# **讀取 OpenAI API Key**
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("❌ OPENAI_API_KEY 環境變數未設置", file=sys.stderr)
    raise ValueError("❌ OpenAI API Key 未設置，請確認環境變數 `OPENAI_API_KEY`")


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
    """使用 Google Cloud Vision API 進行 OCR，並等待確保獲取完整數據"""
    client = vision.ImageAnnotatorClient()

    retry_attempts = 3  # ✅ OCR 最高重試次數
    for attempt in range(retry_attempts):
        try:
            print(f"🟡 嘗試 OCR 分析，第 {attempt + 1} 次...", file=sys.stderr)

            # **確保圖片格式正確**
            content = io.BytesIO(image_file.read())
            image = vision.Image(content=content.getvalue())

            response = client.text_detection(image=image)
            texts = response.text_annotations

            if not texts:
                print(f"⚠️ 第 {attempt + 1} 次 OCR 無法識別文字，等待 1 秒後重試...", file=sys.stderr)
                time.sleep(1)
                continue  # 重試

            raw_text = texts[0].description  # 取得 OCR 解析的文字
            print("\n🔍 OCR 解析結果：")
            print(raw_text)

            # **使用 OpenAI 分析 OCR 結果**
            return extract_with_openai(raw_text)

        except Exception as e:
            print(f"⚠️ OCR 解析失敗，第 {attempt + 1} 次: {e}", file=sys.stderr)
            time.sleep(1)  # **等待 1 秒後重試**

    return {"status": "error", "message": "OCR 解析失敗，請稍後再試"}


def extract_with_openai(text):
    """使用 OpenAI 來解析 OCR 結果並提取關鍵資訊"""
    prompt = f"""
    以下是從圖片 OCR 解析出的日文文本：
    {text}

    請從這些文本中提取：
    1. 商品名稱
    2. 商品價格（日幣，未稅），如果有含稅價格，則不顯示未稅價格
    3. 商品價格（日幣，含稅），如果沒有則回傳 "N/A"
    4. 台幣報價（台幣約為日幣價格 * 0.35，結果應該無條件進位）

    **請忽略數字中的 `,` 和 `.`，確保能正確讀取價格。**

    **輸出 JSON 格式如下**：
    {{
        "商品名稱": "...",
        "商品日幣價格 (含稅)": "...",
        "台幣報價": "..."
    }}
    """

    retry_attempts = 3  # ✅ OpenAI API 最高重試次數
    for attempt in range(retry_attempts):
        try:
            print(f"🟡 嘗試與 OpenAI 交互，第 {attempt + 1} 次...", file=sys.stderr)

            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的商品資料解析助手"},
                    {"role": "user", "content": prompt}
                ]
            )

            ai_result = response["choices"][0]["message"]["content"]

            # **確保 JSON 結構正確**
            ai_data = json.loads(ai_result)

            # **修正價格格式**：移除 `,` 和 `.` 以確保數字正確
            price_jpy = ai_data.get("商品日幣價格 (含稅)", "N/A")
            if price_jpy not in ["N/A", ""]:
                price_jpy = int("".join(filter(str.isdigit, price_jpy)))  # 只保留數字

            # **台幣報價換算**：日幣 * 0.35 **無條件進位**
            price_twd = math.ceil(price_jpy * 0.35) if isinstance(price_jpy, int) else "N/A"

            print("✅ OpenAI 分析完成！", file=sys.stderr)

            return {
                "status": "done",
                "商品名稱": ai_data.get("商品名稱", "N/A"),
                "商品日幣價格 (含稅)": f"{price_jpy} 円" if isinstance(price_jpy, int) else "N/A",
                "台幣報價": f"{price_twd} 元" if isinstance(price_twd, int) else "N/A"
            }

        except json.JSONDecodeError as e:
            print(f"⚠️ OpenAI 解析失敗，第 {attempt + 1} 次: {e}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ OpenAI API 呼叫錯誤，第 {attempt + 1} 次: {e}", file=sys.stderr)

        # **等待 1 秒後重試**
        time.sleep(1)

    return {"status": "error", "message": "OpenAI 解析失敗，請稍後再試"}


# **Render 需要這行來啟動 Flask**
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # 預設為 10000，Render 會提供 PORT
    app.run(host="0.0.0.0", port=port)
