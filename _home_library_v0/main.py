'''
home_library_v0 / main.py
-----------------------------
Version 3 - ISBN 추출

예광탄 방식을 활용한 아주 얇은 코드
'''
import io
from pathlib import Path
from fastapi import Depends, FastAPI, File, UploadFile, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError
from database import Base, engine, get_db
from models import Book
from services.recognition import extract_isbn  # version 3에서 추가

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

# models.py에서 정의한 Book, ReadingStatus, Review 클래스들을 실제 PostgreSQL 테이블로 생성하는 학할
# (이미 테이블이 있으면 넘어가고, 없으면 새로 만든다. )
Base.metadata.create_all(engine)

# FastAPI 앱 객체 생성, title--> /docs(스웨거 문서)에서 화면 상단에 표시될 이름
app = FastAPI(title='우리집 책장 API')

# -------------------------------------------------------------------------------------------------
# POST /books/scan --> 사진을 업로드해서 책 한 권을 등록하는 API --> Version 2 (진짜 이미지인지 검증)
# -------------------------------------------------------------------------------------------------
@app.post('/books/scan', status_code=status.HTTP_201_CREATED)
def scan_book(image: UploadFile = File(...), db: Session = Depends(get_db)):
    # V2에서는 raw 변수에 이미지를 받아만 둔다. 
    # 저장은 검증을 통과한 다음에 한다. 
    raw = image.file.read()

    try:
        # io.BytesIO(raw) --> 방금 읽은 바이트 데이터를 메모리 안의 파일처럼 다루게 해주는 도구
        #                     (디스크에 진짜 파일을 만들지 않고도 파일인것처럼 열어볼 수 있다.)
        # Image.open(...) --> PIL(Pillow) 라이브러리로 이 바이트가 이미지로 열리는지 시도
        # with ... as probe: --> 확인이 끝나면 자동으로 메모리를 정리해준다. (파일을 닫는다.)
        with Image.open(io.BytesIO(raw)) as probe:
            # probe.verify() --> 이 파일이 진짜로 손상되지 않은 이미지 형식이 맞는지 내부적으로 검사(PIL)
            probe.verify()

    # UnidentifiedImageError --> PIL이 아예 이미지 형식으로조차 인식하지 못했을 때 발생하는 에러
    # OSError --> 파일이 중간에 잘렸거나, 손상된 경우 등 좀 더 넓은 범위의 파일 관련 에러
    except (UnidentifiedImageError, OSError):
        # HTTP 상태코드 415(Unsupported Media Type, 지원하지 않는 파일 형식) 함수 실행 중단 시킨다.
        # raise를 만나는 순간 저장, DB등록은 실행되지 않는다. 
        raise HTTPException(415, '올바른 이미지 파일이 아닙니다.')


    # uploads 폴더 밑에 "원래 업로드 된 파일명"으로 저장 경로를 만든다.
    path = UPLOAD_DIR / image.filename

    # image.file.read() --> 업로드 된 파일의 실제 바이트 내용을 읽어온다.
    # path.write_bytes(...) --> 그 바이트를 위에서 만든 경로에 실제 파일로 저장
    path.write_bytes(raw)

    # V3 --> extract_isbn(path) --> 방금 저장한 사진 파일 경로를 넘겨서 ISBN처럼 생긴 문자열을 뽑아온다.
    isbn = extract_isbn(path)

    title = f'인식된 ISBN: {isbn}' if isbn else '확인 필요: 인식 실패'

    status_value = 'confirmed' if isbn else 'needs_review'


    book = Book(title=title, isbn=isbn, cover_path=str(path), recognition_status=status_value)

    db.add(book)  # 이 책 데이터 저장 대기열에 올린다. (아직 DB에 실제로 사용되지는 않는다.)
    db.commit()  # 대기열에 올린 내용을 실제로 DB에 확정 저장
    db.refresh(book)  # DB가 자동으로 채운 값(id, created_at)을 book객체에 다시 불러와 채워준다.

    return book  # book 객체를 자동으로 JSON으로 변환해서 Streamlit에게 돌려준다.

# --------------------------------------------------------------
# GET  /books  --> 등록된 책 전체 목록을 돌려주는 API
# --------------------------------------------------------------
@app.get('/books')
def list_books(db: Session = Depends(get_db)):
    # select(Book) --> Book 테이블에서 모두 가져와라. SQL SELECT 문을 파이썬 코드로 작성
    # db.scalars(...).all()  --> SELECT문을 실제로 DB에 실행시키고, 결과를 파이썬 리스트로 받는다.
    return db.scalars(select(Book)).all()











