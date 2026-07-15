"""PostgreSQL database configuration for SQLAlchemy 2.0 examples."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:1234@localhost:5432/swc_api",
)

# pool_pre_ping은 풀에서 꺼낸 PostgreSQL 연결이 살아 있는지 먼저 확인한다.
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# SQLAlchemy 2.0에서는 autocommit 모드를 사용하지 않는다. commit/rollback으로
# 트랜잭션 경계를 명시하고, autoflush=False로 수업 중 flush 시점을 예측 가능하게 둔다.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """모든 ORM 모델이 상속하는 SQLAlchemy 2.0 선언적 기준 클래스."""

    pass