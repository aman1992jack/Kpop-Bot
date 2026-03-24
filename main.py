import requests
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
gemini_key = os.getenv("GEMINI_API_KEY")

def ask_gemini_safe(prompt_text):
    if not gemini_key:
        return "🛑 嚴重錯誤：找不到 Gemini API Key！"

    # 改回確定找得到的 flash 模型，並保留「解除安全封鎖」的強大設定！
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
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
        
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        elif 'error' in res_json:
            error_code = res_json['error'].get('code')
            error_msg = res_json['error'].get('message')
            return f"❌ Google API 拒絕連線！\n錯誤代碼：{error_code}\n原因：{error_msg}"
        else:
            return f"⚠️ 未知的回傳格式，原始資料：{res_json}"
            
    except Exception as e:
        return f"🌐 連線層級錯誤：{str(e)}"

def run_daily_report():
    info_text = """
    請幫我整理 2026/03/24-06/30 台灣 KPOP 重點：
    1. ITZY 高雄 6/27：3/24預售, 3/25預售, 3/26全面開賣。
    2. CNBLUE 高雄 6/13：3/26 售票。
    請用 Markdown 列表格式輸出。
    """
    report = ask_gemini_safe(info_text)
    requests.post(discord_webhook_url, json={"content": f"📢 **K-POP 深度情報 (解除封印版)**\n\n{report}"})

if __name__ == "__main__":
    run_daily_report()
