from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from models import get_today_content, add_user, get_user_by_name, submit_answers
from database import get_connection

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
