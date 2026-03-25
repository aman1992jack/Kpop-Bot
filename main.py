import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def send_to_discord(text):
    if not discord_webhook_url:
        print("找不到 Discord Webhook")
        return
    # 分段發送，避免超過 Discord 2000 字限制
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        requests.post(discord_webhook_url, json={"content": text[i:i+chunk_size]})
        time.sleep(1)

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    # 1. 抓取豐富的 K-POP 新聞
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:10] # 一次抓 10 則給 AI 分析
        
        news_list = ""
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            news_list += f"- {title} (連結: {link})\n"

        # 2. 👑 完整的 AI 靈魂指令
        prompt = f"""
        你現在是台灣 K-POP 專業情報員。請分析以下最新新聞：
        {news_list}
        
        任務：提取未來三個月在台灣的活動資訊。
        必須包含：藝人、活動名、演出日期地點、售票日期。
        格式：『🔥 [藝人] | [活動] | [日期地點] | 售票：[日期]』。若無精準日期也請列出大概時間。
        
        請以適合發布在社群媒體的活潑語氣排版，過濾掉無關的八卦新聞，只留下活動與搶票情報。如果新聞有附上連結，請在該活動底下附上 [新聞連結](網址)。
        """
        
        # 3. 呼叫我們成功突圍的 2.5 Flash 大腦
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        send_to_discord("⏳ 正在請 Gemini 2.5 Flash 撰寫深度情報...")
        
        api_res = requests.post(api_url, json=payload, timeout=30)
        
        # 4. 完美輸出
        if api_res.status_code == 200:
            res_json = api_res.json()
            report = res_json['candidates'][0]['content']['parts'][0]['text']
            send_to_discord(f"📢 **【K-POP 台灣深度情報雷達 (2.5 滿血完全體)】**\n\n{report}")
        else:
            send_to_discord(f"❌ **API 發生錯誤**: {api_res.status_code}\n{api_res.text}")
            
    except Exception as e:
        send_to_discord(f"⚠️ 程式運行中斷：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
