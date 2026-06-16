import json, time, os
os.environ["DEEPSEEK_API_KEY"] = "sk-f76d44f5c99c4d8fbcd010bfe9741496"

from database import init_db
init_db()

from content_processor import extract_text_from_pdfs
from config import settings
pages = extract_text_from_pdfs(settings.pdf_dir)

print(f"\n开始逐页处理，共 {len(pages)} 页...")

from openai import OpenAI
client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

from models import save_daily_content, save_question, publish_content

for idx, page in enumerate(pages):
    day_seq = idx + 1
    text = page["text"]
    
    prompt = f"""你是一个企业培训题库生成专家。请根据以下文档内容生成每日学习材料。

要求：
1. 生成 5 条知识点（每条 50-80 字）
2. 基于知识点出 5 道选择题（A/B/C/D 四选一）
3. 每题附带正确答案和简短解析

严格按以下 JSON 格式输出：
{{
    "knowledge_points": ["知识点1","知识点2","知识点3","知识点4","知识点5"],
    "questions": [
        {{"text":"题目","options":{{"A":"选项A","B":"选项B","C":"选项C","D":"选项D"}},"correct_answer":"A","explanation":"解析"}}
    ]
}}

文档内容（来自 {page["source"]} 第 {page["page"]} 页）：
{text}
"""
    
    print(f"\n第 {day_seq} 天 ({page['source']} p.{page['page']}) 处理中...")
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
        kps = (kps * 5)[:5]
        questions = (questions * 5)[:5]
        
        save_daily_content(day_seq, kps)
        for i, q in enumerate(questions):
            save_question(day_seq, i+1, q["text"], q["options"], q["correct_answer"], q.get("explanation",""), page["source"])
        publish_content(day_seq)
        print(f"  完成: {len(kps)} 知识点, {len(questions)} 题")
    except Exception as e:
        print(f"  失败: {e}")
        time.sleep(5)

print(f"\n全部完成！处理了 {len(pages)} 页")
