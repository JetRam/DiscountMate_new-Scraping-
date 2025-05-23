# ======IMPORTS======
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pymongo.mongo_client import MongoClient

# =====HEADERS======
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# ======HELPER FUNCTIONS======
def get_text_or_default(value, default="N/A"):
    return value.text.strip() if value else default

def get_total_pages_balaklava(soup):
    pagination = soup.find('div', class_='mfl-pagination')
    if pagination:
        page_links = pagination.find_all('a')
        page_numbers = [int(link.get_text()) for link in page_links if link.get_text().isdigit()]
        return max(page_numbers, default=1)
    return 1

def setup_mongo():
    client = MongoClient("mongodb+srv://discountmate_read_and_write:discountmate@discountmatecluster.u80y7ta.mongodb.net/?retryWrites=true&w=majority&appName=DiscountMateCluster")
    db = client['ScrappedData']
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    collection = db[f"{timestamp}_Foodland"]
    return collection

# ======SCRAPER FUNCTION======
def scrape_foodland():
    url = "https://foodlandbalaklava.com.au/search?page=1"
    page = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(page.text, 'html.parser')
    total_pages = get_total_pages_balaklava(soup)
    print(f"Total Pages: {total_pages} Balaklava")

    results = []

    for current_page in range(1, total_pages + 1):
        print(f"Scraping Page: {current_page}")
        url = f"https://foodlandbalaklava.com.au/search?page={current_page}"
        page = requests.get(url, headers=headers, timeout=10)

        if page.status_code == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            products = soup.find_all('div', class_="TalkerGrid__Item")

            for product in products:
                data = {
                    "product_code": product.get('data-product-code', 'N/A'),
                    "category": get_text_or_default(product.find('div', class_='talker__breadcrumb'), 'N/A'),
                    "item_name": get_text_or_default(product.find('div', class_='talker__name talker__section').find('span')),
                    "item_price": get_text_or_default(product.find('span', class_='talker__prices__was'), 'N/A'),
                    "best_price": get_text_or_default(product.find('strong', class_='price__sell'), 'N/A'),
                    "unit_price": get_text_or_default(product.find('span', class_='talker__prices__comparison--UnitPrice'), 'N/A'),
                    "special_text": get_text_or_default(product.find('div', class_='talker__promo__special-text'), 'N/A'),
                    "promo_text": get_text_or_default(product.find('span', class_='talker__promo__text'), 'N/A'),
                    "link": "https://foodlandbalaklava.com.au" + product.find('a').get('href', '')
                }

                results.append(data)

    if results:
        collection = setup_mongo()
        collection.insert_many(results)
        print("Scraping completed successfully!")
    else:
        print("No products found on Balaklava site.")

# ======MAIN=====
if __name__ == '__main__':
    print("Starting Foodland Balaklava scrape...")
    scrape_foodland()
    print("Scraping completed successfully!")
