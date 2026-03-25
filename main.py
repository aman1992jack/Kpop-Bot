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

    # 1. 抓取新聞：加入 when:14d，只搜尋最近 14 天內的最新新聞
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會) when:14d"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:15] # 抓取前 15 則最新新聞
        
        news_list = ""
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text # 把新聞發布時間也抓下來
            news_list += f"- [{pub_date}] {title} (連結: {link})\n"

        # 取得今天真實的日期
        today_str = datetime.now().strftime("%Y年%m月%d日")

        # 2. 👑 軍事化極簡指令：禁絕廢話、定義聯名為重點
        prompt = f"""
        今天是 {today_str}。請分析以下最近 14 天內的台灣 K-POP 新聞：
        {news_list}
        
        任務要求：
        1. 提取未來三個月內的活動資訊（包含演唱會、見面會、簽售會、聯名活動等，例如速食店聯名也算重點活動）。
        2. 絕對不要輸出任何問候語、結語、免責聲明或搶票提醒。不要跟我打招呼。
        3. 嚴格比對時間，如果活動或售票日期已經在 {today_str} 之前發生，請直接捨棄。
        4. 嚴格遵守以下格式條列，不要加上任何多餘的敘述文字：
        
        🔥 [藝人或品牌] | [活動種類] | [演出/活動日期與地點] | 售票/開始：[日期]
        🔗 [新聞連結]
        
        如果沒有符合條件的未來活動，請只輸出「🤖 目前近期無最新的 K-POP 重點活動情報。」
        """
        
        # 3. 呼叫 Gemini 2.5 Flash
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        api_res = requests.post(api_url, json=payload, timeout=30)
        
        # 4. 完美發送
        if api_res.status_code == 200:
            res_json = api_res.json()
            report = res_json['candidates'][0]['content']['parts'][0]['text']
            send_to_discord(f"📢 **【K-POP 台灣深度情報雷達】**\n\n{report}")
        else:
            send_to_discord(f"❌ **API 發生錯誤**: {api_res.status_code}\n{api_res.text}")
            
    except Exception as e:
        send_to_discord(f"⚠️ 程式運行中斷：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
