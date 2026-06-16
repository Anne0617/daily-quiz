import sqlite3
conn = sqlite3.connect("data/content.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT day_seq, status FROM daily_content ORDER BY day_seq").fetchall()
q_count = conn.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]
print(f"总题目: {q_count} 道")
for r in rows:
    kps = conn.execute("SELECT knowledge_points FROM daily_content WHERE day_seq=?", (r["day_seq"],)).fetchone()[0]
    kp_list = conn.execute("SELECT substr(text,1,40) as t FROM questions WHERE day_seq=? ORDER BY seq", (r["day_seq"],)).fetchall()
    print(f"  第{r['day_seq']}天 ({r['status']})")
    for q in kp_list:
        print(f"    Q: {q['t']}...")
conn.close()
