import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def send_to_discord(text):
    if not discord_webhook_url:
        print("找不到 Discord Webhook")
        return
    # Discord 單則訊息上限 2000，我們設 1800 確保安全
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        requests.post(discord_webhook_url, json={"content": text[i:i+chunk_size]})
        time.sleep(1)

def check_weverse():
    report = "🕸️ **【Weverse 官方公告巡邏】**\n\n"
    
    # 👑 【Weverse 直達車名單】
    # 你可以在這裡無限新增你想監控的團體，但記得一定要放 /notice 結尾的網址！
    weverse_targets = {
        "BABYMONSTER": "https://weverse.io/babymonster/notice",
        "LE SSERAFIM": "https://weverse.io/lesserafim/notice",
        "ILLIT": "https://weverse.io/illit/notice"
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for group, url in weverse_targets.items():
                try:
                    # 直接空降該團體的公告區
                    page.goto(url, timeout=20000)
                    # Weverse 公告區通常會有很多 <a> (連結)，我們等它出現代表畫面載入完成了
                    page.wait_for_selector("a", timeout=10000)
                    time.sleep(3) # 強制等待 3 秒讓文字完全浮現
                    
                    text = page.locator("body").inner_text()
                    # 抓取前 200 個字並清理換行，避免 Python 語法錯誤
                    clean_text = text[:200].replace('\n', ' | ') 
                    report += f"🔹 **{group}**: `{clean_text}...`\n\n"
                except Exception as e:
                    report += f"❌ **{group}**: 抓取失敗 (頁面超時或防護阻擋)\n\n"
                    
            browser.close()
    except Exception as e:
        report += f"⚠️ Playwright 啟動失敗：{str(e)}\n"
        
    return report

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    events = '(演唱會 OR 售票 OR 搶票 OR 見面會 OR 聯名 OR 快閃 OR 簽售 OR 品牌 OR 代言 OR 電影 OR 戲劇 OR 出演 OR 影集)'

    q1 = '"TWICE" OR "ITZY" OR "BABYMONSTER" OR "aespa" OR "LE SSERAFIM" OR "NMIXX" OR "BLACKPINK" OR "NewJeans" OR "IVE" OR "I-DLE" OR "QWER" OR "ILLIT" OR "MEOVV"'
    q2 = '"BTS" OR "SEVENTEEN" OR "Stray Kids" OR "TXT" OR "CRAVITY" OR "BIGBANG" OR "少女時代" OR "ALLDAY PROJECT" OR "CORTIS"'
    q3 = '"IU" OR "泫雅" OR "太妍" OR "潤娥" OR "Yena" OR "GD" OR "T.O.P." OR "子瑜" OR "舒華" OR "薇娟" OR "美延" OR "Karina" OR "劉知珉" OR "Winter" OR "張員瑛" OR "Jennie" OR "Lisa" OR "Jisoo" OR "Rosé"'

    queries = [q1, q2, q3]
    all_news_dict = {}
    url_mapping = {} 
    news_counter = 1

    for q in queries:
        full_query = f"({q}) {events}" 
        rss_url = f"https://news.google.com/rss/search?q={quote(full_query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            res = requests.get(rss_url, timeout=15)
            root = ET.fromstring(res.text)
            # 確保抓取量夠大，避免舒華或 Yena 被演算法擠掉
            items = root.findall('.//item')[:30] 
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                if title not in all_news_dict:
                    link_id = f"[LINK_{news_counter:02d}]"
                    url_mapping[link_id] = link
                    all_news_dict[title] = f"- [發布時間: {pub_date}] {title} (新聞代號: {link_id})"
                    news_counter += 1
        except Exception as e:
            continue
            
    news_list = "\n".join(list(all_news_dict.values())[:80]) 

    today_str = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""
    今天是 {today_str}。請分析以下台灣新聞：
    {news_list}
    
    1. 去重統整：合併相同活動。
    2. 時間篩選：留下未來 3 個月內即將售票、舉辦的活動，或「近期上映的影視作品」。
    3. 重點定義：演唱會、見面會、簽售會、代言、實體聯名/快閃，以及「參演電影/戲劇/節目」。
    
    輸出規定：
    - 不要有廢話或問候語。
    - 格式：🔥 [藝人/團體] | [活動或影視種類] | [日期與地點/上映平台] | 售票/備註：[資訊]
    🔗 [新聞代號]
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    send_to_discord("⏳ 啟動隱身雷達！正在收集新聞與 Weverse 公告...")
    
    weverse_report = check_weverse()
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            api_res = requests.post(api_url, json=payload, timeout=None)
            if api_res.status_code == 200:
                res_json = api_res.json()
                report = res_json['candidates'][0]['content']['parts'][0]['text']
                
                # 👑 魔法隱身術：把代號換成 Discord 的 Markdown 連結格式
                # 這樣畫面上只會顯示「點我閱讀新聞」，超長網址會被完美隱藏！
                for link_id, real_url in url_mapping.items():
                    report = report.replace(link_id, f"[點我閱讀新聞]({real_url})")
                    
                final_msg = f"📢 **【K-POP 終極雷達】**\n\n{report}\n\n---\n\n{weverse_report}"
                send_to_discord(final_msg)
                break
            elif api_res.status_code == 503:
                time.sleep(20)
            else:
                send_to_discord(f"❌ **API 錯誤**: {api_res.status_code}")
                break
        except Exception as e:
            send_to_discord(f"❌ **錯誤**: {str(e)}")
            break

if __name__ == "__main__":
    fetch_and_send()
