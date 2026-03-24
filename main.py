import requests
import os
import xml.etree.ElementTree as ET
import time
from urllib.parse import quote

print("🚀 程式開始執行...")

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
if not discord_webhook_url:
    print("❌ 致命錯誤：找不到 DISCORD_WEBHOOK！")
    exit(1)

def fetch_and_send():
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:10]
        
        report = "📢 **【K-POP 台灣最新情報推播 (直連滿血版)】**\n\n"
        has_news = False
        
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            
            if any(keyword in title for keyword in ["演唱會", "搶票", "售票", "來台", "開賣"]):
                report += f"🔥 **{title}**\n🔗 <{link}>\n\n"
                has_news = True
                
        if not has_news:
            report += "🤖 目前網路上尚未更新重要的 K-POP 活動資訊。"
            
        print(f"📝 準備發送至 Discord，總字數為：{len(report)}")
        
        # 關鍵修復：分段發送邏輯 (每次最多傳 1800 字)
        chunk_size = 1800
        for i in range(0, len(report), chunk_size):
            chunk = report[i:i+chunk_size]
            discord_res = requests.post(discord_webhook_url, json={"content": chunk})
            print(f"📨 第 {i//chunk_size + 1} 段發送狀態: {discord_res.status_code}")
            time.sleep(1) # 暫停 1 秒避免被 Discord 鎖定
            
    except Exception as e:
        print(f"💥 發生錯誤：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
    print("🏁 程式執行完畢")
