import requests
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
from datetime import datetime, timedelta

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
    q3 = '"IU" OR "泫雅" OR "太妍" OR "潤娥" OR "Yena" OR "崔叡娜" OR "叡娜" OR "GD" OR "T.O.P." OR "子瑜" OR "舒華" OR "薇娟" OR "美延" OR "Karina" OR "劉知珉" OR "Winter" OR "張員瑛" OR "Jennie" OR "Lisa" OR "Jisoo" OR "Rosé"'

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
            # 👑 擴大搜索面：從 50 條提升到 100 條，絕不放過任何角落！
            items = root.findall('.//item')[:100] 
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

    tw_time = datetime.utcnow() + timedelta(hours=8)
    today_str = tw_time.strftime("%Y年%m月%d日")
    short_date = f"{tw_time.month}/{tw_time.day}"
    report_type = "早報" if tw_time.hour < 15 else "晚報"
    header_title = f"【K-POP 終極雷達 - {short_date} {report_type}】"

    prompt = f"""
    今天是台灣時間 {today_str}。請作為嚴格的 K-POP 情報分析師，分析以下新聞清單：
    {news_list}
    
    請嚴格執行以下 4 大鐵則，若不符合請【直接剔除】，寧缺勿濫：
    
    1. 【強制去重 (唯一化)】：同一個活動（例如 IVE 台北演唱會），不管清單裡有幾篇報導，【強制合併成唯一 1 筆】！挑選資訊最齊全的一篇作為代表連結。絕對不准出現重複的活動！
    2. 【擊殺懶人包】：看到標題含有「懶人包、總整理、盤點、全攻略」的統整性新聞，請【直接刪除】！我們只需要獨立情報，不需要空泛的盤點。
    3. 【地域與時間雙重過濾】：
       - 實體活動（演唱會/見面會/快閃）：【僅限台灣】。海外一律刪除。
       - 絕對不要財經分析(營收/股價)、炎上爭議、八卦緋聞、機場穿搭。
       - 單次活動若日期「已過」，或聯名活動「已過期」，直接刪除。
    4. 【無日期特例 (3天法則)】：若是「影視大銀幕出演」、「品牌代言」或「音樂回歸」，只要該新聞的 [發布時間] 在 3 天內（{today_str} 往前推 3 天），【無視舉辦日期，強制保留】！
    
    輸出規定：
    - 絕對不要有任何廢話或開場白。
    - 格式：🔥 [藝人/團體] | [情報種類] | [時間與地點/備註] | 詳情：[重點資訊]
    - 🔗 直接輸出代號（如：[LINK_01]）。
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
    
    send_to_discord(f"⏳ 啟動 {report_type} 深度掃描！搜索範圍擴大至 300 篇，正在進行 5 分鐘精準去重過濾...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # 👑 思考時間大升級：給予 AI 5分鐘 (300 秒) 處理龐大資料！
            api_res = requests.post(api_url, json=payload, timeout=300)
            if api_res.status_code == 200:
                res_json = api_res.json()
                candidate = res_json.get('candidates', [{}])[0]
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    report = candidate['content']['parts'][0]['text']
                    
                    for link_id, real_url in url_mapping.items():
                        report = report.replace(link_id, f"[📰 閱讀新聞](<{real_url}>)")
                        
                    final_msg = f"📢 **{header_title}**\n\n{report}"
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
            send_to_discord(f"⚠️ 第 {attempt + 1} 次嘗試失敗，準備重試...")
            time.sleep(5) 

if __name__ == "__main__":
    fetch_and_send()
