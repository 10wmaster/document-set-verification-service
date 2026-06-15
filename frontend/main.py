"""
Тестовый сервер OHS Expert Compliance API
Для демонстрации работы фронтенда и проверки API

Запуск: python main.py
После запуска:
- Фронтенд: http://127.0.0.1:9001/
- API: http://127.0.0.1:9001/api/v1/verify/expert
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="OHS Expert Compliance API", version="1.0.0")

# Получаем директорию где лежит main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============== Модели данных ==============

class DocumentElement(BaseModel):
    text: str
    font: str
    size: int
    page: int


class VerifyRequest(BaseModel):
    doc_type: str  # "instruction" или "journal"
    document_data: List[DocumentElement]


class Violation(BaseModel):
    category: str
    severity: str  # "CRITICAL", "WARNING", "RECOMMEND"
    message: str
    location: str
    legal_tip: str


class VerifyResponse(BaseModel):
    status: str
    analyzed_at: str
    total_errors: int
    compliance_percent: int
    critical_errors: int
    warnings: int
    recommendations: int
    passed_checks: int
    violations: List[Violation]


# ============== Валидация (упрощённая) ==============

def validate_instruction(elements: List[DocumentElement]) -> List[Violation]:
    """Проверка инструкции по Приказу 772н"""
    violations = []
    text_all = " ".join([e.text for e in elements]).lower()
    
    # Обязательные разделы
    required_sections = [
        ("общие требования охраны труда", "Раздел 'Общие требования охраны труда'"),
        ("требования охраны труда перед началом работы", "Раздел 'Требования охраны труда перед началом работы'"),
        ("требования охраны труда во время работы", "Раздел 'Требования охраны труда во время работы'"),
        ("требования охраны труда в аварийных ситуациях", "Раздел 'Требования охраны труда в аварийных ситуациях'"),
        ("требования охраны труда по окончании работы", "Раздел 'Требования охраны труда по окончании работы'"),
    ]
    
    for pattern, name in required_sections:
        if pattern not in text_all:
            violations.append(Violation(
                category="Структура (Приказ 772н)",
                severity="CRITICAL",
                message=f"Отсутствует обязательный раздел: '{name}'",
                location="Structures",
                legal_tip=f"Добавьте в документ главу '{name}'"
            ))
    
    # Проверка шрифта
    for el in elements:
        if el.font.lower() not in ["times new roman", "arial"]:
            violations.append(Violation(
                category="Оформление",
                severity="WARNING",
                message=f"Шрифт '{el.font}' не соответствует требованиям",
                location=f"Страница {el.page}",
                legal_tip="Рекомендуется использовать Times New Roman"
            ))
        if el.size != 14:
            violations.append(Violation(
                category="Оформление",
                severity="WARNING",
                message=f"Размер шрифта {el.size} пт не соответствует требованиям (14 пт)",
                location=f"Страница {el.page}",
                legal_tip="Установите размер шрифта 14 пт"
            ))
    
    return violations


def validate_journal(elements: List[DocumentElement]) -> List[Violation]:
    """Проверка журнала по Постановлению 2464"""
    violations = []
    text_all = " ".join([e.text for e in elements]).lower()
    
    # Проверка на наличие данных
    if len(elements) < 2:
        violations.append(Violation(
            category="Структура (Постановление 2464)",
            severity="CRITICAL",
            message="Журнал пуст или содержит недостаточно записей",
            location="Content",
            legal_tip="Добавьте записи в журнал"
        ))
    
    # Проверка обязательных полей
    if "фио" not in text_all and "иванов" not in text_all:
        violations.append(Violation(
            category="Заполнение",
            severity="CRITICAL",
            message="Отсутствует поле 'ФИО' работника",
            location="Records",
            legal_tip="Добавьте ФИО работника в каждую запись"
        ))
    
    if "подпись" not in text_all:
        violations.append(Violation(
            category="Заполнение",
            severity="CRITICAL",
            message="Отсутствуют подписи работников",
            location="Signatures",
            legal_tip="Добавьте подписи в соответствующую графу"
        ))
    
    return violations


# ============== API эндпоинты ==============

@app.get("/")
def root():
    """Корневой эндпоинт — возвращает index.html"""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/index.css")
def css():
    """Стили главной страницы"""
    return FileResponse(os.path.join(BASE_DIR, "index.css"))


@app.get("/index.js")
def js():
    """JS главной страницы"""
    return FileResponse(os.path.join(BASE_DIR, "index.js"))


@app.get("/upload.html")
def upload_page():
    """Страница загрузки документа"""
    return FileResponse(os.path.join(BASE_DIR, "upload.html"))


@app.get("/upload_page.css")
def upload_css():
    """Стили страницы загрузки"""
    return FileResponse(os.path.join(BASE_DIR, "upload_page.css"))


@app.get("/upload_page.js")
def upload_js():
    """JS страницы загрузки"""
    return FileResponse(os.path.join(BASE_DIR, "upload_page.js"))


@app.get("/document.html")
def document_page():
    """Страница результатов"""
    return FileResponse(os.path.join(BASE_DIR, "document.html"))


# Раздаём изображения
@app.get("/логотип.png")
def logo():
    return FileResponse(os.path.join(BASE_DIR, "логотип.png"))


@app.get("/iconCarrier.png")
def icon_carrier():
    return FileResponse(os.path.join(BASE_DIR, "iconCarrier.png"))


@app.get("/api/health")
def health_check():
    """Проверка работоспособности API"""
    return {
        "service": "OHS Expert Compliance API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/verify/expert", response_model=VerifyResponse)
def verify_document(request: VerifyRequest):
    """
    Проверка документа на соответствие нормативным требованиям
    
    - **doc_type**: "instruction" — инструкция по охране труда (Приказ 772н)
    - **doc_type**: "journal" — журнал инструктажей (Постановление 2464)
    """
    
    # Валидация типа докум��нта
    if request.doc_type not in ["instruction", "journal"]:
        raise HTTPException(status_code=400, detail="doc_type must be 'instruction' or 'journal'")
    
    # Выбор функции валидации
    if request.doc_type == "instruction":
        violations = validate_instruction(request.document_data)
        base_checks = 5  # Обязательные разделы
    else:
        violations = validate_journal(request.document_data)
        base_checks = 3  # Обязательные поля
    
    # Расчёт статистики
    critical = len([v for v in violations if v.severity == "CRITICAL"])
    warnings = len([v for v in violations if v.severity == "WARNING"])
    recommends = len([v for v in violations if v.severity == "RECOMMEND"])
    total = len(violations)
    passed = max(0, base_checks * 2 - total)  # Упрощённая формула
    compliance = max(0, min(100, (passed / (passed + total + 1)) * 100))
    
    return VerifyResponse(
        status="PASSED" if total == 0 else "FAILED",
        analyzed_at=datetime.now().isoformat(),
        total_errors=total,
        compliance_percent=int(compliance),
        critical_errors=critical,
        warnings=warnings,
        recommendations=recommends,
        passed_checks=passed,
        violations=violations
    )


@app.get("/api/v1/dashboard/stats")
def get_stats():
    """Статистика проверок (демо-данные)"""
    return {
        "total_documents": 47,
        "passed_documents": 32,
        "failed_documents": 15,
        "compliance_rate": 68,
        "last_check": datetime.now().isoformat()
    }


@app.get("/api/v1/verify/export/{doc_type}")
def export_report(doc_type: str):
    """
    Экспорт отчёта в Excel (заглушка)
    В реальной версии здесь будет генерация Excel файла
    """
    if doc_type not in ["instruction", "journal"]:
        raise HTTPException(status_code=400, detail="doc_type must be 'instruction' or 'journal'")
    
    return {
        "message": f"Excel отчёт для {doc_type} готов",
        "download_url": f"/api/v1/verify/export/{doc_type}?format=excel",
        "note": "Полная версия с openpyxl доступна в backend/main.py"
    }


# ============== Запуск сервера ==============

if __name__ == "__main__":
    print("=" * 50)
    print("OHS Expert Compliance API — Тестовый сервер")
    print("=" * 50)
    print()
    print("Доступные страницы:")
    print("  Главная:       http://127.0.0.1:9001/")
    print("  Загрузка:      http://127.0.0.1:9001/upload.html")
    print("  Результаты:    http://127.0.0.1:9001/document.html")
    print()
    print("API эндпоинты:")
    print("  GET  /api/health           — Проверка работы")
    print("  POST /api/v1/verify/expert — Проверка документа")
    print("  GET  /api/v1/dashboard/stats — Статистика")
    print()
    print("=" * 50)
    
    uvicorn.run(app, host="127.0.0.1", port=9001)