from docx import Document
from docx.shared import Pt
from pathlib import Path
from pprint import pprint


def parser_docx(file_path):
    doc = Document(file_path)
    result = []
    
    for para in doc.paragraphs:
        # Собираем данные абзаца один раз
        p_fmt = para.paragraph_format
        para_data = {
            "alignment": str(p_fmt.alignment),
            "space_before": p_fmt.space_before.pt if p_fmt.space_before else 0.0,
            "space_after": p_fmt.space_after.pt if p_fmt.space_after else 0.0,
            "first_line": p_fmt.first_line_indent.cm if p_fmt.first_line_indent else 0.0,
            "line_spacing": p_fmt.line_spacing if p_fmt.line_spacing else 1.0
        }
        
        for run in para.runs:
            text = run.text.strip()
            if not text: continue

            # Формируем полный объект данных
            chunk = {
                "text": text,
                "font": run.font.name or 'Times New Roman', # Чаще всего дефолт такой
                "size": run.font.size.pt if run.font.size else 12.0, # Ставим дефолт числом
                **para_data # Подмешиваем данные абзаца в каждый run
            }
            result.append(chunk)
            
    return result