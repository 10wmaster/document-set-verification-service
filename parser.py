import re
import pdfplumber
from docx import Document

def get_docx_text(path):
    doc = Document(path)
    # Собираем текст из абзацев и таблиц
    return "\n".join([p.text for p in doc.paragraphs] + 
                     [cell.text for t in doc.tables for r in t.rows for cell in r.cells])

def get_pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def identify_and_parse(file_path: str):
    """Определяет тип файла и извлекает данные"""
    ext = file_path.lower().split('.')[-1]
    text = ""

    # 1. Выбираем инструмент в зависимости от расширения
    if ext == "docx":
        text = get_docx_text(file_path)
    elif ext == "pdf":
        text = get_pdf_text(file_path)
    else:
        return {"error": "Unsupported format"}

    # 2. Определяем ТИП документа по ключевым словам
    doc_type = "unknown"
    content = text.upper()
    
    if "ТИТУЛЬНЫЙ ЛИСТ" in content or "МИНИСТЕРСТВО" in content:
        doc_type = "title_page"
    elif "АНТИПЛАГИАТ" in content or "ЗАИМСТВОВАНИЙ" in content:
        doc_type = "antiplagiat_report"
    elif "ОТЗЫВ" in content:
        doc_type = "supervisor_review"

    return {
        "doc_type": doc_type,
        "raw_text_preview": text[:200], # Показываем первые 200 символов для проверки
        "length": len(text)
    }