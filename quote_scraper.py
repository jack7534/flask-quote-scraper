import requests
from bs4 import BeautifulSoup
import json
import re
import math  # 🔹 引入 math 模組來處理無條件進位

# 設定 User-Agent 避免被擋
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
        return None
    except Exception as e:
        return {"錯誤": f"Amazon 爬取失敗: {str(e)}"}

def scrape_rakuten(url):
    """ 爬取 Rakuten 樂天市場 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        # **1️⃣ 獲取商品名稱**
        title = soup.select_one(".item-name") or soup.select_one("h1") or soup.select_one("meta[property='og:title']")
        if title and title.name == "meta":
            title_text = title["content"].strip()
        elif title:
            title_text = title.text.strip()
        else:
            title_text = "無法獲取商品名稱"

        # **2️⃣ 抓取價格**
        price_jpy = None

        # **從 `<meta itemprop="price">` 內獲取價格**
        meta_element = soup.select_one("meta[itemprop='price']")
        if meta_element and "content" in meta_element.attrs:
            price_jpy = int(meta_element["content"])

        # **嘗試從 `#priceCalculationConfig` 抓 `data-price`**
        if not price_jpy:
            config_element = soup.select_one("#priceCalculationConfig")
            if config_element and "data-price" in config_element.attrs:
                price_jpy = int(config_element["data-price"])

        # **嘗試從 `<input id="ratPrice">` 內抓價格**
        if not price_jpy:
            input_element = soup.select_one("input#ratPrice")
            if input_element and "value" in input_element.attrs:
                price_jpy = int(input_element["value"])

        # **Debug: 打印找到的價格與名稱**
        print(f"💡 樂天價格解析：價格={price_jpy}")
        print(f"🛒 樂天商品名稱：{title_text}")

        # **回傳結果**
        if price_jpy:
            return {
                "網站": "Rakuten",
                "名稱": title_text,
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),  # 🔹 無條件進位
                "連結": url
            }
        else:
            return {"錯誤": "無法獲取樂天市場價格"}

    except Exception as e:
        return {"錯誤": f"Rakuten 爬取失敗: {str(e)}"}

def scrape_yahoo_auction(url):
    """ 爬取 Yahoo Auctions 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        # 抓取商品名稱
        title = soup.select_one(".Product__title") or soup.select_one(".ProductTitle__text")

        # 嘗試獲取競標價或直購價
        bid_price = soup.select_one(".Price__value")  # 競標價
        buy_price = soup.select_one(".Price__now") or soup.select_one(".ProductPrice__value")  # 直購價
        auction_time = soup.select_one(".Auction__endTime")  # 競標結束時間

        price_jpy = None
        price_text = None

        # **嘗試抓取價格，優先直購價**
        if buy_price:
            price_text = buy_price.text.strip()
        elif bid_price:
            price_text = bid_price.text.strip()

        # **確保數值不被 `税 0 円` 影響**
        if price_text:
            price_text = re.sub(r"税\s*\d*\s*円", "", price_text)  # 移除税務訊息
            price_jpy = int(re.sub(r"[^\d]", "", price_text))  # 只保留數字

        # **結果整理**
        if title and price_jpy:
            return {
                "網站": "Yahoo Auctions",
                "名稱": title.text.strip(),
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),  # 🔹 無條件進位
                "競標結束時間": auction_time.text.strip() if auction_time else "無法取得",
                "連結": url
            }
        return {"錯誤": "無法獲取 Yahoo Auctions 價格"}

    except Exception as e:
        return {"錯誤": f"Yahoo Auctions 爬取失敗: {str(e)}"}

def get_quotation(url):
    """ 根據提供的網址，選擇對應的爬蟲 """
    if "amazon.co.jp" in url:
        return scrape_amazon_japan(url)
    elif "rakuten.co.jp" in url:
        return scrape_rakuten(url)
    elif "auctions.yahoo.co.jp" in url:
        return scrape_yahoo_auction(url)
    else:
        return {"錯誤": "目前不支援此網站"}

if __name__ == "__main__":
    print("\n📌 **請先前往以下網站搜尋商品，然後複製商品網址貼上查詢報價：**")
    print("🔹 [Amazon Japan](https://www.amazon.co.jp/)")
    print("🔹 [Rakuten 樂天市場](https://search.rakuten.co.jp/)")
    print("🔹 [Yahoo Auctions 雅虎拍賣](https://auctions.yahoo.co.jp/)\n")

    url = input("🔍 請輸入商品網址：")
    result = get_quotation(url)

    if result is None:
        print("❌ 無法獲取該商品的資訊，請確認網址是否正確")
    elif "錯誤" in result:
        print(f"❌ {result['錯誤']}")
    else:
        print("\n📌 報價結果：")
        print(f"🛒 網站：{result['網站']}")
        print(f"📌 商品名稱：{result['名稱']}")
        print(f"💴 原價（日幣）：¥{result['日幣價格']}")
        print(f"💰 台幣報價：NT$ {result['台幣報價']}")
        if "競標結束時間" in result:
            print(f"⏳ 競標結束時間：{result['競標結束時間']}")
        print(f"🔗 商品連結：{result['連結']}\n")
