import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('\"')
            if key and not os.environ.get(key):
                os.environ[key] = value


_load_dotenv()


@dataclass
class Settings:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    base_url: str = os.getenv("BASE_URL", "http://localhost:8080")
    wecom_webhook_url: str = os.getenv("WECOM_WEBHOOK_URL", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    db_path: str = os.getenv("DB_PATH", "data/content.db")
    pdf_dir: str = os.getenv("PDF_DIR", "data/pdfs")
    user_list_file: str = os.getenv("USER_LIST_FILE", "user_list/managers.xlsx")
    report_output_dir: str = os.getenv("REPORT_OUTPUT_DIR", "data/reports")
    push_time: str = os.getenv("PUSH_TIME", "09:00")
    week_report_day: int = int(os.getenv("WEEK_REPORT_DAY", "1"))
    month_report_day: int = int(os.getenv("MONTH_REPORT_DAY", "1"))
    admin_mention: str = os.getenv("ADMIN_MENTION", "")
    stats_time: str = os.getenv("STATS_TIME", "18:00")
    reminder_time: str = os.getenv("REMINDER_TIME", "16:00")
    reminder_day: int = int(os.getenv("REMINDER_DAY", "5"))
    wecom_group_name: str = os.getenv("WECOM_GROUP_NAME", "")


settings = Settings()
