from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    tablename = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
