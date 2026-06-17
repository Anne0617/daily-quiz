from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from models import get_today_content, add_user, get_user_by_name, submit_answers
from database import get_connection
from datetime import datetime
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class SubmitRequest(BaseModel):
    name: str
    department: str = ""
    day_seq: int
    answers: list[str]


@router.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, day: int):
    content = get_today_content(day)
    if not content:
        return HTMLResponse(f"<h3>第 {day} 天的内容尚未发布</h3>", status_code=404)
    return templates.TemplateResponse(request, "quiz.html", context={
        "day_seq": day,
        "knowledge_points": content["knowledge_points"],
        "questions": content["questions"],
    })


@router.post("/api/submit")
async def submit_exam(req: SubmitRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "请填写姓名")
    if len(req.answers) != 5:
        raise HTTPException(400, "请完成全部 5 道题")
    user = get_user_by_name(name)
    if not user:
        user_id = add_user(name, req.department.strip())
        user = {"id": user_id, "name": name, "department": req.department.strip()}
    elif not user.get("department") and req.department:
        conn = get_connection()
        conn.execute("UPDATE users SET department=? WHERE id=?", (req.department.strip(), user["id"]))
        conn.commit()
        conn.close()
    content = get_today_content(req.day_seq)
    if not content:
        raise HTTPException(404, "该日内容不存在")
    result = submit_answers(user["id"], req.day_seq, req.answers, content["questions"])
    result["name"] = name
    result["department"] = user.get("department", "")
    result["day_seq"] = req.day_seq
    return JSONResponse(result)


@router.get("/api/check_user")
async def check_user(name: str):
    user = get_user_by_name(name.strip())
    if user:
        return JSONResponse({"exists": True, "name": user["name"], "department": user.get("department", "")})
    return JSONResponse({"exists": False})


@router.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@router.get("/api/daily-content")
async def daily_content(day: int):
    """API for local push script: returns formatted daily content."""
    content = get_today_content(day)
    if not content:
        return JSONResponse({"error": f"Day {day} not published"}, status_code=404)
    
    today = datetime.now().strftime("%Y-%m-%d")
    quiz_url = f"{settings.base_url}/quiz?day={day}"
    kps = content.get("knowledge_points", [])
    
    lines = [f"星河十五五规划 · 第{day}天", f"日期：{today}", "", "【今日知识点】"]
    for i, kp in enumerate(kps, 1):
        lines.append(f"{i}. {kp}")
    lines += ["", "---", "", "【今日自测】", quiz_url, "", "请完成 5 道选择题，答完即出分。"]
    
    return JSONResponse({
        "day": day,
        "knowledge_points": kps,
        "quiz_url": quiz_url,
        "message": "\n".join(lines),
    })

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html", {})


@router.get("/api/stats/days")
async def stats_days():
    from database import get_connection
from datetime import datetime
from config import settings
    conn = get_connection()
    rows = conn.execute("SELECT day_seq FROM daily_content WHERE status='published' ORDER BY day_seq").fetchall()
    conn.close()
    return JSONResponse([r["day_seq"] for r in rows])


@router.get("/api/stats/unanswered")
async def stats_unanswered(day: int):
    from database import get_connection
from datetime import datetime
from config import settings
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name, department FROM users WHERE is_active=1").fetchall()
        result = []
        for u in rows:
            a = conn.execute("SELECT count(*) FROM answers WHERE user_id=? AND day_seq=?", (u["id"], day)).fetchone()[0]
            if a == 0:
                result.append({"name": u["name"], "dept": u["department"]})
    finally:
        conn.close()
    return JSONResponse({"unanswered": result})

@router.get("/api/settings")
async def get_settings():
    from config import settings
    return JSONResponse({"push_time": settings.push_time, "stats_time": settings.stats_time, "reminder_time": settings.reminder_time, "reminder_day": settings.reminder_day, "base_url": settings.base_url})

@router.post("/api/settings")
async def save_settings(data: dict):
    import re
    env_path = ws / ".env"
    try:
        env = env_path.read_text(encoding="utf-8")
        for key in ["PUSH_TIME", "STATS_TIME", "REMINDER_TIME", "REMINDER_DAY", "BASE_URL"]:
            k = key.lower()
            if k in data and data.get(k) is not None:
                env = re.sub(r"^{}=.*".format(key), "{}={}".format(key, data[k]), env, flags=re.MULTILINE)
        env_path.write_text(env, encoding="utf-8")
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@router.get("/api/stats/day")
async def stats_day(day: int):
    from database import get_connection
from datetime import datetime
from config import settings
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active=1").fetchone()["c"]
        answered = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM answers WHERE day_seq=?", (day,)).fetchone()["c"]
        correct = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=? AND is_correct=1", (day,)).fetchone()["c"]
        total_q = conn.execute("SELECT COUNT(*) as c FROM answers WHERE day_seq=?", (day,)).fetchone()["c"]
        correct_rate = round(correct / total_q * 100, 1) if total_q > 0 else 0
        sql = "SELECT u.name, u.department as dept, SUM(CASE WHEN a.is_correct=1 THEN 1 ELSE 0 END) as correct, COUNT(a.id) as total FROM users u LEFT JOIN answers a ON u.id = a.user_id AND a.day_seq=? WHERE u.is_active=1 GROUP BY u.id ORDER BY u.name"
        users_rows = conn.execute(sql, (day,)).fetchall()
    finally:
        conn.close()
    return JSONResponse({
        "total_users": total,
        "answered_users": answered,
        "correct_rate": correct_rate,
        "users": [dict(u) for u in users_rows],
    })
