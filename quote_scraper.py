import requests
from bs4 import BeautifulSoup
import json
import re
import math
import time
import random
import cloudscraper  # 需要安裝 `pip install cloudscraper`

# 設定 User-Agent 避免被擋
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# **全局定義 session**
session = requests.Session()

def clean_price(price_text):
    """ 清理價格字串，確保能轉換為 int """
    price_text = re.sub(r"[^\d]", "", price_text.replace("円", "").replace(",", "").strip())
    return int(price_text) if price_text else None

### **這裡改回 01 版本的 Amazon Japan**
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

### **以下的 Rakuten、Yahoo、Bic Camera 都完全不動**
def scrape_rakuten(url):
    """ 爬取 Rakuten 樂天市場 商品資訊 """
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.select_one(".item-name") or soup.select_one("h1") or soup.select_one("meta[property='og:title']")
        title_text = title["content"].strip() if title and title.name == "meta" else title.text.strip() if title else "無法獲取商品名稱"

        price_meta = soup.select_one("meta[itemprop='price']")
        price_jpy = clean_price(price_meta["content"]) if price_meta else None

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


def scrape_bic_camera(url):
    """ 爬取 Bic Camera 商品資訊 """
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        session = requests.Session()

        # 先訪問首頁，取得 Cookies
        session.get("https://www.biccamera.com/", headers=HEADERS, timeout=10)

        # 發送請求
        response = scraper.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            return {"錯誤": f"Bic Camera 請求失敗，狀態碼: {response.status_code}"}

        soup = BeautifulSoup(response.text, "lxml")

        # 商品名稱
        title = soup.select_one("h1")
        title_text = title.text.strip() if title else "無法獲取商品名稱"

        # 價格
        price_meta = soup.select_one('meta[itemprop="price"]')
        price_jpy = clean_price(price_meta["content"]) if price_meta else None

        # 圖片
        image = soup.select_one("meta[property='og:image']")
        image_url = image["content"] if image else ""

        if title_text and price_jpy:
            return {
                "網站": "Bic Camera",
                "名稱": title_text,
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),
                "圖片": image_url,
                "連結": url
            }
        return {"錯誤": "無法獲取 Bic Camera 商品價格"}
    except Exception as e:
        return {"錯誤": f"Bic Camera 爬取失敗: {str(e)}"}


### **新增 Matsukiyo Cocokara**
def scrape_matsukiyo(url):
    """ 爬取 Matsukiyo Cocokara（松本清）商品資訊 """
    try:
        # 使用 cloudscraper 繞過防爬
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        scraper.get("https://www.matsukiyococokara-online.com/", headers=HEADERS)  # 先訪問首頁取得 cookies
        response = scraper.get(url, headers=HEADERS, timeout=30, allow_redirects=True)

        # 如果狀態碼不是 200，則返回錯誤
        if response.status_code != 200:
            return {"錯誤": f"Matsukiyo 請求失敗，狀態碼: {response.status_code}"}

        soup = BeautifulSoup(response.text, "lxml")

        # 商品名稱
        title = soup.select_one("h1")
        title_text = title.text.strip() if title else "無法獲取商品名稱"

        # 嘗試從 <div class='p-productdetail__price'> 取得價格
        price_meta = soup.select_one("div.p-productdetail__price big")
        price_jpy = clean_price(price_meta.text) if price_meta else None

        # 圖片
        image = soup.select_one("meta[property='og:image']")
        image_url = image["content"] if image else ""

        if title_text and price_jpy:
            return {
                "網站": "Matsukiyo Cocokara",
                "名稱": title_text,
                "日幣價格": price_jpy,
                "台幣報價": math.ceil(price_jpy * 0.35),
                "圖片": image_url,
                "連結": url
            }
        return {"錯誤": "無法獲取 Matsukiyo 商品價格"}
    except Exception as e:
        return {"錯誤": f"Matsukiyo 爬取失敗: {str(e)}"}

def get_quotation(url):
    """ 根據提供的網址，選擇對應的爬蟲 """
    if "amazon.co.jp" in url:
        return scrape_amazon_japan(url)
    elif "rakuten.co.jp" in url:
        return scrape_rakuten(url)
    elif "auctions.yahoo.co.jp" in url:
        return scrape_yahoo_auction(url)
    elif "biccamera.com" in url:
        return scrape_bic_camera(url)
    elif "matsukiyococokara-online.com" in url:
        return scrape_matsukiyo(url)
    else:
        return {"錯誤": "目前不支援此網站"}

if __name__ == "__main__":
    url = input("🔍 請輸入商品網址：")
    result = get_quotation(url)
    print("\n📌 報價結果：", json.dumps(result, indent=4, ensure_ascii=False))
