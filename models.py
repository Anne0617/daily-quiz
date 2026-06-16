import sqlite3
import json
from datetime import datetime, date
from typing import Optional
from database import get_connection


def add_user(name: str, department: str = "") -> int:
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO users (name, department) VALUES (?, ?)", (name, department))
        conn.commit()
        row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else 0
    finally:
        conn.close()


def get_user_by_name(name: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_users() -> list[dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM users WHERE is_active=1 ORDER BY department, name").fetchall()]
    finally:
        conn.close()


def import_users_from_list(names: list[tuple[str, str]]):
    conn = get_connection()
    try:
        for name, dept in names:
            conn.execute("INSERT OR IGNORE INTO users (name, department) VALUES (?, ?)", (name.strip(), dept.strip()))
        conn.commit()
        print(f"导入完成: {len(names)} 条")
    finally:
        conn.close()


def get_or_create_daily_content(day_seq: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM daily_content WHERE day_seq = ?", (day_seq,)).fetchone()
        if not row:
            conn.execute("INSERT INTO daily_content (day_seq, status) VALUES (?, 'draft')", (day_seq,))
            conn.commit()
            row = conn.execute("SELECT * FROM daily_content WHERE day_seq = ?", (day_seq,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_pending_days() -> list[int]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT day_seq FROM daily_content WHERE status = 'draft' ORDER BY day_seq").fetchall()
        return [r["day_seq"] for r in rows]
    finally:
        conn.close()


def publish_content(day_seq: int):
    conn = get_connection()
    try:
        conn.execute("UPDATE daily_content SET status = 'published' WHERE day_seq = ?", (day_seq,))
        conn.commit()
    finally:
        conn.close()


def save_daily_content(day_seq: int, knowledge_points: list[str]):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO daily_content (day_seq, knowledge_points, status) VALUES (?, ?, 'draft')",
            (day_seq, json.dumps(knowledge_points, ensure_ascii=False))
        )
        conn.commit()
    finally:
        conn.close()


def save_question(day_seq: int, seq: int, text: str, options: dict, correct: str, explanation: str = "", topic: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO questions (day_seq, seq, text, options, correct_answer, explanation, topic) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (day_seq, seq, text, json.dumps(options, ensure_ascii=False), correct, explanation, topic)
        )
        conn.commit()
    finally:
        conn.close()


def get_today_content(day_seq: int) -> dict:
    conn = get_connection()
    try:
        dc = conn.execute("SELECT * FROM daily_content WHERE day_seq = ? AND status = 'published'", (day_seq,)).fetchone()
        if not dc:
            return {}
        dc = dict(dc)
        dc["knowledge_points"] = json.loads(dc.get("knowledge_points", "[]"))
        questions = [dict(r) for r in conn.execute("SELECT * FROM questions WHERE day_seq = ? ORDER BY seq", (day_seq,)).fetchall()]
        for q in questions:
            q["options"] = json.loads(q["options"])
        dc["questions"] = questions
        return dc
    finally:
        conn.close()


def get_published_day_count() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as c FROM daily_content WHERE status = 'published'").fetchone()
        return row["c"] if row else 0
    finally:
        conn.close()


def get_max_published_day() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT MAX(day_seq) as m FROM daily_content WHERE status = 'published'").fetchone()
        return row["m"] if row and row["m"] else 0
    finally:
        conn.close()


def submit_answers(user_id: int, day_seq: int, answers: list[str], questions: list[dict]) -> dict:
    conn = get_connection()
    details = []
    correct_count = 0
    try:
        for i, q in enumerate(questions):
            selected = answers[i].upper().strip() if i < len(answers) else ""
            correct = q["correct_answer"].upper().strip()
            is_correct = 1 if selected == correct else 0
            if is_correct:
                correct_count += 1
            conn.execute(
                "INSERT OR REPLACE INTO answers (user_id, day_seq, question_seq, selected, is_correct) VALUES (?, ?, ?, ?, ?)",
                (user_id, day_seq, q["seq"], selected, is_correct)
            )
            details.append({
                "seq": q["seq"], "text": q["text"], "selected": selected,
                "correct_answer": correct, "options": q["options"],
                "is_correct": bool(is_correct), "explanation": q.get("explanation", ""),
            })
        conn.commit()
    finally:
        conn.close()
    return {"score": correct_count, "total": len(questions), "details": details}


def get_user_score_for_day(user_id: int, day_seq: int) -> Optional[dict]:
    conn = get_connection()
    try:
        correct = conn.execute("SELECT COUNT(*) as c FROM answers WHERE user_id=? AND day_seq=? AND is_correct=1", (user_id, day_seq)).fetchone()["c"]
        total = conn.execute("SELECT COUNT(*) as c FROM answers WHERE user_id=? AND day_seq=?", (user_id, day_seq)).fetchone()["c"]
        if total == 0:
            return None
        return {"user_id": user_id, "day_seq": day_seq, "correct": correct, "total": total}
    finally:
        conn.close()


def get_week_report(year: int, week: int) -> dict:
    conn = get_connection()
    try:
        from datetime import datetime
        first_day = datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u").date()
        last_day = datetime.strptime(f"{year}-W{week:02d}-7", "%G-W%V-%u").date()
        start_str = first_day.strftime("%Y-%m-%d")
        end_str = last_day.strftime("%Y-%m-%d")

        rows = conn.execute("""
            SELECT u.name, u.department,
                   COUNT(a.id) as total_answers,
                   SUM(CASE WHEN a.is_correct=1 THEN 1 ELSE 0 END) as correct_answers,
                   COUNT(DISTINCT a.day_seq) as days_participated
            FROM users u
            LEFT JOIN answers a ON u.id = a.user_id
            WHERE a.answered_at >= ? AND a.answered_at < ?
            GROUP BY u.id
            ORDER BY (SUM(CASE WHEN a.is_correct=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(a.id)) DESC
        """, (start_str, end_str)).fetchall()

        total_days = conn.execute(
            "SELECT COUNT(*) as c FROM daily_content WHERE push_date >= ? AND push_date < ? AND status='published'",
            (start_str, end_str)
        ).fetchone()["c"]

        return {
            "year": year, "week": week, "start_date": start_str, "end_date": end_str,
            "total_days": total_days, "users": [dict(r) for r in rows]
        }
    finally:
        conn.close()


def get_wrong_questions_top(limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT q.day_seq, q.seq, q.text, q.options, q.correct_answer, q.explanation,
                   COUNT(CASE WHEN a.is_correct=0 THEN 1 END) as wrong_count,
                   COUNT(a.id) as total_count
            FROM answers a
            JOIN questions q ON a.day_seq = q.day_seq AND a.question_seq = q.seq
            GROUP BY q.id
            ORDER BY wrong_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["options"] = json.loads(d["options"])
            d["wrong_rate"] = round(d["wrong_count"] / d["total_count"] * 100, 1) if d["total_count"] > 0 else 0
            result.append(d)
        return result
    finally:
        conn.close()
