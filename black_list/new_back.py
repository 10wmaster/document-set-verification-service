from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

app = FastAPI(title="OHS Document Verification Service Suite")


class DocumentChunk(BaseModel):
    text: str
    font: str
    size: float
    # Поля от DOCX-парсера
    alignment: Optional[str] = None
    first_line: Optional[float] = 0.0
    line_spacing: Optional[float] = 1.0
    # Поля от PDF-парсера
    page: Optional[int] = None
    is_bold: Optional[bool] = False


class ValidationRequest(BaseModel):
    doc_type: str  # "instruction", "journal", "package_checklist"
    document_data: List[DocumentChunk]
    uploaded_package_types: Optional[List[str]] = None



def normalize_font(font_name: str) -> str:
    f = font_name.lower()
    if "+" in f: f = f.split("+")[-1]
    if "timesnewroman" in f or "times-roman" in f: return "times new roman"
    if "arial" in f: return "arial"
    return f



# Модуль А: Нормоконтроль оформления (ГОСТ Р 7.0.97-2016)
def check_gost_7_0_97(chunks: List[DocumentChunk]) -> List[str]:
    errors = []
    target_font = "times new roman"
    target_size = 14.0

    for idx, chunk in enumerate(chunks):
        if len(chunk.text) < 3: continue

        if target_font not in normalize_font(chunk.font):
            errors.append(
                f"[Элемент {idx}] Нестандартный шрифт: '{chunk.font}' в тексте '{chunk.text[:20]}...' (Ожидается: Times New Roman)")

        if chunk.size < 12.0 or chunk.size > 14.0:
            errors.append(f"[Элемент {idx}] Нарушение размера шрифта: {chunk.size}pt (Допускается от 12 до 14 по ГОСТ)")

        if chunk.first_line and abs(chunk.first_line - 1.25) > 0.05 and chunk.first_line != 0.0:
            errors.append(
                f"[Элемент {idx}] Неверный отступ первой строки: {chunk.first_line} см (По ГОСТ требуется 1.25 см)")

    return errors


# Модуль Б: Проверка структуры Инструкции (Приказ Минтруда № 772н)
def check_order_772n(chunks: List[DocumentChunk]) -> List[str]:
    errors = []
    full_text = " ".join([c.text.lower() for c in chunks])

    required_chapters = {
        "общие требования": "Общие требования охраны труда",
        "перед началом работы": "Требования охраны труда перед началом работы",
        "во время работы": "Требования охраны труда во время работы",
        "в аварийных ситуациях": "Требования охраны труда в аварийных ситуациях",
        "по окончании работы": "Требования охраны труда по окончании работы"
    }

    for key, original_name in required_chapters.items():
        if key not in full_text:
            errors.append(f"Критическая ошибка: В инструкции отсутствует обязательный раздел '{original_name}'")

    return errors


# Модуль В: Контроль реквизитов и дат в журналах (ГОСТ 12.0.004-2015 + Пост. 2464)
def check_journal_and_dates(chunks: List[DocumentChunk]) -> List[str]:
    errors = []
    full_text = " ".join([c.text.lower() for c in chunks])

    required_fields = ["фио", "дата", "подпись", "инструктаж"]
    for field in required_fields:
        if field not in full_text:
            errors.append(
                f"Ошибка формы ГОСТ 12.0.004: На странице/в таблице не найден обязательный столбец или поле '{field.upper()}'")

    for chunk in chunks:

        if len(chunk.text) == 10 and chunk.text.count(".") == 2:
            try:
                doc_date = datetime.strptime(chunk.text, "%d.%m.%Y")
                if datetime.now() - doc_date > timedelta(days=180):
                    errors.append(
                        f"Контроль дат: Инструктаж от {chunk.text} просрочен! Периодичность прохождения (6 мес.) нарушена.")
            except ValueError:
                continue

    return errors


# Модуль Г: Оценка полноты комплекта документов СУОТ (ГОСТ 12.0.230-2007)
def check_package_completeness(uploaded_types: List[str]) -> Dict[str, Any]:
    mandatory_package = ["Политика СУОТ", "Инструкции по профессиям", "Журнал инструктажей", "Программа обучения"]
    missing = [doc for doc in mandatory_package if doc not in uploaded_types]

    status = "Соответствует" if not missing else "Не соответствует"
    compliance_score = int(((len(mandatory_package) - len(missing)) / len(mandatory_package)) * 100)

    return {
        "status": status,
        "compliance_score_percent": compliance_score,
        "missing_documents": missing,
        "recommendation": "Загрузите недостающие документы для успешного прохождения проверки ГИТ." if missing else "Комплект готов к проверке."
    }



@app.post("/api/v1/verify")
async def verify_document(request: ValidationRequest):
    all_errors = []

    # Сценарий 1: Проверка Инструкции
    if request.doc_type == "instruction":
        gost_errors = check_gost_7_0_97(request.document_data)
        order_errors = check_order_772n(request.document_data)
        all_errors.extend(gost_errors)
        all_errors.extend(order_errors)

        return {
            "document_type": "Инструкция по охране труда",
            "status": "Violation" if all_errors else "Success",
            "total_errors": len(all_errors),
            "errors": all_errors
        }

    # Сценарий 2: Проверка Журналов / Протоколов
    elif request.doc_type == "journal":
        journal_errors = check_journal_and_dates(request.document_data)
        return {
            "document_type": "Журнал / Протокол учета инструктажей",
            "status": "Violation" if journal_errors else "Success",
            "total_errors": len(journal_errors),
            "errors": journal_errors
        }

    # Сценарий 3: Имитация аудита комплекта СУОТ
    elif request.doc_type == "package_checklist":
        if not request.uploaded_package_types:
            raise HTTPException(status_code=400, detail="Не передан список загруженных типов документов")
        result = check_package_completeness(request.uploaded_package_types)
        return result

    else:
        raise HTTPException(status_code=400, detail="Неизвестный тип документа")