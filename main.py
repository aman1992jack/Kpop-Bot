import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

# 你的專屬追蹤名單
MY_GROUPS = "BLACKPINK, BABYMONSTER, NMIXX, LE SSERAFIM, IVE, QWER, aespa, ITZY, (G)I-DLE, ILLIT, TWICE, BTS, ALLDAY PROJECT, CORTIS, GENBLUE, 幻藍小熊, BIGBANG"

def ask_gemini(title):
    prompt = f"""
    你是一個台灣 K-POP 專家。請分析這則標題：『{title}』。
    
    任務：
    1. 判斷是否屬於這份名單中的成員或團體活動：{MY_GROUPS}。
    2. 如果是，請提取未來三個月（2026年3月-6月）在台灣的活動資訊。
    3. 必須包含：藝人、活動名、演出日期地點、售票日期(含優先購票)與平台。
    4. 格式：『藝人：[名字] | 活動：[名稱] | 演出：[日期地點] | 售票：[優先/正式售票日期與平台]』。
    5. 如果標題資訊不足，請利用你的知識庫補齊（例如 ITZY 3/24-3/26 售票）。
    6. 若不相關，請回傳『跳過』。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        res_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return res_text
    except:
        return "跳過"

def fetch_future_kpop():
    # 擴大搜尋範圍，直接找未來幾個月的關鍵字
    queries = [
        "KPOP+台灣+2026+演唱會+售票",
        "ITZY+高雄+售票",
        "TWICE+台灣+活動",
        "GENBLUE+幻藍小熊+行程",
        "KPOP+開賣+2026"
    ]
    
    found_any = False
    headers = {'User-Agent': 'Mozilla/5.0'}

    for q in queries:
        search_url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            response = requests.get(search_url, timeout=15)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            for item in items[:5]: # 每個關鍵字抓前 5 則
                title = item.title.text
                smart_info = ask_gemini(title)
                
                if "跳過" not in smart_info:
                    msg = f"🌟 **【三個月內重點情報】**\n✅ {smart_info.strip()}\n🔗 來源：{item.link.text}"
                    requests.post(discord_webhook_url, json={"content": msg})
                    found_any = True
        except:
            continue
            
    if not found_any:
        requests.post(discord_webhook_url, json={"content": "目前尚未搜尋到符合名單的新活動資訊。"})

if __name__ == "__main__":
    fetch_future_kpop()
