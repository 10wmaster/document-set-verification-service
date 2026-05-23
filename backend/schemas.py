from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str

class TokenSchema(BaseModel):
    token: str

class DocumentStats(BaseModel):
    critical_errors: int
    warnings: int
    verified_pages: int

class GostResult(BaseModel):
    name: str
    status: str
    details: str

class VerificationResponse(BaseModel):
    success: bool
    filename: str
    score: int
    stats: DocumentStats
    gosts: List[GostResult]

    class Config:
        from_attributes = True