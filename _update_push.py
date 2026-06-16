import pathlib
ws = pathlib.Path(__file__).parent.resolve()

# Read current wecom_push.py
wp = ws / "wecom_push.py"
old = wp.read_text(encoding="utf-8")

new_wp = '''import json
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
        f"# \\U0001f4c9 星河十五五规划 · 第{day_seq}天",
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
        "## \\U0001f4d1 【今日自测】",
        "点击下方链接参与今日答题：",
        f"[\\U0001f420 开始第 {day_seq} 天答题]({quiz_url})",
        "",
        "> \\u23f1 请于今日完成 5 道选择题，答完即时显示得分与解析。",
    ]
    content = "\\n".join(lines)
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
        f"# \\U0001f4ca 第{day_seq}天进度报告",
        f"**时间：** {today} 18:00{mention}",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 应考人数 | {total} 人 |",
        f"| 已答人数 | {answered} 人 |",
        f"| 完成率 | {rate}% |",
        f"| 平均正确率 | {correct_rate}% |",
        "",
        f"[\\U0001f4dd 查看详情]({settings.base_url}/quiz?day={day_seq})",
        "",
        "> \\u23f3 尚未答题的同事请务必于今晚完成。",
    ]
    content = "\\n".join(lines)
    if not settings.wecom_webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL not set")
        return False
    return send_markdown(settings.wecom_webhook_url, content)


def push_weekly_reminder(week: int, unfinished: list[dict], published_days: int) -> bool:
    mention = f" @{settings.admin_mention}" if settings.admin_mention else ""
    lines = [
        f"# \\u26a0\\ufe0f 第{week}周催办通知{mention}",
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
        lines.append("\\U0001f389 本周所有同事已全部完成考试，无需催办！")
    content = "\\n".join(lines)
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
'''

wp.write_text(new_wp, encoding="utf-8")
print("wecom_push.py updated")

# Now update scheduler.py
sp = ws / "scheduler.py"
new_sp = '''import sys
from datetime import date, datetime, timedelta
from config import settings
from models import get_max_published_day, get_today_content, get_all_users
from wecom_push import push_daily_message, push_daily_stats, push_weekly_reminder, push_report_message
from reporter import push_week_report, push_month_report
import sqlite3


def get_conn():
    import sqlite3
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def today_day_seq() -> int:
    max_day = get_max_published_day()
    return max_day + 1 if max_day > 0 else 1


def task_push():
    day_seq = today_day_seq()
    content = get_today_content(day_seq)
    if not content:
        print(f"Day {day_seq} content not published, skip push")
        return
    quiz_url = f"{settings.base_url}/quiz?day={day_seq}"
    success = push_daily_message(day_seq, content["knowledge_points"], quiz_url)
    if success:
        conn = get_conn()
        conn.execute("UPDATE daily_content SET push_date = ? WHERE day_seq = ?",
                     (date.today().strftime("%Y-%m-%d"), day_seq))
        conn.commit()
        conn.close()
        print(f"Day {day_seq} pushed OK")
    return success


def task_daily_stats():
    day_seq = today_day_seq()
    conn = get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active=1").fetchone()["c"]
        answered = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM answers WHERE day_seq=?", (day_seq,)).fetchone()["c"]
        correct = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=? AND is_correct=1", (day_seq,)).fetchone()["c"]
        total_q = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=?", (day_seq,)).fetchone()["c"]
        correct_rate = round(correct / total_q * 100, 1) if total_q > 0 else 0
    finally:
        conn.close()

    print(f"Stats for day {day_seq}: {answered}/{total} answered, correct rate {correct_rate}%")
    success = push_daily_stats(day_seq, total, answered, correct_rate)
    print("Stats push OK" if success else "Stats push FAILED")
    return success


def task_weekly_reminder():
    today = date.today()
    iso = today.isocalendar()
    year, week = iso[0], iso[1]

    first_day = datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u").date()
    last_day = datetime.strptime(f"{year}-W{week:02d}-7", "%G-W%V-%u").date()

    conn = get_conn()
    try:
        published_days = conn.execute(
            "SELECT day_seq FROM daily_content WHERE status='published' AND push_date >= ? AND push_date <= ?",
            (first_day.isoformat(), last_day.isoformat())
        ).fetchall()
        published_day_seqs = [r["day_seq"] for r in published_days]
        published_count = len(published_day_seqs)

        if published_count == 0:
            print("No published days this week, skip reminder")
            return

        users = conn.execute("SELECT id, name, department FROM users WHERE is_active=1").fetchall()
        unfinished = []
        for u in users:
            answered = conn.execute(
                "SELECT COUNT(DISTINCT day_seq) as c FROM answers WHERE user_id=? AND day_seq IN ({seqs})".format(
                    seqs=",".join("?" * len(published_day_seqs))
                ),
                (u["id"], *published_day_seqs)
            ).fetchone()["c"]
            missing = published_count - answered
            if missing > 0:
                unfinished.append({"name": u["name"], "department": u["department"], "missing_days": missing})
    finally:
        conn.close()

    print(f"Week {week} reminder: {len(unfinished)} unfinished out of {len(users)} users")
    success = push_weekly_reminder(week, unfinished, published_count)
    print("Reminder push OK" if success else "Reminder push FAILED")
    return success


def task_week_report():
    push_week_report()


def task_month_report():
    push_month_report()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scheduler.py [push|stats|reminder|week_report|month_report]")
        sys.exit(1)
    action = sys.argv[1]
    if action == "push":
        task_push()
    elif action == "stats":
        task_daily_stats()
    elif action == "reminder":
        task_weekly_reminder()
    elif action == "week_report":
        task_week_report()
    elif action == "month_report":
        task_month_report()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
'''

sp.write_text(new_sp, encoding="utf-8")
print("scheduler.py updated")
