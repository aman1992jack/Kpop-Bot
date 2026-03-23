import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(text):
    # 這裡強化了指令，要求 AI 必須像專業助理一樣提供具體資訊
    prompt = f"""
    你是一個專門服務 YouTuber 的 K-POP 專業情報助理。
    請分析這則新聞標題：『{text}』
    
    你的任務：
    1. 提取或推論該活動在「台灣」的具體資訊。
    2. 格式必須嚴格遵守：『日期，藝人活動名稱在地點，售票時間與平台』。
    3. 如果新聞標題是懶人包，請從中挑選「最新」或「最熱門」的一個活動來撰寫。
    4. 語氣要專業、精簡，不要任何廢話。
    
    範例輸出：2026/06/27，ITZY 演唱會在高雄巨蛋，2026/03/24 在拓元售票系統，星展銀行優先購票。
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"無法解析資訊: {text}"

def fetch_kpop_taiwan():
    # 增加關鍵字精準度
    search_url = "https://news.google.com/rss/search?q=KPOP+台灣+(開賣+OR+演唱會+OR+簽售+OR+聯名+OR+快閃店)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')
        
        for item in items[:3]:
            original_title = item.title.text
            # 呼叫強化的 AI 解析
            smart_info = ask_gemini(original_title)
            
            # 組合 Discord 訊息
            message = f"📢 **K-POP 台灣精準情報**\n✅ {smart_info}\n🔗 來源：{item.link.text}"
            
            requests.post(discord_webhook_url, json={"content": message})
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_kpop_taiwan()
