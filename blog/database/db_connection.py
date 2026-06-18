from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 데이터베이스 연결 정보 설정
DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/blogdb"

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 팩토리 생성
SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

# 세션 생성
def get_session():
    with SessionFactory() as session:
        yield session