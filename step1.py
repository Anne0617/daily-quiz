import os
os.environ["DEEPSEEK_API_KEY"] = "sk-f76d44f5c99c4d8fbcd010bfe9741496"

from content_processor import extract_text_from_pdfs
from config import settings

pages = extract_text_from_pdfs(settings.pdf_dir)
print(f"共 {len(pages)} 页有效内容")
for p in pages[:3]:
    print(f"  {p['source']} p.{p['page']}: {len(p['text'])} 字")
