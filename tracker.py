import requests
import time
import os
import json

NTFY_TOPIC = "pokewatch-lofts"
CHECK_INTERVAL = 20  # seconds

PRODUCTS_FILE = "products.json"

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE) as f:
        return json.load(f)

def detect_stock(html):
    lower = html.lower()
    out_signals = ["sold out", "out of stock", "currently unavailable",
                   "notify me when available", '"availability":"outofstock"',
                   "outofstock"]
    for s in out_signals:
        if s in lower:
            return False
    in_signals = ["add to bag", "add to basket", "add to cart",
                  '"availability":"instock"', "instock"]
    for s in in_signals:
        if s in lower:
            return True
    return False

def check_product(product):
    url = product["url"]
    name = product["name"]
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        return detect_stock(res.text)
    except Exception as e:
        print(f"Error checking {name}: {e}")
        return None

def send_notification(name, url):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            headers={
                "Title": f"IN STOCK: {name}",
                "Priority": "urgent",
                "Tags": "rotating_light",
                "Click": url,
            },
            data=f"Go buy it now! Tap to open the product page.",
            timeout=10
        )
        print(f"Notification sent for {name}")
    except Exception as e:
        print(f"Failed to send notification: {e}")

def main():
    print("PokéWatch started. Checking every 60 seconds...")
    last_status = {}

    while True:
        products = load_products()
        if not products:
            print("No products in products.json yet. Waiting...")
        for product in products:
            name = product["name"]
            url = product["url"]
            in_stock = check_product(product)
            if in_stock is None:
                print(f"[ERROR] {name}")
                continue
            prev = last_status.get(url)
            last_status[url] = in_stock
            if in_stock:
                print(f"[IN STOCK] {name}")
                if prev is not True:
                    send_notification(name, url)
            else:
                print(f"[OUT OF STOCK] {name}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
