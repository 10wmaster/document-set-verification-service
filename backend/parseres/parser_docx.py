from docx import Document
import requests
from pprint import pprint

def parser_docx(file_path):
    doc = Document(file_path)
    result = []
    for para in doc.paragraphs:
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
            chunk = {
                "text": text,
                "font": run.font.name or 'Times New Roman',
                "size": run.font.size.pt if run.font.size else 12.0,
                **para_data
            }
            result.append(chunk)
    return result

# def check_document_online(file_path, gost_name):
#     print(f"Парсинг файла {file_path}...")
#     data = parser_docx(file_path)
#     payload = {
#         "gost_name": gost_name,
#         "document_data": data
#     }
#     url = "http://127.0.0.1:8001/check"
#     try:
#         response = requests.post(url, json=payload)
#         if response.status_code == 200:
#             print("\n--- РЕЗУЛЬТАТ ПРОВЕРКИ ---")
#             pprint(response.json())
#         else:
#             print(f"Ошибка сервера: {response.status_code}")
#             print(response.text)
#     except requests.exceptions.ConnectionError:
#         print("ОШИБКА: Сервер не запущен! Сначала запусти uvicorn в другом терминале.")

# if __name__ == "__main__":
#     file_to_check = "../test.docx"
#     check_document_online(file_to_check, "ГОСТ_7.32")