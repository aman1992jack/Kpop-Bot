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
    chunk_size = 1800
    for i in range(0, len(text), chunk_size):
        requests.post(discord_webhook_url, json={"content": text[i:i+chunk_size]})
        time.sleep(1)

def test_playwright_social():
    report = "🕸️ **【社群平台 Playwright 抓取測試】**\n\n"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. 測試 Weverse
            report += "🔍 **目標：Weverse (BABYMONSTER)**\n"
            try:
                page.goto("https://weverse.io/babymonster/notice/34440", timeout=15000)
                page.wait_for_selector(".container, .data-container, table tbody tr, .loading-spinner", timeout=10000)
                time.sleep(2)
                text = page.locator("body").inner_text()
                clean_text = text[:150].replace('\n', ' ') # 👑 修復點
                report += f"✅ 成功！預覽：`{clean_text}...`\n\n"
            except Exception as e:
                report += f"❌ 失敗：{str(e)}\n\n"
                
            # 2. 測試 Threads
            report += "🔍 **目標：Threads**\n"
            try:
                page.goto("https://www.threads.net/", timeout=15000)
                page.wait_for_selector("._ammd, ._aqff, .system-fonts--body, .segoe", timeout=10000)
                time.sleep(2)
                text = page.locator("body").inner_text()
                clean_text = text[:150].replace('\n', ' ') # 👑 修復點
                report += f"✅ 成功！預覽：`{clean_text}...`\n\n"
            except Exception as e:
                report += f"❌ 失敗：{str(e)}\n\n"
                
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
    
    send_to_discord("⏳ 雷達啟動！正在收集新聞與測試社群平台...")
    
    social_report = test_playwright_social()
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            api_res = requests.post(api_url, json=payload, timeout=None)
            if api_res.status_code == 200:
                res_json = api_res.json()
                report = res_json['candidates'][0]['content']['parts'][0]['text']
                
                for link_id, real_url in url_mapping.items():
                    report = report.replace(link_id, real_url)
                    
                final_msg = f"📢 **【K-POP 終極雷達】**\n\n{report}\n\n---\n\n{social_report}"
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
