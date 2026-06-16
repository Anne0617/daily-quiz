"""
Unified message sender for WeCom.
- Priority 1: Webhook API (if WECOM_WEBHOOK_URL is set)
- Priority 2: Desktop UI automation (if WECOM_GROUP_NAME is set)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from datetime import datetime


def send_message(message: str, msg_type: str = "text") -> bool:
    """Send a message via available channel. Returns True if sent successfully."""

    # Try webhook first (admin-friendly)
    if settings.wecom_webhook_url:
        from wecom_push import send_markdown
        ok = send_markdown(settings.wecom_webhook_url, message)
        if ok:
            print(f"[sender] Sent via webhook ({msg_type})")
            return True
        print(f"[sender] Webhook failed, trying desktop...")

    # Fallback: desktop automation
    group_name = getattr(settings, "wecom_group_name", "")
    if group_name:
        from desktop_sender import send_to_wecom_group
        ok = send_to_wecom_group(group_name, message)
        if ok:
            print(f"[sender] Sent via desktop automation ({msg_type})")
            return True
        print(f"[sender] Desktop automation failed")

    print(f"[sender] No channel available - set WECOM_WEBHOOK_URL or WECOM_GROUP_NAME")
    return False


def push_daily(day_seq: int) -> bool:
    """Push today knowledge points + quiz link."""
    from models import get_today_content
    content = get_today_content(day_seq)
    if not content:
        print(f"[sender] Day {day_seq} not published")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    quiz_url = f"{settings.base_url}/quiz?day={day_seq}"
    kps = content.get("knowledge_points", [])

    lines = [
        f"# 星河十五五规划 · 第{day_seq}天",
        f"**日期：** {today}",
        "",
        "【今日知识点】",
    ]
    for i, kp in enumerate(kps, 1):
        lines.append(f"{i}. {kp}")
    lines += [
        "",
        "---",
        "",
        "【今日自测】",
        "点击下方链接参与今日答题：",
        f"> {quiz_url}",
        "",
        "请于今日完成 5 道选择题，答完即时显示得分与解析。",
    ]
    msg = "\n".join(lines)
    return send_message(msg, f"daily_push_day{day_seq}")


def push_stats(day_seq: int) -> bool:
    """Push daily completion stats."""
    import sqlite3
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active=1").fetchone()["c"]
        answered = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM answers WHERE day_seq=?", (day_seq,)).fetchone()["c"]
        correct = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=? AND is_correct=1", (day_seq,)).fetchone()["c"]
        total_q = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=?", (day_seq,)).fetchone()["c"]
        rate = round(correct / total_q * 100, 1) if total_q > 0 else 0
    finally:
        conn.close()

    pct = round(answered / total * 100, 1) if total > 0 else 0
    lines = [
        f"# 第{day_seq}天进度报告",
        f"**时间：** {datetime.now().strftime('%Y-%m-%d')} 18:00",
        "",
        f"应考人数：{total} 人",
        f"已答人数：{answered} 人",
        f"完成率：{pct}%",
        f"平均正确率：{rate}%",
        "",
        f"> 答题链接：{settings.base_url}/quiz?day={day_seq}",
        "",
        "尚未答题的同事请务必于今晚完成。",
    ]
    msg = "\n".join(lines)
    return send_message(msg, f"daily_stats_day{day_seq}")


def push_reminder(week: int) -> bool:
    """Push weekly reminder for unfinished users."""
    from datetime import date, timedelta
    import sqlite3

    today = date.today()
    iso = today.isocalendar()
    year, wk = iso[0], iso[1]
    first_day = datetime.strptime(f"{year}-W{wk:02d}-1", "%G-W%V-%u").date()
    last_day = datetime.strptime(f"{year}-W{wk:02d}-7", "%G-W%V-%u").date()

    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        published = conn.execute(
            "SELECT day_seq FROM daily_content WHERE status='published' AND push_date >= ? AND push_date <= ?",
            (first_day.isoformat(), last_day.isoformat())
        ).fetchall()
        day_seqs = [r["day_seq"] for r in published]
        pub_count = len(day_seqs)

        if pub_count == 0:
            print("[reminder] No published days this week")
            return False

        users = conn.execute("SELECT id, name, department FROM users WHERE is_active=1").fetchall()
        unfinished = []
        for u in users:
            answered = conn.execute(
                f"SELECT COUNT(DISTINCT day_seq) as c FROM answers WHERE user_id=? AND day_seq IN ({','.join('?' * len(day_seqs))})",
                (u["id"], *day_seqs)
            ).fetchone()["c"]
            missing = pub_count - answered
            if missing > 0:
                unfinished.append({"name": u["name"], "dept": u["department"], "missing": missing})
    finally:
        conn.close()

    lines = [f"# 第{wk}周催办通知"]
    if unfinished:
        lines.append(f"本周共发布 {pub_count} 天考试，以下同事尚未完成：")
        lines.append("")
        for u in unfinished:
            lines.append(f"- {u['name']}（{u['dept'] or '-'}）缺考 {u['missing']} 天")
        lines += [
            "",
            "请上述同事务必在今晚完成缺考内容。",
        ]
    else:
        lines.append("本周所有同事已全部完成考试，无需催办！")
    msg = "\n".join(lines)
    return send_message(msg, f"reminder_week{wk}")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "push":
        day = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        if not day:
            from models import get_max_published_day
            day = get_max_published_day() + 1
        push_daily(day)
    elif action == "stats":
        day = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        if not day:
            from models import get_max_published_day
            day = get_max_published_day() + 1
        push_stats(day)
    elif action == "reminder":
        from datetime import date
        push_reminder(date.today().isocalendar()[1])
    else:
        print("Usage: python auto_sender.py [push|stats|reminder] [day]")
