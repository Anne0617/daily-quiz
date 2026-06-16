import os
os.environ["DEEPSEEK_API_KEY"] = "sk-f76d44f5c99c4d8fbcd010bfe9741496"
from content_processor import process_all_pdfs
process_all_pdfs(auto_publish=True)
