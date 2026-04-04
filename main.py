import os
import shutil
import uuid
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from parser import identify_and_parse

app = FastAPI(title="Document Checker API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Сервис проверки документов готов к работе"}

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    
    allowed_extensions = ('.pdf', '.docx')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail=f"Разрешены только форматы: {allowed_extensions}")

    safe_filename = f"{uuid.uuid4()}_{os.path.basename(file.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        background_tasks.add_task(cleanup_file, file_path)

        # 4. Парсинг
        analysis = identify_and_parse(file_path)
        
        return {
            "file": file.filename,
            "analysis": analysis,
            "message": "Файл успешно обработан"
        }

    except Exception as e:
        cleanup_file(file_path)
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)