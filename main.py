import requests
import os

discord_webhook = os.getenv("DISCORD_WEBHOOK")

def test_scraping():
    # 偽裝成人類常用的 Chrome 瀏覽器，降低被擋的機率
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 我們要測試的三個目標
    targets = {
        "Dcard (追星板隱藏 API)": "https://www.dcard.tw/_api/forums/entertainer/posts?limit=3",
        "Weverse (BABYMONSTER 公告)": "https://weverse.io/babymonster/notice/34440",
        "Threads (網頁版首頁)": "https://www.threads.net/"
    }

    report = "🚀 **【突破舒適圈：社群平台爬蟲真實測試報告】**\n\n"

    for name, url in targets.items():
        report += f"🔍 **測試目標：{name}**\n"
        try:
            # 發送請求，最多等 10 秒
            res = requests.get(url, headers=headers, timeout=10)
            report += f"📡 狀態碼：`{res.status_code}` (200代表成功，403代表被擋)\n"
            
            # 把抓回來的東西，取前 200 個字元來看看是不是我們要的內容
            snippet = res.text[:200].replace('\n', ' ')
            report += f"📄 抓取內容預覽：\n```text\n{snippet}...\n```\n\n"
            
        except Exception as e:
            report += f"💥 連線失敗：{str(e)}\n\n"

    # 傳送到 Discord
    if discord_webhook:
        requests.post(discord_webhook, json={"content": report})
    else:
        print("找不到 Discord Webhook")

if __name__ == "__main__":
    test_scraping()
