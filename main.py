import requests
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini_safe(prompt_text):
    # 更換成更穩定的 Pro 模型，並放寬安全設定
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        # 增加多層檢查，防止 candidates 消失
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        elif 'promptFeedback' in res_json:
            return f"內容被 Google 屏蔽，原因：{res_json['promptFeedback']}"
        else:
            return "無法解析回傳格式"
    except Exception as e:
        return f"連線錯誤：{str(e)}"

def run_daily_report():
    # 這裡我們直接提供事實，讓 AI 做排版就好
    info_text = """
    請幫我整理 2026/03/24-06/30 台灣 KPOP 重點：
    1. ITZY 高雄 6/27：3/24預售, 3/25預售, 3/26全面開賣。
    2. CNBLUE 高雄 6/13：3/26 售票。
    3. 子瑜 7-11 聯名：請查詢是否有最新開賣日。
    請用 Markdown 列表格式輸出。
    """
    report = ask_gemini_safe(info_text)
    requests.post(discord_webhook_url, json={"content": f"📢 **K-POP 深度情報 (PRO 模式)**\n\n{report}"})

if __name__ == "__main__":
    run_daily_report()
