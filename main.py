import requests
import os
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def send_to_discord(text):
    if not discord_webhook_url:
        print("找不到 Discord Webhook 網址")
        return
    # 分段發送，避免超過 Discord 2000 字限制
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        requests.post(discord_webhook_url, json={"content": text[i:i+chunk_size]})
        time.sleep(1)

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 測試中斷：找不到 GEMINI_API_KEY，請檢查 GitHub Secrets。")
        return

    # 1. 抓取測試用新聞
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:5] 
        
        news_list = ""
        for item in items:
            title = item.find('title').text
            news_list += f"- {title}\n"

        # 2. 準備呼叫 API
        prompt = f"請將以下新聞整理成『🔥 [藝人] | [活動]』的格式：\n{news_list}"
        
        # 👑 關鍵修改：使用官方正確的模型名稱 gemini-2.5-flash
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        send_to_discord("⏳ 正在向 **Gemini 2.5 Flash** 發送請求，請稍候...")
        
        # 3. 發送請求並攔截所有資訊
        api_res = requests.post(api_url, json=payload, timeout=30)
        
        # 4. 深度解析回傳結果
        if api_res.status_code == 200:
            res_json = api_res.json()
            report = res_json['candidates'][0]['content']['parts'][0]['text']
            send_to_discord(f"✅ **API 連線奇蹟成功 (2.5 大腦)！**\n\n{report}")
        else:
            # 整理最詳細的報錯單
            error_msg = f"❌ **API 拒絕連線 (2.5 診斷報告)**\n\n"
            error_msg += f"**1. HTTP 狀態碼:** `{api_res.status_code}`\n"
            
            try:
                error_json = api_res.json()
                formatted_error = json.dumps(error_json, indent=2, ensure_ascii=False)
                error_msg += f"**2. 官方原始報錯內容:**\n```json\n{formatted_error}\n```"
            except:
                error_msg += f"**2. 官方原始報錯內容:**\n```text\n{api_res.text}\n```"
                
            send_to_discord(error_msg)
            
    except Exception as e:
        send_to_discord(f"⚠️ 程式運行中斷：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
