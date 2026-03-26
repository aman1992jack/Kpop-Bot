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
    
    lines = text.split('\n')
    current_msg = ""
    
    for line in lines:
        if len(current_msg) + len(line) + 1 > 1800:
            try:
                requests.post(discord_webhook_url, json={"content": current_msg}, timeout=10)
            except:
                pass
            time.sleep(1)
            current_msg = line + "\n"
        else:
            current_msg += line + "\n"
            
    if current_msg.strip():
        try:
            requests.post(discord_webhook_url, json={"content": current_msg}, timeout=10)
        except:
            pass

def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    events = '(演唱會 OR 售票 OR 搶票 OR 見面會 OR 聯名 OR 快閃 OR 簽售 OR 品牌 OR 代言 OR 電影 OR 戲劇 OR 出演 OR 影集 OR 大銀幕 OR 主演 OR 回歸 OR 新歌)'

    q1 = '"TWICE" OR "ITZY" OR "BABYMONSTER" OR "aespa" OR "LE SSERAFIM" OR "NMIXX" OR "BLACKPINK" OR "NewJeans" OR "IVE" OR "I-DLE" OR "QWER" OR "ILLIT" OR "MEOVV" OR "幻藍小熊" OR "GENBLUE"'
    q2 = '"BTS" OR "SEVENTEEN" OR "Stray Kids" OR "TXT" OR "CRAVITY" OR "BIGBANG" OR "少女時代" OR "ALLDAY PROJECT" OR "CORTIS"'
    q3 = '"IU" OR "泫雅" OR "太妍" OR "潤娥" OR "Yena" OR "GD" OR "T.O.P." OR "子瑜" OR "舒華" OR "薇娟" OR "美延" OR "Karina" OR "劉知珉" OR "Winter" OR "張員瑛" OR "Jennie" OR "Lisa" OR "Jisoo" OR "Rosé"'

    queries = [q1, q2, q3]
    all_news_dict = {}
    url_mapping = {} 
    news_counter = 1

    for q in queries:
        full_query = f"({q}) {events} when:30d" 
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
    
    if not news_list.strip():
        send_to_discord("🤖 爬蟲回報：目前各大平台均無相關新聞。")
        return

    today_str = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""
    今天是 {today_str}。請作為專業的 K-POP 台灣站情報分析師，分析以下新聞清單：
    {news_list}
    
    請嚴格執行以下情報萃取與過濾 SOP：
    
    1. 【地域限制 - 專注台灣】：
       - 實體活動（演唱會、見面會、簽售會、快閃店、展覽）：【必須在台灣（包含台北、高雄、林口、桃園等）】。嚴格剔除海外活動。
       - 全球性情報（發布新歌、回歸、出新專輯、影視作品上映、國際品牌代言）：不限地區，請一律保留。
       
    2. 【動態時間過濾】（請以今天日期 {today_str} 為基準核對）：
       - 單次性活動（演唱會、簽售會、頒獎典禮）：如果活動舉辦日期「已經過去」，請【直接剔除】。
       - 持續性活動（超商聯名、快閃店、品牌代言）：如果今天還在「活動效期內」，請保留；若已結束，請剔除。
       
    3. 【無情過濾垃圾】：剔除網友八卦、吵架、單純機場穿搭、無明確企劃的農場文。
    
    輸出規定：
    - 絕對不要有任何問候語、廢話或開場白。
    - 格式：🔥 [藝人/團體] | [情報種類] | [時間與地點/備註] | 詳情：[重點資訊]
    - 🔗 每個活動【只能保留一個】最具代表性的新聞代號，直接輸出代號（如：[LINK_01]）。
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    send_to_discord("⏳ 啟動動態日曆防卡死雷達！正在為您篩選最新鮮的台灣情報...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # 👑 聽你的建議：給予 AI 充分的 3 分鐘 (180 秒) 思考時間！
            api_res = requests.post(api_url, json=payload, timeout=180)
            if api_res.status_code == 200:
                res_json = api_res.json()
                candidate = res_json.get('candidates', [{}])[0]
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    report = candidate['content']['parts'][0]['text']
                    
                    for link_id, real_url in url_mapping.items():
                        report = report.replace(link_id, f"[📰 閱讀新聞](<{real_url}>)")
                        
                    final_msg = f"📢 **【K-POP 終極雷達】**\n\n{report}"
                    send_to_discord(final_msg)
                else:
                    finish_reason = candidate.get('finishReason', '未知原因')
                    send_to_discord(f"⚠️ AI 拒絕分析！原因代碼：{finish_reason}")
                break
            elif api_res.status_code == 503:
                time.sleep(20)
            else:
                send_to_discord(f"❌ **API 錯誤**: {api_res.status_code}")
                break
        except Exception as e:
            send_to_discord(f"⚠️ 第 {attempt + 1} 次嘗試失敗 (等待超過 3 分鐘)，準備重試...")
            time.sleep(5) 

if __name__ == "__main__":
    fetch_and_send()
