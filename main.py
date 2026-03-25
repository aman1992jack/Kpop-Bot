import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
from datetime import datetime

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def send_to_discord(text):
    if not discord_webhook_url:
        print("找不到 Discord Webhook")
        return
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        requests.post(discord_webhook_url, json={"content": text[i:i+chunk_size]})
        time.sleep(1)

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    # 【第一層升級：精準團名關鍵字打擊】
    groups = '"TWICE" OR "ITZY" OR "BABYMONSTER" OR "aespa" OR "LE SSERAFIM" OR "NMIXX" OR "BLACKPINK" OR "NewJeans" OR "IVE" OR "(G)I-DLE" OR "BTS" OR "SEVENTEEN" OR "Stray Kids"'
    keywords = '台灣 (演唱會 OR 售票 OR 搶票 OR 見面會 OR 聯名 OR 快閃)'
    query = f"({groups}) {keywords}"
    
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=15)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:25] 
        
        news_list = ""
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            news_list += f"- [發布時間: {pub_date}] {title} (連結: {link})\n"

        today_str = datetime.now().strftime("%Y年%m月%d日")

        # 【第二層與第三層：AI 深度去重與時間篩選】
        prompt = f"""
        今天是 {today_str}。請作為一個資料處理程式，分析以下台灣新聞：
        {news_list}
        
        請嚴格執行以下三層過濾邏輯：
        1. 去重與統整：新聞中可能有多家媒體報導同一個活動，請將相同活動的資訊合併，以資訊最完整的那篇為主，並附上該篇連結。
        2. 時間篩選：嚴格剔除「已經發生過的活動」、「售票日已過」的活動。只留下未來 3 個月內即將售票或舉辦的活動。
        3. 重點定義：包含演唱會、見面會、簽售會、以及速食店/超商等實體聯名或快閃活動。
        
        輸出規定（非常嚴格）：
        - 絕對不要輸出任何問候語、廢話、免責聲明、或搶票提醒。
        - 只能使用以下單一格式輸出：
        
        🔥 [藝人/團體] | [活動種類] | [演出/活動日期與地點] | 售票：[日期與時間]
        🔗 [新聞連結]
        
        如果經過篩選後，完全沒有未來 3 個月內的活動，請只輸出單行文字：「🤖 目前網路上無未來 3 個月內的最新 K-POP 活動情報。」
        """
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        send_to_discord("⏳ 啟動無時間限制模式！正在請 Gemini 2.5 Flash 撰寫深度情報...")
        
        # 👑 終極死纏爛打機制：如果 503 塞車，就自動重試
        max_retries = 5
        for attempt in range(max_retries):
            # timeout=None 代表程式會無止盡地等下去，不再主動掛電話
            api_res = requests.post(api_url, json=payload, timeout=None)
            
            if api_res.status_code == 200:
                res_json = api_res.json()
                report = res_json['candidates'][0]['content']['parts'][0]['text']
                send_to_discord(f"📢 **【K-POP 點名雷達 (無限制突圍版)】**\n\n{report}")
                break # 成功就跳出迴圈，任務結束
                
            elif api_res.status_code == 503:
                send_to_discord(f"⚠️ Google 伺服器塞車中 (503)，機器人將在 20 秒後發動第 {attempt + 1} 次重試...")
                time.sleep(20) # 休息 20 秒再撞一次
                
            else:
                send_to_discord(f"❌ **API 發生未預期錯誤**: {api_res.status_code}\n{api_res.text}")
                break # 遇到其他死胡同錯誤，直接放棄
                
    except Exception as e:
        send_to_discord(f"⚠️ 程式運行中斷：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
