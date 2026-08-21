import io
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError
from database import Base, engine, get_db
from models import Book

# ── v5에서 새로 추가된 import ──
# normalize_isbn: isbn_hint(사용자가 직접 입력한 ISBN)를 검증할 때도 재사용
# lookup_metadata: 방금 recognition.py에 추가한, Open Library 조회 함수
from services.recognition import extract_isbn, lookup_metadata, normalize_isbn

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="우리집 책장 API")


@app.post("/books/scan", status_code=status.HTTP_201_CREATED)
def scan_book(
    image: UploadFile = File(...),
    # ── v5에서 새로 추가된 매개변수 ──
    # isbn_hint: str | None = Form(None)
    #   → OCR이 계속 실패하는 경우, 사용자가 직접 ISBN 숫자를 입력해서 넘길 수 있는 선택적 입력값
    #   Form(None) → "폼 데이터로 들어오고, 안 보내도 기본값 None"이라는 뜻(필수 아님)
    isbn_hint: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # ── 여기까지는 v2~v4와 동일 (이미지 검증) ──
    raw = image.file.read()
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "올바른 이미지 파일이 아닙니다.")

    path = UPLOAD_DIR / image.filename
    path.write_bytes(raw)

    # ── v4 대비 추가된 부분 ──
    # isbn_hint가 있으면(사용자가 직접 입력) 그 값을 체크섬 검증만 하고 사용
    # 없으면 기존처럼 OCR로 추출
    isbn = normalize_isbn(isbn_hint) if isbn_hint else extract_isbn(path)

    # isbn이 있으면 Open Library에 조회 요청 → 성공하면 진짜 제목/저자/출판사가 담긴 dict
    metadata = lookup_metadata(isbn) if isbn else None

    # metadata가 있으면 그걸 그대로 쓰고, 없으면 "확인 필요" 형태의 기본값 dict를 만듦
    # (v3~v4에서는 title, isbn을 각각 따로 다뤘지만, v5부터는 data라는 dict 하나로 통합)
    data = metadata or {"isbn": isbn, "title": f"확인 필요: {image.filename}"}

    # Book(**data, ...) → data 딕셔너리를 "풀어서" 각각의 키워드 인자로 전달
    # 예: data = {"isbn": "979...", "title": "실제 책 제목", "author": "홍길동", "publisher": "출판사"}
    #     → Book(isbn="979...", title="실제 책 제목", author="홍길동", publisher="출판사", ...)와 동일
    book = Book(**data, cover_path=str(path), recognition_status="confirmed" if metadata else "needs_review")
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.get("/books")
def list_books(db: Session = Depends(get_db)):
    return db.scalars(select(Book)).all()


# ─────────────────────────────────────────────
# 💡 오늘 수업에서 꼭 보여줄 데모
# ─────────────────────────────────────────────
# 1) ISBN이 잘 인식되는 책 표지 → title이 진짜 책 제목으로 뜨는지 확인 (v3까지는 "인식된 ISBN: ..."였음)
# 2) isbn_hint에 유효한 ISBN을 직접 입력(예: "9791190090018") → OCR 없이도 바로 서지정보 조회되는지 확인
#    (Streamlit에 아직 isbn_hint 입력창이 없다면, /docs의 Swagger UI에서 직접 테스트 가능)
# 3) 인터넷이 느리거나 끊긴 상황을 가정 → lookup_metadata의 timeout=5초 덕분에 서버가 안 멈추고 needs_review로 넘어가는지 확인