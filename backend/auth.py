import os
import hmac
import hashlib
import jwt
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from sqlalchemy.orm import Session
from database import Base

# Ключ теперь безопасно читается из файла .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Токен выдается на сутки


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)


def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    """Проверяет хэш данных от виджета Telegram"""
    if "hash" not in data:
        return False

    tg_hash = data.pop("hash")
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items()) if v is not None])

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(calculated_hash, tg_hash)


def create_access_token(data: dict):
    """Генерирует JWT-токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_or_create_user(db: Session, tg_id: int, first_name: str, last_name: str = None) -> User:
    """Ищет пользователя в БД, а если его нет — создаёт нового"""
    user = db.query(User).filter(User.telegram_id == tg_id).first()

    if not user:
        full_name = first_name
        if last_name:
            full_name += f" {last_name}"

        user = User(telegram_id=tg_id, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user