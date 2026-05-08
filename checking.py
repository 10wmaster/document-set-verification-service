from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
app = FastAPI(title ="Document Checker")

dictionary_of_all_gosts = { "ГОСТ_12.0.004":
                                { "size": 12.0,
                                  "font": "Times New Roman",
                                  "indent": 1.25},
                            "ГОСТ_7.32":{"size": 14.0,
                                         "font": "Arial",
                                         "indent": 1.5}}
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
        if chunk["size"]!=rules["size"]:
            errors.append(f"Ошибка размера в '{chunk['text'][:25]}...': "
                f"у вас {chunk['size']}, а надо {rules['size']}")
        if chunk["font"]!=rules["font"]:
            errors.append(f"Ошибка шрифта в '{chunk['text'][:25]}...': "
                f"у вас {chunk['font']}, а надо {rules['font']}")
    return errors

@app.post("/check")
async def check_document(request: CheckRequest):
    rules =  dictionary_of_all_gosts.get(request.gost_name)
    if not rules:
        return {"status": "Error", "message": "Выбранный ГОСТ не поддерживается"}
    data_as_dicts = [item.dict() for item in request.document_data]
    violations = compliense_checker(data_as_dicts, rules)
    if not violations:
        return {"status": "Success", "message": "Документ соответствует ГОСТУ"}
    return {"status": "Violation", "count": len(violations), "errors": violations}


















