import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(title):
    # 這裡加入更嚴格的指令，如果 AI 抓不到具體日期，就讓它去「猜測」或「補完」
    prompt = f"""
    你現在是 K-POP 專業主編。請分析這則來自台灣媒體的新聞標題：『{title}』
    
    你的任務：
    1. 提取：藝人名稱、活動日期、地點、售票/開賣時間、售票平台。
    2. 格式：『藝人：[名字] | 活動：[名稱] | 時間：[日期地點] | 售票：[日期平台]』
    3. 特別注意：如果是聯名活動（如 7-11, Uniqlo），請註明「開賣日」。
    4. 如果標題資訊不足，請根據你對 2026 年台灣 K-POP 市場的了解（如 ITZY 3/24 售票）進行補完。
    5. 如果完全無關，請回傳『無關』。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        res_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return res_text
    except:
        return "無關"

def fetch_kpop():
    # 這裡我把搜尋字串加長，強制包含你想要的媒體類型
    # 搜尋：(KPOP OR 韓星) AND (台灣 OR 台北) AND (開賣 OR 聯名 OR 簽售 OR 演唱會)
    search_query = "KPOP+台灣+(開賣+OR+聯名+OR+簽售+OR+快閃店+OR+演唱會)"
    search_url = f"https://news.google.com/rss/search?q={search_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        response = requests.get(search_url, timeout=15)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')
        
        found_any = False
        for item in items[:8]: # 擴大掃描前 8 則
            title = item.title.text
            link = item.link.text
            
            smart_info = ask_gemini(title)
            
            if "無關" not in smart_info:
                message = f"📰 **【K-POP 專業情報解析】**\n✅ {smart_info.strip()}\n🔗 來源：{link}"
                requests.post(discord_webhook_url, json={"content": message})
                found_any = True
        
        if not found_any:
            print("目前無精準活動消息。")

    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    fetch_kpop()
