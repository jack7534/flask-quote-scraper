import requests
import json


def search_pchome(keyword):
    """ 爬取 PChome 商品 API """

    search_url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={keyword}&page=1&sort=rnk/dc"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        print("❌ 無法取得 PChome 資料，請檢查網路連線")
        return []

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("❌ 無法解析 PChome API 回應")
        return []

    if "prods" not in data or not data["prods"]:
        print("❌ 找不到商品")
        return []

    products = []
    for item in data["prods"][:10]:  # 取前 10 個商品
        name = item["name"]
        price = item["price"]
        link = f"https://24h.pchome.com.tw/prod/{item['Id']}"

        products.append({
            "名稱": name,
            "價格": f"NT$ {price}",
            "連結": link
        })

    return products


if __name__ == "__main__":
    keyword = input("🔍 請輸入要搜尋的商品名稱：")
    results = search_pchome(keyword)

    if not results:
        print("❌ 找不到商品")
    else:
        print("\n📌 PChome 商品搜尋結果：")
        for idx, product in enumerate(results):
            print(f"{idx + 1}. {product['名稱']} - {product['價格']}")
            print(f"🔗 {product['連結']}\n")
