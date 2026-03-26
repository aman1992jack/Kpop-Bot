def fetch_and_send():
    if not gemini_key:
        send_to_discord("🛑 錯誤：找不到 GEMINI_API_KEY")
        return

    # 【分流雷達設定】
    locations = '(台灣 OR 台北 OR 高雄 OR 桃園 OR 台南 OR 林口)'
    # 👑 修改 1：在關鍵字中加入「電影、戲劇、出演、影集」，一網打盡影視情報
    events = '(演唱會 OR 售票 OR 搶票 OR 見面會 OR 聯名 OR 快閃 OR 簽售 OR 品牌 OR 代言 OR 電影 OR 戲劇 OR 出演 OR 影集)'

    q1 = '"TWICE" OR "ITZY" OR "BABYMONSTER" OR "aespa" OR "LE SSERAFIM" OR "NMIXX" OR "BLACKPINK" OR "NewJeans" OR "IVE" OR "I-DLE" OR "QWER" OR "ILLIT" OR "MEOVV"'
    q2 = '"BTS" OR "SEVENTEEN" OR "Stray Kids" OR "TXT" OR "CRAVITY" OR "BIGBANG" OR "少女時代" OR "ALLDAY PROJECT" OR "CORTIS"'
    q3 = '"IU" OR "泫雅" OR "太妍" OR "潤娥" OR "Yena" OR "GD" OR "T.O.P." OR "子瑜" OR "舒華" OR "薇娟" OR "美延" OR "Karina" OR "劉知珉" OR "Winter" OR "張員瑛" OR "Jennie" OR "Lisa" OR "Jisoo" OR "Rosé"'

    queries = [q1, q2, q3]
    all_news_dict = {}
    url_mapping = {} 
    news_counter = 1

    for q in queries:
        full_query = f"({q}) {locations} {events}"
        rss_url = f"https://news.google.com/rss/search?q={quote(full_query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            res = requests.get(rss_url, timeout=15)
            root = ET.fromstring(res.text)
            items = root.findall('.//item')[:15] 
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
            print(f"抓取批次發生錯誤: {e}")
            continue
            
    news_list = "\n".join(list(all_news_dict.values())[:40]) 

    if not news_list:
        send_to_discord("🤖 爬蟲回報：目前各大平台均無相關新聞。")
        return

    today_str = datetime.now().strftime("%Y年%m月%d日")

    # 👑 修改 2：更新 AI 指令，明確把「影視作品出演」列入重點定義
    prompt = f"""
    今天是 {today_str}。請作為一個資料處理程式，分析以下台灣新聞：
    {news_list}
    
    請嚴格執行以下三層過濾邏輯：
    1. 去重與統整：新聞中可能有多家媒體報導同一個活動，請將相同活動的資訊合併，以資訊最完整的那篇為主。
    2. 時間篩選：嚴格剔除「已經發生過的實體活動」、「售票日已過」的活動。只留下未來 3 個月內即將售票、舉辦的活動，或「近期即將上映/播出的影視作品」。
    3. 重點定義：包含演唱會、見面會、簽售會、品牌代言活動、實體聯名/快閃活動、以及「參演電影/戲劇/節目」等影視跨界消息。
    
    輸出規定（非常嚴格）：
    - 絕對不要輸出任何問候語、廢話、免責聲明、或搶票提醒。
    - 只能使用以下單一格式輸出：
    
    🔥 [藝人/團體] | [活動或影視種類] | [日期與地點/上映平台] | 售票/備註：[相關資訊]
    🔗 [新聞代號]
    
    注意：連結部分請直接輸出「[新聞代號]」即可（例如 🔗 [LINK_01]），絕對不要輸出任何網址。
    如果經過篩選後沒有任何情報，請只輸出：「🤖 目前網路上無未來 3 個月內的最新 K-POP 活動情報。」
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    send_to_discord("⏳ 啟動影視跨界擴充雷達！正在請 Gemini 2.5 Flash 撰寫深度情報...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            api_res = requests.post(api_url, json=payload, timeout=None)
            if api_res.status_code == 200:
                res_json = api_res.json()
                report = res_json['candidates'][0]['content']['parts'][0]['text']
                
                for link_id, real_url in url_mapping.items():
                    report = report.replace(link_id, real_url)
                    
                send_to_discord(f"📢 **【K-POP 終極雷達 (影視擴充版)】**\n\n{report}")
                break
            elif api_res.status_code == 503:
                send_to_discord(f"⚠️ Google 伺服器塞車中 (503)，機器人將在 20 秒後發動第 {attempt + 1} 次重試...")
                time.sleep(20)
            else:
                send_to_discord(f"❌ **API 發生未預期錯誤**: {api_res.status_code}\n{api_res.text}")
                break
        except Exception as e:
            send_to_discord(f"❌ **呼叫 AI 發生錯誤**: {str(e)}")
            break
