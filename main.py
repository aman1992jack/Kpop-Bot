import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")

def fetch_and_send():
    if not discord_webhook_url:
        print("找不到 Discord Webhook 網址")
        return

    # 1. 爬蟲去抓網路資料
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:10]  # 抓前 10 則來篩選
        
        report = "📢 **【K-POP 台灣最新情報推播 (純淨直連版)】**\n\n"
        has_news = False
        
        # 2. 純程式碼過濾：找出有重點關鍵字的標題
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            
            # 只要標題有這些字，就認定是重要情報
            if any(keyword in title for keyword in ["演唱會", "搶票", "售票", "來台", "開賣"]):
                report += f"🔥 **{title}**\n🔗 {link}\n\n"
                has_news = True
                
        if not has_news:
            report += "🤖 目前網路上尚未更新重要的 K-POP 活動資訊。"
            
        # 3. 直接發送到 Discord
        requests.post(discord_webhook_url, json={"content": report})
        
    except Exception as e:
        error_msg = f"⚠️ 機器人發生錯誤：{str(e)}"
        requests.post(discord_webhook_url, json={"content": error_msg})

if __name__ == "__main__":
    fetch_and_send()
