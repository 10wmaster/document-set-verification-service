from fastapi.responses import HTMLResponse
from fastapi import FastAPI, UploadFile, HTTPException, Form, File
from typing import List
from parseres.parser_docx import parser_docx
import uvicorn, shutil, os
import uuid

os.makedirs("uploads", exist_ok=True)


app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Загрузка документов</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            input, button { margin: 10px 0; padding: 8px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            .result { margin-top: 20px; white-space: pre-wrap; background: #f5f5f5; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Загрузка нескольких документов</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" name="files" multiple accept=".docx,.pdf">
                <br>
                <button type="submit">Загрузить файлы</button>
            </form>
            <div id="result" class="result"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData();
                const files = document.querySelector('input[type="file"]').files;
                
                for (let file of files) {
                    formData.append('files', file);
                }
                
                const response = await fetch('/upload-docs', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML = JSON.stringify(result, null, 2);
            };
        </script>
    </body>
    </html>
    """
    
@app.post("/upload-docs")
async def handle_upload(files: List[UploadFile] = File(...)):
    DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PDF_TYPE = "application/pdf"
    
    all_results = []
    
    for file in files:
        # Проверка типа файла
        if file.content_type != DOCX_TYPE and file.content_type != PDF_TYPE:
            raise HTTPException(
                status_code=400, 
                detail=f"Файл {file.filename} имеет неподдерживаемый формат"
            )
        
        # Создание пути
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join("uploads", unique_name)
        
        # Сохранение файла
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Вызов парсера
        parsed_data = parser_docx(file_path)
        
        all_results.append({
            "filename": file.filename,
            "data": parsed_data
        })
    
    return {"results": all_results, "total_files": len(all_results)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)