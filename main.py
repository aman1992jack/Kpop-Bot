import requests
from bs4 import BeautifulSoup
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini(title, link):
    # 強化指令：要求 AI 就算標題模糊，也要根據目前的 2026 KPOP 知識來解析
    prompt = f"""
    你現在是台灣 K-POP 專業情報員。標題：『{title}』。
    請從這則新聞中提取 2026 年 3月至 6月在台灣的活動：
    1. 藝人與活動名
    2. 演出日期與地點
    3. 售票日期（含優先購票、全面開賣）與平台
    
    格式必須是：『藝人：[名字] | 活動：[名稱] | 演出：[日期地點] | 售票：[日期平台]』
    
    已知事實參考（如果標題提到以下藝人，請優先使用這些正確日期）：
    - ITZY 高雄場：3/24星展預售、3/25會員預售、3/26全面開賣 (拓元)
    - CNBLUE 高雄場：3/26 全面開賣 (年代)
    - 孫燕姿 大巨蛋：3/20 已開賣 (KKTIX)
    - TWICE 台北場：3/20-22 已結束
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return None

def fetch_kpop():
    # 這裡我把關鍵字組合得非常暴力，確保 Google 一定會噴出東西
    queries = [
        "ITZY+高雄+售票+拓元",
        "2026+演唱會+台灣+KPOP+售票",
        "KPOP+聯名+開賣+2026",
        "子瑜+7-11+聯名+開賣",
        "CNBLUE+高雄+售票"
    ]
    
    processed_titles = set() # 避免重複發送
    
    for q in queries:
        search_url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            response = requests.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            for item in items[:3]:
                title = item.title.text
                if title in processed_titles: continue
                
                info = ask_gemini(title, item.link.text)
                if info and "藝人：" in info:
                    message = f"🔥 **【挖到重點情報】**\n{info}\n🔗 來源：{item.link.text}"
                    requests.post(discord_webhook_url, json={"content": message})
                    processed_titles.add(title)
        except:
            continue

if __name__ == "__main__":
    fetch_kpop()
