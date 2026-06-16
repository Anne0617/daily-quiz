import sys
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
    from auto_sender import push_daily
    day_seq = today_day_seq()
    success = push_daily(day_seq)
    if success:
        conn = get_conn()
        conn.execute("UPDATE daily_content SET push_date = ? WHERE day_seq = ?",
                     (date.today().strftime("%Y-%m-%d"), day_seq))
        conn.commit()
        conn.close()
        print(f"Day {day_seq} pushed OK")
    return success


def task_daily_stats():
    from auto_sender import push_stats
    day_seq = today_day_seq()
    success = push_stats(day_seq)
    print(f"Stats for day {day_seq} sent: {success}")
    return success


def task_weekly_reminder():
    from auto_sender import push_reminder
    today = date.today()
    iso = today.isocalendar()
    success = push_reminder(iso[1])
    print(f"Week {iso[1]} reminder sent: {success}")
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
