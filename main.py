import requests
from bs4 import BeautifulSoup
import os

# 取得鑰匙
discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(text):
    # 這段是請 Gemini 幫忙整理資訊的指令
    prompt = f"你是一個 K-POP 專家。請從以下新聞標題中提取活動資訊，格式必須為：『日期，藝人活動名稱在地點，售票時間與平台』。如果資訊不全，請根據你的知識補全（特別是台灣的售票習慣）。新聞內容：{text}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return text # 如果 AI 出錯，就回傳原始標題

def fetch_kpop_taiwan():
    search_url = "https://news.google.com/rss/search?q=KPOP+台灣+(開賣+OR+演唱會+OR+簽售+OR+聯名+OR+快閃店)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')
        
        for item in items[:3]: # 先抓 3 則測試
            original_title = item.title.text
            # 讓 AI 幫你整理成你想要的格式
            smart_info = ask_gemini(original_title)
            
            message = f"🌟 **【AI 自動整理情報】**\n{smart_info}\n🔗 來源：{item.link.text}\n------------------------------------"
            requests.post(discord_webhook_url, json={"content": message})
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_kpop_taiwan()
