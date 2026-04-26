from fastapi import FastAPI, File, UploadFile
from parser import parser_docx
import uvicorn

app = FastAPI()

class DocElement(BaseModel):
    text: str
    font: str
    size: float | str  # Может быть числом или строкой "По умолчанию"
    alignment: str | None


@app.get("/")
def home():
    return {"message": "Сервер да"}

@app.post("/upload-docs")
async def create_upload_file(file: UploadFile = File(...)):


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)