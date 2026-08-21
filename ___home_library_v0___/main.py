'''
home_library_v0/main.py
-----------------------------
예광탄 방식을 활용한 아주 얇은 코드
main에 라우터 기능 등 모두 넣을 예정
'''
from pathlib import Path
from fastapi import Depends, FastAPI, File, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Book

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

# models.py에서 정의한 Book, ReadingStatus, Review 클래스틀을 실제 PostgreSQL 테이블로 생성하는 역할
# (이미 테이블이 있으면 넘어가고, 없으면 새로 만든다.)
Base.metadata.create_all(engine)

# FastAPI 앱 객체 생성, title--> /docs(스웨거 문서)에서 화면 상단에 표시될 이름
app = FastAPI(title='우리집 책장 API')

# ------------------------------------------------------------
# POST /books/scan --> 사진을 업로드해서 책 한권을 등록하는 API
# ------------------------------------------------------------
@app.post('/books/scan', status_code=status.HTTP_201_CREATED)
def scam_book(image: UploadFile = File(...), db:Session = Depends(get_db)):
    # uploads 폴더 밑에 "원래 업로드 된 파일명"으로 저장 경로를 만든다
    path = UPLOAD_DIR / image.filename

    # image.file.read() --> 업로드 된 파일의 실제 바이트 내용을 읽어온다.
    # path.write_bytes(...) --> 그 바이트를 위에서 만든 경로에 실제 파일로 저장
    path.write_bytes(image.file.read())

    book = Book(title='테스트북(임시)', cover_path=str(path), recognition_status='confirmed')

    db.add(book)   # 이 책 데이터 저장 대기열에 올린다. (아직 DB에 실제로 사용되지는 않는다.)
    db.commit()   # 대기열에 올린 내용을 실제로 DB에 확정 저장
    db.refresh(book)  # DB가 자동으로 채운 값(id, created_at)을 book객체에 다시 불러와 채워준다.

    return book # book 객체를 자동으로 JSON으로 변환해서 Streamlit에게 돌려준다.

# ------------------------------------------------------------
# GET  /books --> 등록된 책 전체 목록을 돌려주는 API
# ------------------------------------------------------------
@app.get('/books')
def list_books(db: Session = Depends(get_db)):
    # select(Book) --> Book 테이블에서 모두 가져와라. SQL SELECT 문을 파이썬 코드로 작성
    # db.scalars(...).all()  --> SELECT문을 실제로 DB에 실행시키고, 결과를 파이썬 리스트로 받는다.
    return db.scalars(select(Book)).all()