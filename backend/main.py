from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import os
import jwt
import time
import io
import hashlib
import hmac
from dotenv import load_dotenv

import models
import schemas
from database import engine, get_db

# Загрузка конфигурации окружения
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Сервис нормоконтроля документов по ГОСТ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация переданных тобой ключей безопасности
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "your_bot_username")
ALGORITHM = "HS256"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(FRONTEND_DIR, exist_ok=True)


# ИБ-Валидация: Проверка подлинности данных от Telegram через HMAC-SHA256
def verify_telegram_signature(data: dict, bot_token: str) -> bool:
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # Формируем строку данных для проверки (сортируем по алфавиту, исключаем hash)
    check_list = [f"{k}={v}" for k, v in data.items() if k != "hash" and v is not None]
    check_list.sort()
    data_check_string = "\n".join(check_list)

    # Вычисляем секретный ключ на основе токена бота
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    # Вычисляем контрольный HMAC-хэш
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(calculated_hash, received_hash)


@app.get("/api/config")
async def get_config():
    return {"tg_bot_username": TELEGRAM_BOT_USERNAME}


@app.post("/api/auth", response_model=schemas.TokenSchema)
async def telegram_auth(data: schemas.TelegramAuthData, db: Session = Depends(get_db)):
    # Запускаем строгую валидацию подписи данных
    auth_dict = data.model_dump()
    if not verify_telegram_signature(auth_dict, BOT_TOKEN):
        raise HTTPException(status_code=401, detail="Криптографическая проверка подписи Telegram провалена")

    # Защита от старых атак повторного воспроизведения (Replay Attack)
    if time.time() - data.auth_date > 86400:
        raise HTTPException(status_code=400, detail="Срок действия сессии авторизации истек")

    user = db.query(models.User).filter(models.User.telegram_id == str(data.id)).first()
    if not user:
        user = models.User(
            telegram_id=str(data.id),
            username=data.username or data.first_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = jwt.encode({"sub": str(user.id), "exp": time.time() + 3600}, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token}


@app.post("/api/upload", response_model=schemas.VerificationResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.docx', '.pdf')):
        raise HTTPException(status_code=400, detail="Разрешены только файлы форматов .docx и .pdf")

    await file.read()

    mock_gosts = [
        {"name": "ГОСТ Р 7.0.97 (Оформление)", "status": "warning",
         "details": "Обнаружен неверный шрифт в заголовках разделов (ожидался Times New Roman, 14pt)."},
        {"name": "ГОСТ Р 7.0.11 (Диссертации)", "status": "success",
         "details": "Структура элементов титульного листа и реферата полностью соответствует норме."},
        {"name": "ГОСТ 7.32 (Отчет о НИР)", "status": "error",
         "details": "Абзацный отступ на страницах 4, 7 и 9 составляет 1.5 см вместо положенных по стандарту 1.25 см."},
        {"name": "ГОСТ 2.105 (Общие требования)", "status": "error",
         "details": "Нарушена сквозная нумерация формул во второй главе. Пропущен номер (2.3)."},
        {"name": "ГОСТ Р 7.0.5 (Ссылки)", "status": "success",
         "details": "Библиографические ссылки и затекстовый список литературы оформлены корректно."}
    ]

    mock_stats = {"critical_errors": 2, "warnings": 1, "verified_pages": 15}

    db_record = models.DocumentRecord(filename=file.filename, score=82, stats=mock_stats, gosts_data=mock_gosts,
                                      user_id=1)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return {
        "success": True,
        "filename": db_record.filename,
        "score": db_record.score,
        "stats": db_record.stats,
        "gosts": db_record.gosts_data
    }


@app.get("/api/report/download")
async def download_report():
    buffer = io.BytesIO()
    report_text = "%PDF-1.4 \n % Полный сгенерированный отчет нормоконтроля для предзащиты UrFU"
    buffer.write(report_text.encode('utf-8'))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=gost_report.pdf"})


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/results")
async def read_results():
    return FileResponse(os.path.join(FRONTEND_DIR, "results.html"))