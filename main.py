import requests
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini_to_report():
    # 這是最強的指令：直接讓 AI 整合它目前已知的 2026 台灣 K-POP 實時情報
    prompt = """
    你現在是專門服務台灣 YouTuber 的 K-POP 專業情報主編。
    請根據 2026 年 3 月 24 日的最新現狀，整理出未來三個月（3月-6月）在台灣最火熱的 K-POP 活動。
    
    重點提取對象：ITZY, TWICE, CNBLUE, BABYMONSTER, 幻藍小熊, NMIXX, IVE, aespa, (G)I-DLE。
    
    請務必包含以下已確定的精準資訊：
    1. ITZY 高雄巨蛋 (6/27)：3/24 星展預售、3/25 會員預售、3/26 拓元全面開賣。
    2. CNBLUE 高雄海音館 (6/13)：3/26 12:00 年代售票全面開賣。
    3. 其他你在 2026 年已知且尚未結束的聯名活動或演唱會。
    
    格式要求：
    『🔥 [藝人名] | [活動名]
    演出日期：[日期地點]
    售票/開賣：[精準時間與平台]
    備註：[給創作者的拍片提醒]』
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI 解析暫時離線，請檢查 API Key。錯誤：{e}"

def run_daily_report():
    print("🚀 正在生成今日 K-POP 深度情報...")
    report = ask_gemini_to_report()
    
    if report:
        # 為了美觀，我們分段傳送
        data = {"content": f"📢 **【K-POP 台灣三個月情報雷達】**\n資料更新日期：2026/03/24\n\n{report}"}
        requests.post(discord_webhook_url, json=data)
        print("✅ 報表已發送到 Discord！")

if __name__ == "__main__":
    run_daily_report()
