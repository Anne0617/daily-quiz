import sqlite3
conn = sqlite3.connect("data/content.db")
conn.row_factory = sqlite3.Row

count = conn.execute("SELECT COUNT(*) as c FROM daily_content").fetchone()["c"]
published = conn.execute("SELECT COUNT(*) as c FROM daily_content WHERE status='published'").fetchone()["c"]
questions = conn.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]

print(f"daily_content: {count} 条 (已发布: {published})")
print(f"questions: {questions} 道")

if count > 0:
    rows = conn.execute("SELECT day_seq, status, substr(knowledge_points,1,60) as kp_preview FROM daily_content ORDER BY day_seq").fetchall()
    for r in rows:
        print(f"  第{r['day_seq']}天: {r['status']} - {r['kp_preview']}...")

conn.close()
