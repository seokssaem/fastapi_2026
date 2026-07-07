# bus/database.py
"""
PostgreSQL 연결 및 세션 관리
P07 노트북과 동일한 DB_URL 사용 (DB명: busapidb, 비밀번호: 1234)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_URL = "postgresql://postgres:1234@localhost:5432/busapidb"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("[database] bus_stop 테이블 준비 완료 (정류소ID 기본키)")


def get_session():
    return SessionLocal()


if __name__ == "__main__":
    init_db()
