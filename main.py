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
    
    lines = text.split('\n')
    current_msg = ""
    
    for line in lines:
        if len(current_msg) + len(line) + 1 > 1800:
            requests.post(discord_webhook_url, json={"content": current_msg})
            time.sleep(1)
            current_msg = line + "\n"
        else:
            current_msg += line + "\n"
            
    if current_msg.strip():
        requests.post(discord_webhook_url, json={"content": current_msg})

def check_weverse():
    report = "🕸️ **【Weverse 官方公告巡邏】**\n\n"
    
    weverse_targets = {
        "BABYMONSTER": "https://weverse.io/babymonster/notice",
        "LE SSERAFIM": "https://weverse.io/lesserafim/notice",
        "ILLIT": "https://weverse.io/illit/notice"
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            for group, url in weverse_targets.items():
                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_selector("a[href*='/notice/']", timeout=15000)
                    time.sleep(3) 
                    
                    notice_links = page.locator("a[href*='/notice/']").all_inner_texts()
                    if notice_links:
                        clean_text = " | ".join([t.strip() for t in notice_links if t.strip()])[:200].replace('\n', '')
                        report += f"🔹 **{group}**: `{clean_text}...`\n\n"
                    else:
                        report += f"🔹 **{group}**: 目前無最新公告\n\n"
                except Exception as e:
                    report += f"❌ **{group}**: 抓取超時或遭阻擋\n\n"
                    
            browser.close()
    except Exception as e:
        report += f"⚠️ Playwright 啟動失敗：{str(e)}\n"
        
    return report

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    events = '(演唱會 OR 售票 OR 搶票 OR 見面會 OR 聯名 OR 快閃 OR 簽售 OR 品牌 OR 代言 OR 電影 OR 戲劇 OR 出演 OR 影集)'

    q1 = '"TWICE" OR "ITZY" OR "BABYMONSTER" OR "aespa" OR "LE SSERAFIM" OR "NMIXX" OR "BLACKPINK" OR "NewJeans" OR "IVE" OR "I-DLE" OR "QWER" OR "ILLIT" OR "MEOVV" OR "幻藍小熊" OR "GENBLUE"'
    q2 = '"BTS" OR "SEVENTEEN" OR "Stray Kids" OR "TXT" OR "CRAVITY" OR "BIGBANG" OR "少女時代" OR "ALLDAY PROJECT" OR "CORTIS"'
    q3 = '"IU" OR "泫雅" OR "太妍" OR "潤娥" OR "Yena" OR "GD" OR "T.O.P." OR "子瑜" OR "舒華" OR "薇娟" OR "美延" OR "Karina" OR "劉知珉" OR "Winter" OR "張員瑛" OR "Jennie" OR "Lisa" OR "Jisoo" OR "Rosé"'

    queries = [q1, q2, q3]
    all_news_dict = {}
    url_mapping = {} 
    news_counter = 1

    for q in queries:
        # 👑 第一道鎖：在搜尋字串後加上 when:1m，強制 Google 只給最近 1 個月的新聞
        full_query = f"({q}) {events} when:1m" 
        rss_url = f"https://news.google.com/rss/search?q={quote(full_query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            res = requests.get(rss_url, timeout=15)
            root = ET.fromstring(res.text)
            items = root.findall('.//item')[:50] 
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
            
    news_list = "\n".join(list(all_news_dict.values())) 

    today_str = datetime.now().strftime("%Y年%m月%d日")

    # 👑 第二道鎖：在 AI 指令中明確區分「舉辦日期」與「發布時間」
    prompt = f"""
    今天是 {today_str}。請分析以下台灣新聞：
    {news_list}
    
    請嚴格執行以下過濾邏輯：
    1. 去重統整：合併相同活動。
    2. 時間篩選：實體活動（演唱會/見面會）請留下未來 3 個月內的資訊。
       ⚠️ 特例保護：若是「參演電影/戲劇/節目」或「品牌代言/聯名」的消息，【不受活動舉辦日期的限制】，但前提是該新聞的「發布時間」必須是近期！
    
    輸出規定：
    - 不要有廢話或問候語。
    - 格式：🔥 [藝人/團體] | [活動或影視種類] | [日期與地點/上映平台] | 售票/備註：[資訊]
    - 🔗 每個活動【只能保留一個】最具代表性的新聞代號，請直接輸出代號（如：[LINK_01]）。
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    send_to_discord("⏳ 啟動終極淨化保鮮雷達！正在收集海量新聞與精準掃描 Weverse...")
    
    weverse_report = check_weverse()
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            api_res = requests.post(api_url, json=payload, timeout=None)
            if api_res.status_code == 200:
                res_json = api_res.json()
                report = res_json['candidates'][0]['content']['parts'][0]['text']
                
                for link_id, real_url in url_mapping.items():
                    report = report.replace(link_id, f"[📰 閱讀新聞](<{real_url}>)")
                    
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
