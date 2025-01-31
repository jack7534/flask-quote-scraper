import requests
from bs4 import BeautifulSoup
import json
import re
import math  # 🔹 引入 math 模組來處理無條件進位

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def clean_price(price_text):
    """ 清理價格字串，確保能轉換為 int """
    price_text = price_text.replace("円", "").replace(",", "").replace("(税込)", "").replace("(税 0)", "").strip()
    return int(re.sub(r"[^\d]", "", price_text))  # 只保留數字部分，移除日文字

def scrape_amazon_japan(url):
    """ 爬取 Amazon Japan 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.select_one("#productTitle")
        price = soup.select_one(".a-price .a-offscreen")

        if title and price:
            price_jpy = clean_price(price.text)
            return {
                "網站": "Amazon Japan",
                "名稱": title.text.strip(),
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),  # 🔹 無條件進位
                "連結": url
            }
        return {"錯誤": "無法獲取 Amazon 商品價格"}
    except Exception as e:
        return {"錯誤": f"Amazon 爬取失敗: {str(e)}"}

def get_quotation(url):
    """ 根據提供的網址，選擇對應的爬蟲 """
    if "amazon.co.jp" in url:
        return scrape_amazon_japan(url)
    else:
        return {"錯誤": "目前不支援此網站"}

if __name__ == "__main__":
    # 🚨 ❌ 這一段刪除，因為 API 會調用這個函數，而不是透過 input()
    # url = input("🔍 請輸入商品網址：")
    # result = get_quotation(url)
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    pass  # 保留這個作為空白執行
