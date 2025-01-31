import requests
from bs4 import BeautifulSoup
import json
import re
import math
import time

# 設定 User-Agent 避免被擋
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def clean_price(price_text):
    """ 清理價格字串，確保能轉換為 int """
    price_text = re.sub(r"[^\d]", "", price_text.replace("円", "").replace(",", "").strip())
    return int(price_text) if price_text else None

def scrape_amazon_japan(url):
    """ 爬取 Amazon Japan 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.select_one("#productTitle")
        price = soup.select_one(".a-price .a-offscreen")
        image = soup.select_one("#landingImage")

        price_jpy = clean_price(price.text) if price else None
        image_url = image["src"] if image else ""

        if title and price_jpy:
            return {
                "網站": "Amazon Japan",
                "名稱": title.text.strip(),
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),
                "圖片": image_url,
                "連結": url
            }
        return {"錯誤": "無法獲取 Amazon 商品價格"}
    except Exception as e:
        return {"錯誤": f"Amazon 爬取失敗: {str(e)}"}

def scrape_rakuten(url):
    """ 爬取 Rakuten 樂天市場 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.select_one(".item-name") or soup.select_one("h1") or soup.select_one("meta[property='og:title']")
        if title and title.name == "meta":
            title_text = title["content"].strip()
        elif title:
            title_text = title.text.strip()
        else:
            title_text = "無法獲取商品名稱"

        price_jpy = None

        # 嘗試從不同位置獲取價格
        meta_price = soup.select_one("meta[itemprop='price']")
        if meta_price and "content" in meta_price.attrs:
            price_jpy = clean_price(meta_price["content"])

        config_price = soup.select_one("#priceCalculationConfig")
        if not price_jpy and config_price and "data-price" in config_price.attrs:
            price_jpy = clean_price(config_price["data-price"])

        input_price = soup.select_one("input#ratPrice")
        if not price_jpy and input_price and "value" in input_price.attrs:
            price_jpy = clean_price(input_price["value"])

        image = soup.select_one("meta[property='og:image']")
        image_url = image["content"] if image else ""

        if price_jpy:
            return {
                "網站": "Rakuten",
                "名稱": title_text,
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),
                "圖片": image_url,
                "連結": url
            }
        else:
            return {"錯誤": "無法獲取 Rakuten 商品價格"}
    except Exception as e:
        return {"錯誤": f"Rakuten 爬取失敗: {str(e)}"}

def scrape_yahoo_auction(url):
    """ 爬取 Yahoo Auctions 商品資訊 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.select_one(".Product__title") or soup.select_one(".ProductTitle__text")
        bid_price = soup.select_one(".Price__value")
        buy_price = soup.select_one(".Price__now") or soup.select_one(".ProductPrice__value")
        auction_time = soup.select_one(".Auction__endTime")

        price_jpy = None
        price_text = None

        if buy_price:
            price_text = buy_price.text.strip()
        elif bid_price:
            price_text = bid_price.text.strip()

        if price_text:
            price_text = re.sub(r"税\s*\d*\s*円", "", price_text)
            price_jpy = clean_price(price_text)

        image = soup.select_one("meta[property='og:image']")
        image_url = image["content"] if image else ""

        if title and price_jpy:
            return {
                "網站": "Yahoo Auctions",
                "名稱": title.text.strip(),
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),
                "競標結束時間": auction_time.text.strip() if auction_time else "無法取得",
                "圖片": image_url,
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
        print(f"🔗 商品連結：{result['連結']}")
        print(f"🖼 商品圖片：{result['圖片']}\n")
