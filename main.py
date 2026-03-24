import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(text):
    prompt = f"你是一個 K-POP 專家。請分析這則標題：『{text}』。提取資訊並整理成：『藝人：[名字] | 活動：[名稱] | 時間：[日期地點] | 售票：[日期平台]』。如果標題太模糊，請回傳『跳過』。"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "跳過"

def fetch_kpop():
    # 換成更穩定的 Google News 來源，並增加關鍵字精準度
    search_url = "https://news.google.com/rss/search?q=KPOP+台灣+(開賣+OR+演唱會+OR+簽售+OR+聯名)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    print(f"正在連線到: {search_url}")
    
    try:
        response = requests.get(search_url, timeout=15)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')
        
        count = 0
        for item in items[:5]:
            title = item.title.text
            link = item.link.text
            
            smart_info = ask_gemini(title)
            
            if "跳過" not in smart_info:
                message = f"📢 **K-POP 台灣精準情報**\n✅ {smart_info}\n🔗 來源：{link}"
                requests.post(discord_webhook_url, json={"content": message})
                count += 1
        
        print(f"成功發送 {count} 則訊息到 Discord！")
        if count == 0:
            requests.post(discord_webhook_url, json={"content": "🤖 機器人已上線，但目前 1 小時內無新的 K-POP 活動消息。"})

    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    fetch_kpop()
