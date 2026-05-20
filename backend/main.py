import os
import shutil
import uuid
import uvicorn
import jwt
from typing import List
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Загрузка скрытых переменных из .env
from dotenv import load_dotenv
load_dotenv()

# Импорты модулей проекта
import database
from auth import (
    User,
    create_access_token,
    get_or_create_user,
    verify_telegram_auth,
    ALGORITHM,
    SECRET_KEY
)
from database import get_db

# --- ИМПОРТИРУЕМ ОБА ПАРСЕРА ---
from parseres.parser_docx import parser_docx
from parseres.parser_pdf import parser_pdf

# Создание таблиц БД
database.Base.metadata.create_all(bind=database.engine)

BOT_TOKEN = os.getenv("BOT_TOKEN")
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Document Checker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dictionary_of_all_gosts = {
    "ГОСТ_12.0.004": {"size": 12.0, "font": "Times New Roman", "indent": 1.25},
    "ГОСТ_7.32": {"size": 14.0, "font": "Arial", "indent": 1.5},
}


class Item(BaseModel):
    text: str
    size: float
    font: str


class CheckRequest(BaseModel):
    gost_name: str
    document_data: List[Item]


def compliense_checker(document, rules):
    errors = []
    for chunk in document:
        if chunk["size"] != rules["size"]:
            errors.append(
                f"Ошибка размера в '{chunk['text'][:25]}...': у вас {chunk['size']}, а надо {rules['size']}"
            )
        if chunk["font"] != rules["font"]:
            errors.append(
                f"Ошибка шрифта в '{chunk['text'][:25]}...': у вас {chunk['font']}, а надо {rules['font']}"
            )
    return errors


def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Вы не авторизованы!")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Токен невалиден или истёк")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Загрузка документов</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #fafafa; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            input, button { margin: 10px 0; padding: 8px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; }
            .auth-block { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; text-align: center; }
            .hidden { display: none; }
            .tg-btn { display: inline-block; background: #54a9eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 16px; transition: background 0.2s; }
            .tg-btn:hover { background: #3b90ce; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="auth-block" id="authBlock">
                <h3>Авторизация для работы с системой</h3>
                <a id="tgAuthBtn" class="tg-btn" target="_self" href="https://oauth.telegram.org/auth?bot_id=8965622057&origin=http%3A%2F%2F127.0.0.1%3A8000%2F&embed=0">
                    Войти через Telegram
                </a>
            </div>

            <div id="mainInterface" class="hidden">
                <p>Статус: <strong id="userName" style="color: #28a745;"></strong></p>
                <h2>Загрузка документов на проверку ГОСТ</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" name="files" multiple accept=".docx,.pdf">
                    <br>
                    <button type="submit">Проверить файлы</button>
                </form>
                <div id="result" class="result">Результаты проверки появятся здесь...</div>
            </div>
        </div>

        <script>
            function showInterface(name) {
                document.getElementById('authBlock').classList.add('hidden');
                document.getElementById('mainInterface').classList.remove('hidden');
                document.getElementById('userName').innerText = name;
            }

            async function checkUrlParams() {
                const hashStr = window.location.hash;
                if (hashStr && hashStr.includes('tgAuthResult=')) {
                    try {
                        const base64Data = hashStr.split('tgAuthResult=')[1];
                        const decodedJson = atob(base64Data.replace(/-/g, '+').replace(/_/g, '/'));
                        const telegramUser = JSON.parse(decodedJson);

                        const response = await fetch('/auth/telegram', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(telegramUser)
                        });

                        if (response.ok) {
                            const data = await response.json();
                            localStorage.setItem('token', data.access_token);
                            localStorage.setItem('user_name', telegramUser.first_name || "Авторизован");
                            window.history.replaceState({}, document.title, "/");
                            showInterface(telegramUser.first_name || "Авторизован");
                        } else {
                            alert('Ошибка создания сессии на бэкенде!');
                        }
                    } catch (e) {
                        console.error("Ошибка парсинга токена Telegram:", e);
                    }
                }
            }

            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData();
                const files = document.querySelector('input[type="file"]').files;
                if (files.length === 0) {
                    alert("Пожалуйста, выберите файлы");
                    return;
                }
                for (let file of files) { formData.append('files', file); }

                const token = localStorage.getItem('token');
                document.getElementById('result').innerText = "Файлы обрабатываются парсером...";

                const response = await fetch('/upload-docs', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });
                const result = await response.json();
                document.getElementById('result').innerHTML = JSON.stringify(result, null, 2);
            };

            window.onload = () => {
                const token = localStorage.getItem('token');
                const savedName = localStorage.getItem('user_name');
                if (token) {
                    showInterface(savedName || "Авторизован (сессия активна)");
                } else {
                    checkUrlParams();
                }
            };
        </script>
    </body>
    </html>
    """


@app.post("/auth/telegram")
async def auth_telegram(user_data: dict, db: Session = Depends(get_db)):
    tg_id = user_data.get("id") or 12345678
    first_name = user_data.get("first_name") or "Пользователь"
    last_name = user_data.get("last_name") or ""

    user = get_or_create_user(
        db=db,
        tg_id=int(tg_id),
        first_name=first_name,
        last_name=last_name,
    )

    token_payload = {"sub": str(user.telegram_id), "name": user.full_name}
    token = create_access_token(token_payload)
    return {"status": "success", "access_token": token, "token_type": "bearer"}


@app.post("/upload-docs")
async def handle_upload(
        files: List[UploadFile] = File(...),
        current_user: dict = Depends(get_current_user),
):
    # ИЗМЕНЕНИЕ: Список разрешенных MIME-типов (Ворд и ПДФ)
    ALLOWED_TYPES = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/pdf"
    ]
    all_results = []

    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Файл {file.filename} должен быть формата .docx или .pdf"
            )

        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join("uploads", unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ИЗМЕНЕНИЕ: Динамический выбор парсера в зависимости от расширения файла
        if file.filename.lower().endswith(".docx"):
            parsed_data = parser_docx(file_path)
        elif file.filename.lower().endswith(".pdf"):
            parsed_data = parser_pdf(file_path)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат")

        rules = dictionary_of_all_gosts.get("ГОСТ_7.32")
        violations = compliense_checker(parsed_data, rules)

        status = "Success" if not violations else "Violation"
        all_results.append(
            {"filename": file.filename, "status": status, "errors": violations}
        )

    return {"results": all_results, "total_files": len(all_results)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)