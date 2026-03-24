import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote

print("🚀 程式開始執行...")

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
if not discord_webhook_url:
    print("❌ 致命錯誤：找不到 DISCORD_WEBHOOK！請檢查 GitHub Secrets 是否有設定對。")
    exit(1)
else:
    print("✅ 成功讀取 Discord 鑰匙")

def fetch_and_send():
    query = "KPOP 台灣 (開賣 OR 聯名 OR 簽售 OR 演唱會)"
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    print(f"🔍 準備抓取新聞...")
    try:
        res = requests.get(rss_url, timeout=10)
        print(f"📡 Google News 連線狀態碼: {res.status_code} (200代表成功)")
        
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:10]
        print(f"🗞️ 成功抓到 {len(items)} 則新聞，開始過濾關鍵字...")
        
        report = "📢 **【K-POP 台灣最新情報推播 (大聲除錯版)】**\n\n"
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
        
        # 發送 Discord
        discord_res = requests.post(discord_webhook_url, json={"content": report})
        print(f"📨 Discord 回傳狀態碼: {discord_res.status_code} (204代表成功發送)")
        print(f"📨 Discord 官方回覆內容: {discord_res.text}")
        
    except Exception as e:
        print(f"💥 發生嚴重錯誤：{str(e)}")

if __name__ == "__main__":
    fetch_and_send()
    print("🏁 程式執行完畢")
