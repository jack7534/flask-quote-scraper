import requests
from bs4 import BeautifulSoup

# 設定 User-Agent，模擬正常瀏覽器請求
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def search_amazon(keyword):
    """ 爬取 Amazon Japan 商品資訊 """
    search_url = f"https://www.amazon.co.jp/s?k={keyword}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    products = []
    for item in soup.select('.s-result-item')[:5]:  # 取前 5 個商品
        title = item.select_one("h2 a span")
        price = item.select_one(".a-price-whole")
        link = item.select_one("h2 a")

        if title and price and link:
            products.append({
                "名稱": title.text.strip(),
                "價格": f"¥{price.text.strip()}",
                "連結": f"https://www.amazon.co.jp{link['href']}"
            })

    return products


def search_rakuten(keyword):
    """ 爬取 Rakuten 樂天市場 """
    search_url = f"https://search.rakuten.co.jp/search/mall/{keyword}/"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    products = []
    for item in soup.select('.searchresultitem')[:5]:  # 取前 5 個商品
        title = item.select_one(".title")
        price = item.select_one(".important")
        link = item.select_one("a")

        if title and price and link:
            products.append({
                "名稱": title.text.strip(),
                "價格": price.text.strip(),
                "連結": link["href"]
            })

    return products


def search_yahoo_auction(keyword):
    """ 爬取 Yahoo Auctions 拍賣商品 """
    search_url = f"https://auctions.yahoo.co.jp/search/search?p={keyword}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    products = []
    for item in soup.select(".Product")[:5]:  # 取前 5 個商品
        title = item.select_one(".Product__title")
        price = item.select_one(".Product__price")
        link = item.select_one(".Product__title a")

        if title and price and link:
            products.append({
                "名稱": title.text.strip(),
                "價格": price.text.strip(),
                "連結": link["href"]
            })

    return products


def search_mercari(keyword):
    """ 爬取 Mercari 二手市場 """
    search_url = f"https://www.mercari.com/jp/search/?keyword={keyword}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    products = []
    for item in soup.select(".items-box")[:5]:  # 取前 5 個商品
        title = item.select_one(".items-box-name")
        price = item.select_one(".items-box-price")
        link = item.select_one("a")

        if title and price and link:
            products.append({
                "名稱": title.text.strip(),
                "價格": price.text.strip(),
                "連結": f"https://www.mercari.com{link['href']}"
            })

    return products


def search_kakaku(keyword):
    """ 爬取 Kakaku.com 比價網 """
    search_url = f"https://kakaku.com/search_results/{keyword}/"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    products = []
    for item in soup.select(".p-result_item")[:5]:  # 取前 5 個商品
        title = item.select_one(".p-result_item .p-result_item_name")
        price = item.select_one(".p-result_item .p-result_item_price")
        link = item.select_one(".p-result_item a")

        if title and price and link:
            products.append({
                "名稱": title.text.strip(),
                "價格": price.text.strip(),
                "連結": f"https://kakaku.com{link['href']}"
            })

    return products


if __name__ == "__main__":
    keyword = input("🔍 請輸入要搜尋的商品名稱（日文或英文）：")

    print("\n📌 來自 Amazon Japan 的結果：")
    for product in search_amazon(keyword):
        print(f"{product['名稱']} - {product['價格']}")
        print(f"🔗 {product['連結']}\n")

    print("\n📌 來自 Rakuten 樂天市場的結果：")
    for product in search_rakuten(keyword):
        print(f"{product['名稱']} - {product['價格']}")
        print(f"🔗 {product['連結']}\n")

    print("\n📌 來自 Yahoo 拍賣的結果：")
    for product in search_yahoo_auction(keyword):
        print(f"{product['名稱']} - {product['價格']}")
        print(f"🔗 {product['連結']}\n")

    print("\n📌 來自 Mercari 的結果：")
    for product in search_mercari(keyword):
        print(f"{product['名稱']} - {product['價格']}")
        print(f"🔗 {product['連結']}\n")

    print("\n📌 來自 Kakaku.com 比價網的結果：")
    for product in search_kakaku(keyword):
        print(f"{product['名稱']} - {product['價格']}")
        print(f"🔗 {product['連結']}\n")
