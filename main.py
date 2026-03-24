import requests
import os

discord_webhook_url = os.getenv("DISCORD_WEBHOOK")
claude_key = os.getenv("CLAUDE_API_KEY")

def ask_claude(prompt_text):
    if not claude_key:
        return "🛑 嚴重錯誤：找不到 Claude API Key！"

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": claude_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt_text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()

        if 'content' in res_json:
            return res_json['content'][0]['text']
        elif 'error' in res_json:
            error_type = res_json['error'].get('type')
            error_msg = res_json['error'].get('message')
            return f"❌ Claude API 錯誤！\n類型：{error_type}\n原因：{error_msg}"
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
    report = ask_claude(info_text)
    requests.post(discord_webhook_url, json={"content": f"📢 **K-POP 深度情報**\n\n{report}"})

if __name__ == "__main__":
    run_daily_report()
