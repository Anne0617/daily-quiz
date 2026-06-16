import json
import time
from pathlib import Path
from openai import OpenAI
from config import settings
from models import save_daily_content, save_question, publish_content


def extract_text_from_pdfs(pdf_dir: str) -> list[dict]:
    try:
        import pdfplumber
    except ImportError:
        print("请先安装 pdfplumber: pip install pdfplumber")
        return []

    pdf_dir_obj = Path(pdf_dir)
    if not pdf_dir_obj.exists():
        print(f"PDF 目录不存在: {pdf_dir}")
        return []

    pdf_files = sorted(pdf_dir_obj.glob("*.pdf"))
    if not pdf_files:
        print(f"未找到 PDF 文件: {pdf_dir}")
        return []

    pages = []
    for pdf_path in pdf_files:
        print(f"提取: {pdf_path.name}")
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    pages.append({"source": pdf_path.name, "page": i + 1, "text": text.strip()})
    print(f"共提取 {len(pages)} 页有效内容")
    return pages


def ai_generate_quiz(client: OpenAI, chunk: dict, day_seq: int) -> tuple:
    prompt = f'''你是一个企业培训题库生成专家。请根据以下规划文档内容，生成一套完整的每日学习材料。

要求：
1. 生成 5 条知识点（每条约 50-80 字，简明扼要）
2. 基于这些知识点出 5 道选择题（A/B/C/D 四选一，有唯一正确答案）
3. 题目贴合实际、带有一定辨析度，不能太简单
4. 每题附带正确答案解析（30-50 字）

严格按照以下 JSON 格式输出，不要加任何多余的文字：
{{
    "knowledge_points": ["知识点1", "知识点2", "知识点3", "知识点4", "知识点5"],
    "questions": [
        {{
            "text": "题目文字",
            "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},
            "correct_answer": "A",
            "explanation": "为什么选这个"
        }}
    ]
}}

文档内容（来自 {chunk["source"]} 第 {chunk["page"]} 页）：
{chunk["text"]}
'''
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=2000,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            data = json.loads(content)
            kps = data.get("knowledge_points", [])
            questions = data.get("questions", [])
            if len(kps) < 3 or len(questions) < 3:
                print(f"  [重试] 生成内容不足: {len(kps)} KP, {len(questions)} Q")
                continue
            kps = (kps * 5)[:5]
            questions = (questions * 5)[:5]
            for i, q in enumerate(questions):
                q.setdefault("options", {{"A": "是", "B": "否", "C": "不确定", "D": "以上都不对"}})
                q.setdefault("correct_answer", "A")
                q.setdefault("explanation", "")
            return kps, questions
        except Exception as e:
            print(f"  [重试 {attempt+1}/3] API 错误: {e}")
            time.sleep(3)
    return [], []


def process_all_pdfs(day_offset: int = 0, auto_publish: bool = False):
    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    if not settings.deepseek_api_key:
        print("错误: 未配置 DEEPSEEK_API_KEY")
        return

    pages = extract_text_from_pdfs(settings.pdf_dir)
    if not pages:
        print("没有提取到内容，请检查 data/pdfs/ 目录")
        return

    for idx, page in enumerate(pages):
        day_seq = day_offset + idx + 1
        print(f"\n=== 生成第 {day_seq} 天内容 ({page['source']} p.{page['page']}) ===")
        kps, questions = ai_generate_quiz(client, page, day_seq)
        if not kps:
            print(f"  跳过第 {day_seq} 天")
            continue
        save_daily_content(day_seq, kps)
        for i, q in enumerate(questions):
            save_question(day_seq, i + 1, q["text"], q["options"], q["correct_answer"], q.get("explanation", ""), page["source"])
        if auto_publish:
            publish_content(day_seq)
            print(f"  第 {day_seq} 天已发布")
        else:
            print(f"  第 {day_seq} 天已保存为草稿")

    print(f"\n完成！共处理 {len(pages)} 页")


def list_drafts():
    from models import get_pending_days
    days = get_pending_days()
    if not days:
        print("没有待审核的草稿")
        return
    print(f"待审核天数: {len(days)}")
    for d in days:
        print(f"  第 {d} 天")


def publish(day_seq: int):
    publish_content(day_seq)
    print(f"第 {day_seq} 天已发布")


if __name__ == "__main__":
    import sys
    if "--list-drafts" in sys.argv:
        list_drafts()
    elif "--publish" in sys.argv:
        idx = sys.argv.index("--publish") + 1
        if idx < len(sys.argv):
            publish(int(sys.argv[idx]))
    else:
        offset = 0
        auto = "--auto-publish" in sys.argv
        if "--offset" in sys.argv:
            idx = sys.argv.index("--offset") + 1
            if idx < len(sys.argv):
                offset = int(sys.argv[idx])
        process_all_pdfs(day_offset=offset, auto_publish=auto)
