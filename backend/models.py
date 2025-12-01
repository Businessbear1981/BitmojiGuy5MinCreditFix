from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./bitmoji_credit.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class CreditSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    locked = Column(Boolean, default=True)
    cypher_token = Column(String, index=True)
    letters_path = Column(String)
    preview_summary = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
