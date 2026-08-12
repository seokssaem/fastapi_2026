from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# TODO: 본인 PC의 PostgreSQL 접속 정보에 맞게 수정하세요.
DATABASE_URL = 'postgresql+psycopg2://postgres:1234@localhost:5432/tododb'

engine = create_engine(DATABASE_URL, echo=True)

SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def get_session():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
