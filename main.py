from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from python_multipart import*
from parser import parser_docx
import uvicorn, shutil, os


app = FastAPI()



@app.get("/")
def home():
    return {"message": "Сервер да"}
    
@app.post("/upload-docs")
async def handle_upload(files: List[UploadFile] = File(...)):
    DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PDF_TYPE = "application/pdf"

    if file.content_type != DOCX_TYPE and file.content_type != PDF_TYPE:
        raise HTTPException(status_code=400, detail="Этот формат документа не поддерживается")
    
    all_results = []
    
    for file in files:
        #  создание путь
        file_path = os.path.join("uploads", f"saved_{file.filename}")
        
        # сохранение файла на диске 
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # вызов парсера
        parsed_data = parser_docx(file_path) 
        
        # результаты в один список
        all_results.append({
            "filename": file.filename,
            "data": parsed_data
        })
    
    return {"results": all_results}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)