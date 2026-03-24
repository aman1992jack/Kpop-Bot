import requests
import os
import xml.etree.ElementTree as ET
import time
from urllib.parse import quote

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 嚴重錯誤：找不到 Gemini API Key！請檢查 GitHub Secrets。")
        return

    # 1. 爬蟲去抓網路資料
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:5]  # 抓前 5 則
        
        news_list = ""
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            news_list += f"- {title} ({link})\n"
            
        if not news_list:
            send_to_discord("🤖 目前網路上尚未更新 K-POP 活動資訊。")
            return

        # 2. 把抓到的資料，寫成給 AI 的指令
        prompt = f"""
        你現在是台灣 K-POP 專業情報員。請分析以下最新新聞：
        {news_list}
        任務：提取未來三個月在台灣的活動資訊。必須包含：藝人、活動名、演出日期地點、售票日期。
        格式：『🔥 [藝人] | [活動] | [日期地點] | 售票：[日期]』。若無精準日期也請列出大概時間。
        """
        
        # 3. 連線到 Google 的 2.0 超級大腦！
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        ai_res = requests.post(api_url, json=payload, timeout=30)
        res_json = ai_res.json()
        
        # 4. 解析 AI 回傳的精美排版
        final_report = ""
        if 'candidates' in res_json and len(res_json['candidates']) > 0:
            final_report = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            final_report = f"❌ AI 拒絕處理！真實報錯原因：\n{res_json}\n\n原始新聞：\n{news_list}"
            
        # 5. 發送到你的 Discord
        full_message = f"📢 **【K-POP 台灣深度情報雷達 (GitHub 滿血版)】**\n\n{final_report}"
        send_to_discord(full_message)
        
    except Exception as e:
        send_to_discord(f"⚠️ 機器人發生錯誤：{str(e)}")

def send_to_discord(text):
    # Discord 的極限是 2000 字，這裡設定每次最多傳 1800 字並分段
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        requests.post(discord_webhook_url, json={"content": chunk})
        time.sleep(1)  # 讓機器人喘口氣，避免被 Discord 擋下

if __name__ == "__main__":
    fetch_and_send()
