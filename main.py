import requests
from bs4 import BeautifulSoup
import os

# 我們改用「環境變數」來保護你的 Webhook，這比較安全
my_webhook_url = os.getenv("DISCORD_WEBHOOK")

def fetch_kpop_taiwan():
    search_url = "https://news.google.com/rss/search?q=KPOP+台灣+(開賣+OR+演唱會+OR+簽售+OR+聯名+OR+快閃店)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')
        for item in items[:5]:
            title = item.title.text
            link = item.link.text
            message = f"🔥 **【K-POP 台灣活動快報】**\n📌 **標題：** {title}\n🔗 **連結：** {link}\n------------------------------------"
            requests.post(my_webhook_url, json={"content": message})
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_kpop_taiwan()
