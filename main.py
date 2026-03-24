import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(text):
    # 更強大的 Prompt，要求 AI 針對 Dcard 標題提取精準活動
    prompt = f"""
    你是一個專門服務 K-POP YouTuber 的情報助理。
    請分析這個 Dcard 貼文標題：『{text}』
    
    你的任務：
    1. 提取出藝人、活動日期、地點、售票時間。
    2. 如果標題提到「聯名」、「開賣」，請特別標註開賣日期與通路。
    3. 格式請統一為：『藝人：[名字] | 活動：[名稱] | 時間：[日期地點] | 售票/開賣：[日期與平台]』
    4. 語氣精簡，如果資訊不足請根據 2026 年最新台灣 K-POP 資訊嘗試補全。
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"解析失敗，原始標題：{text}"

def fetch_dcard_kpop():
    print("--- 正在掃描 Dcard 追星板最新情報 ---")
    # 我們利用 RSSHub 來抓取 Dcard 追星板，這比直接爬蟲穩定
    rss_url = "https://rsshub.app/dcard/f/star/latest"
    
    try:
        response = requests.get(rss_url, timeout=15)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')

        if not items:
            print("沒抓到 Dcard 內容")
            return

        # 抓取前 5 則最新貼文
        for item in items[:5]:
            title = item.title.text
            link = item.link.text
            
            # 讓 AI 整理資訊
            smart_info = ask_gemini(title)
            
            message = f"📌 **【Dcard 追星板情報】**\n{smart_info}\n🔗 連結：{link}"
            requests.post(discord_webhook_url, json={"content": message})
            
        print("✅ Dcard 情報已傳送到 Discord！")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_dcard_kpop()
