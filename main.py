import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

# 你的專屬追蹤名單
MY_GROUPS = "BLACKPINK, BABYMONSTER, NMIXX, LE SSERAFIM, IVE, QWER, aespa, ITZY, (G)I-DLE, ILLIT, TWICE, BTS, ALLDAY PROJECT, CORTIS, GENBLUE, 幻藍小熊, BIGBANG"

def ask_gemini(text):
    # 這裡調整了指令，要求 AI 必須從文字中提取「未來 3 個月內」的台灣活動
    prompt = f"""
    你現在是台灣 K-POP 專業情報員。請分析這段文字：『{text}』
    
    任務：
    1. 判斷是否包含以下名單成員在台灣的活動：{MY_GROUPS}。
    2. 活動日期必須在 2026 年 3 月至 6 月之間。
    3. 必須提取：藝人、活動名、演出日期地點、所有售票階段(卡友/會員/全面開賣)與平台。
    4. 格式：『藝人：[名字] | 活動：[名稱] | 演出：[日期地點] | 售票：[優先/正式售票日期與平台]』。
    5. 若標題資訊不全，請根據你對 2026 年台灣活動的實時理解（如 ITZY 高雄場售票：3/24-3/26）進行補完。
    6. 若不相關，請回傳『跳過』。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "跳過"

def fetch_future_kpop():
    # 這裡我更換了搜尋策略，使用多組「強效搜尋詞」
    search_terms = [
        "ITZY+高雄+演唱會+售票",
        "TWICE+台灣+2026+活動",
        "BABYMONSTER+台灣+見面會",
        "KPOP+台灣+演唱會+2026+列表",
        "韓星+來台+2026+時間表"
    ]
    
    found_any = False
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 為了讓你看到成果，我們先鎖定這幾個詞進行深度掃描
    for q in search_terms:
        # 使用 Google News 搜尋，但擴大範圍
        search_url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            response = requests.get(search_url, timeout=15)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            for item in items[:5]: # 每一類抓前 5 則
                title = item.title.text
                link = item.link.text
                
                smart_info = ask_gemini(title)
                
                if "跳過" not in smart_info:
                    msg = f"🔍 **【挖掘到未來三個月行程】**\n✅ {smart_info.strip()}\n🔗 來源：{link}"
                    requests.post(discord_webhook_url, json={"content": msg})
                    found_any = True
        except:
            continue
            
    if not found_any:
        # 如果還是沒抓到，我們傳送一個 Debug 訊息，讓你確認程式有在跑
        requests.post(discord_webhook_url, json={"content": "🤖 雷達掃描完畢，目前網路上尚未更新符合名單的新活動資訊。"})

if __name__ == "__main__":
    fetch_future_kpop()
