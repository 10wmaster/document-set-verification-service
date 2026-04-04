import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from parsers import extract_docx_data

app = FastAPI()

UPLOAD_DIR= "uploads"
os.makedirs(UPLOAD_DIR,exist_ok=True)

@app.get("/")
def read_root():
    return{"message":"Сервис проверки документов"}

@app.post("/upload/")
async def upload_document(files: list[UploadFile]=File(...)):
    saved_files= []

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)