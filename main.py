import requests
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini_to_report():
    prompt = """
    你現在是台灣 K-POP 專業情報主編。請針對 2026 年 3 月至 6 月在台灣的活動提供報表。
    
    已知重要資訊：
    1. ITZY 高雄場 (6/27)：3/24星展預售、3/25會員預售、3/26正式開賣。
    2. CNBLUE 高雄場 (6/13)：3/26 12:00 年代售票開賣。
    
    請以『藝人 | 活動 | 售票日期 | 地點』的格式整理。
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        res_json = response.json()
        
        # 修正點：檢查是否有回傳結果，避免 'candidates' 報錯
        if 'candidates' in res_json and len(res_json['candidates']) > 0:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return "⚠️ AI 暫時無法生成內容，請稍後再試。原因：API 回傳格式異常。"
    except Exception as e:
        return f"❌ 發生錯誤：{str(e)}"

def run_daily_report():
    report = ask_gemini_to_report()
    data = {"content": f"📢 **【K-POP 台灣三個月情報雷達】**\n\n{report}"}
    requests.post(discord_webhook_url, json=data)

if __name__ == "__main__":
    run_daily_report()
