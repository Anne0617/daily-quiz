import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings
from database import init_db

app = FastAPI(title="星河十五五规划考试系统", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

from quiz_routes import router as quiz_router
app.include_router(quiz_router)


@app.on_event("startup")
async def startup():
    init_db()
    print(f"服务已启动: http://{settings.host}:{settings.port}")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
