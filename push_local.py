"""本地推送助手 - 从 Railway 获取内容并复制到剪贴板"""
import sys, json, urllib.request, pyperclip

# Railway 上部署后的地址（部署后改成实际的）
RAILWAY_URL = "https://your-app.railway.app"

def fetch_daily(day: int) -> dict:
    url = f"{RAILWAY_URL}/api/daily-content?day={day}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"获取失败: {e}")
        return None

def main():
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if not day:
        print("用法: python push_local.py <天数>")
        return
    
    data = fetch_daily(day)
    if not data:
        return
    
    msg = data["message"]
    pyperclip.copy(msg)
    print(f"✓ 第{day}天内容已复制到剪贴板")
    print(f"  知识点: {len(data['knowledge_points'])}条")
    print(f"  答题链接: {data['quiz_url']}")
    print()
    print("去企微群里按 Ctrl+V 粘贴发送")

if __name__ == "__main__":
    main()
