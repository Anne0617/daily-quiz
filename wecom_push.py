import json
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import settings


def send_markdown(webhook_url: str, content: str) -> bool:
    payload = json.dumps({"msgtype": "markdown", "markdown": {"content": content}}, ensure_ascii=False).encode("utf-8")
    try:
        req = Request(webhook_url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("errcode") == 0
    except URLError as e:
        print(f"send_markdown error: {e}")
        return False


def push_daily_message(day_seq: int, knowledge_points: list[str], quiz_url: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# \U0001f4c9 星河十五五规划 · 第{day_seq}天",
        f"**日期：** {today}",
        "",
        "## 【今日知识点】",
    ]
    for i, kp in enumerate(knowledge_points, 1):
        lines.append(f"{i}. {kp}")
    lines += [
        "",
        "---",
        "",
        "## \U0001f4d1 【今日自测】",
        "点击下方链接参与今日答题：",
        f"[\U0001f420 开始第 {day_seq} 天答题]({quiz_url})",
        "",
        "> \u23f1 请于今日完成 5 道选择题，答完即时显示得分与解析。",
    ]
    content = "\n".join(lines)
    if not settings.wecom_webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL not set")
        return False
    print(f"Pushing day {day_seq}...")
    success = send_markdown(settings.wecom_webhook_url, content)
    print("Pushed OK" if success else "Push FAILED")
    return success


def push_daily_stats(day_seq: int, total: int, answered: int, correct_rate: float) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    rate = round(answered / total * 100, 1) if total > 0 else 0
    mention = f" @{settings.admin_mention}" if settings.admin_mention else ""
    lines = [
        f"# \U0001f4ca 第{day_seq}天进度报告",
        f"**时间：** {today} 18:00{mention}",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 应考人数 | {total} 人 |",
        f"| 已答人数 | {answered} 人 |",
        f"| 完成率 | {rate}% |",
        f"| 平均正确率 | {correct_rate}% |",
        "",
        f"[\U0001f4dd 查看详情]({settings.base_url}/quiz?day={day_seq})",
        "",
        "> \u23f3 尚未答题的同事请务必于今晚完成。",
    ]
    content = "\n".join(lines)
    if not settings.wecom_webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL not set")
        return False
    return send_markdown(settings.wecom_webhook_url, content)


def push_weekly_reminder(week: int, unfinished: list[dict], published_days: int) -> bool:
    mention = f" @{settings.admin_mention}" if settings.admin_mention else ""
    lines = [
        f"# \u26a0\ufe0f 第{week}周催办通知{mention}",
        f"本周共发布 **{published_days}** 天考试，以下同事尚未完成：",
        "",
    ]
    if unfinished:
        lines.append("| 姓名 | 部门 | 缺考天数 |")
        lines.append("|------|------|--------|")
        for u in unfinished:
            lines.append(f"| {u['name']} | {u.get('department', '-')} | {u.get('missing_days', published_days)} 天 |")
        lines += [
            "",
            "请上述同事务必在今晚完成缺考内容，周末将统一汇总报告。",
        ]
    else:
        lines.append("\U0001f389 本周所有同事已全部完成考试，无需催办！")
    content = "\n".join(lines)
    if not settings.wecom_webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL not set")
        return False
    return send_markdown(settings.wecom_webhook_url, content)


def push_report_message(summary_text: str) -> bool:
    if not settings.wecom_webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL not set")
        return False
    return send_markdown(settings.wecom_webhook_url, summary_text)


if __name__ == "__main__":
    import sys
    from models import get_today_content
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    content = get_today_content(day)
    if content:
        url = f"{settings.base_url}/quiz?day={day}"
        push_daily_message(day, content["knowledge_points"], url)
    else:
        print(f"Day {day} not published yet")
