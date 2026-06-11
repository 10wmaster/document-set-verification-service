import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 1. Вычисляем директории относительно расположения main.py
BASE_DIR = Path(__file__).resolve().parent  # Папка backend/
ROOT_DIR = BASE_DIR.parent  # Корневая папка проекта

# 2. Очищаем кэш и принудительно загружаем .env (сначала из backend, затем из корня)
ENV_IN_BACKEND = BASE_DIR / ".env"
ENV_IN_ROOT = ROOT_DIR / ".env"

if ENV_IN_BACKEND.exists():
    load_dotenv(dotenv_path=ENV_IN_BACKEND, override=True)
    ENV_PATH_USED = ENV_IN_BACKEND
elif ENV_IN_ROOT.exists():
    load_dotenv(dotenv_path=ENV_IN_ROOT, override=True)
    ENV_PATH_USED = ENV_IN_ROOT
else:
    ENV_PATH_USED = None

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN or BOT_TOKEN == "ТВОЙ_ТОКЕН_БОТА":
    BOT_TOKEN = "СЮДА_МОЖНО_ВСТАВИТЬ_ТОКЕН_ЕСЛИ_ОШИБКА_500_ОСТАЕТСЯ"

# ПЛАШКА ОТЛАДКИ В КОНСОЛЬ
print("\n" + "=" * 50)
print(" СТАТУС КОНФИГУРАЦИИ ОКРУЖЕНИЯ ")
print(f"Используемый файл конфигурации: {ENV_PATH_USED}")
print(f"Загруженный токен бота: {BOT_TOKEN[:15] if BOT_TOKEN else 'None'}...")
print("=" * 50 + "\n")

# 3. Импортируем остальные модули системы
from parseres.back_and_parsers import router as verify_router
from auth import verify_telegram_auth, create_access_token

app = FastAPI(
    title="OHS Expert Compliance Service API",
    description="Сервис экспресс-аудита ЛНА по охране труда"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/auth/telegram", summary="Авторизация через Telegram")
async def telegram_auth(data: dict):
    # Берем токен, который мы гарантированно проинициализировали выше
    global BOT_TOKEN

    if not BOT_TOKEN or BOT_TOKEN.startswith("СЮДА_МОЖНО"):
        raise HTTPException(
            status_code=500,
            detail="Ошибка бэкенда: Токен бота не задан. Заполните .env или строку BOT_TOKEN в main.py"
        )

    # Проверка криптографической подписи от Telegram
    is_valid = verify_telegram_auth(data, BOT_TOKEN)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Неверная подпись Telegram. Доступ запрещен.")

    # Генерация JWT
    access_token = create_access_token({"sub": str(data.get("id"))})

    return {
        "success": True,
        "token": access_token,
        "user_name": data.get("first_name")
    }


# Подключаем роутер проверок
app.include_router(verify_router)

# Раздача статики фронтенда
FRONTEND_DIR = ROOT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=9001, reload=True)