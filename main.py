import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Модель данных (чертеж нашей задачи)
class Item(BaseModel):
    id: Optional[int] = None
    text: str
    is_done: bool = False

# Наша импровизированная "база данных" в оперативной памяти
items_db: List[Item] = []

# --- READ (Получить всё или один элемент) ---

@app.get("/items", response_model=List[Item])
def get_all_items():
    """Возвращает весь список задач"""
    return items_db

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """Возвращает одну задачу по её ID (индексу)"""
    if item_id < 0 or item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return items_db[item_id]

# --- CREATE (Создать новую запись) ---

@app.post("/items", response_model=Item)
def create_item(item: Item):
    """Добавляет новую задачу в список"""
    # Присваиваем ID на основе текущей длины списка
    item.id = len(items_db)
    items_db.append(item)
    return item

# --- UPDATE (Обновить существующую запись) ---

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    """Полностью заменяет задачу с указанным ID"""
    if item_id < 0 or item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Нечего обновлять")
    
    updated_item.id = item_id
    items_db[item_id] = updated_item
    return updated_item

# --- DELETE (Удалить запись) ---

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """Удаляет задачу из списка"""
    if item_id < 0 or item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Невозможно удалить: ID не найден")
    
    deleted_item = items_db.pop(item_id)
    return {"message": f"Задача '{deleted_item.text}' удалена"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)