from docx import Document
from docx.shared import Pt
from pathlib import Path
from pprint import pprint

def parser_pdf(file_path):
    pass

def parser_docx(file_path):
    doc = Document(file_path)
    result = []
    
    # Храним состояние, чтобы не дублировать информацию
    last_state = {
        "font_name": None,
        "font_size": None,
        "alignment": None,
        "space_after": None,
        "space_before": None,
        "first_line": None,
        "line_spacing": None
    }

    for para in doc.paragraphs:
        # выравнивание, пробел до/после, красная строка один раз для всего абзаца
        current_alignment = para.paragraph_format.alignment
        current_space_before = para.paragraph_format.space_before.pt if para.paragraph_format.space_before else 0.0
        current_space_after = para.paragraph_format.space_after.pt if para.paragraph_format.space_after else 0.0
        current_first_line = para.paragraph_format.first_line_indent.cm if para.paragraph_format.first_line_indent else 0.0
        current_line_spacing = para.paragraph_format.line_spacing
        
        for run in para.runs:
            text = run.text.strip()
            if not text:
                continue

            # Определяем шрифт и размер
            f_name = run.font.name or 'По умолчанию'
            f_size = run.font.size.pt if run.font.size else 'По умолчанию'
            
            # Создаем "пакет" данных для этого кусочка текста
            chunk = {}
            
            # Добавляем инфо о шрифте, только если он изменился
            if f_name != last_state["font_name"] or f_size != last_state["font_size"]:
                chunk["font"] = f_name
                chunk["size"] = f_size
                last_state["font_name"] = f_name
                last_state["font_size"] = f_size
            
            #выравнивание
            if current_alignment != last_state["alignment"]:
                chunk["alignment"] = str(current_alignment) # Превращаем Enum в строку
                last_state["alignment"] = current_alignment
            
            #отступ после
            if current_space_before != last_state["space_before"]:
                chunk["space_before"] = str(current_space_before)
                last_state["space_before"] = current_space_before

            #отступ до
            if current_space_after != last_state["space_after"]:
                chunk["space_after"] = str(current_space_after)
                last_state["space_after"] = current_space_after

            #красная строка
            if current_first_line != last_state["first_line"]:
                chunk["first_line"] = str(current_first_line)
                last_state["first_line"] = current_first_line

            #межстрочный интервал
            if current_line_spacing != last_state["line_spacing"]:
                chunk["line_spacing"] = str(current_line_spacing)
                last_state["line_spacing"] = current_line_spacing
            
            chunk["text"] = text
            result.append(chunk)
            
    return result


folder_path = Path("uploads")

for file in folder_path.iterdir():
    if file.is_file and file.suffix == ".docx":
        pprint(parser_docx(file), indent=6, width=90)
    # else:
    #     #parser_pdf(file)