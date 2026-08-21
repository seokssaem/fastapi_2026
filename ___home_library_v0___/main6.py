import io
import uuid
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError
from database import Base, engine, get_db
from models import Book
from services.recognition import extract_isbn, lookup_metadata, normalize_isbn

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="우리집 책장 API")


@app.post("/books/scan", status_code=status.HTTP_201_CREATED)
def scan_book(
    image: UploadFile = File(...),
    isbn_hint: str | None = Form(None),
    db: Session = Depends(get_db),
):
    raw = image.file.read()
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "올바른 이미지 파일이 아닙니다.")

    # ── v5 대비 추가된 부분: 파일명 충돌 방지 ──
    # v1~v5는 image.filename(원본 파일명)을 그대로 저장 경로로 썼음
    # → 같은 이름의 파일(예: "cover.jpg")을 여러 번 업로드하면 이전 사진을 덮어써버리는 문제가 있었음
    suffix = Path(image.filename or "cover.jpg").suffix.lower()   # 확장자만 추출(.jpg, .png 등)
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"              # uuid로 매번 겹치지 않는 랜덤 파일명 생성
    path.write_bytes(raw)

    isbn = normalize_isbn(isbn_hint) if isbn_hint else extract_isbn(path)
    metadata = lookup_metadata(isbn) if isbn else None
    data = metadata or {"isbn": isbn, "title": f"확인 필요: {image.filename}"}

    book = Book(**data, cover_path=str(path), recognition_status="confirmed" if metadata else "needs_review")
    db.add(book)

    # ── v5 대비 추가된 부분: 중복 ISBN 방지 ──
    try:
        db.commit()
    except IntegrityError:
        # models.py에서 isbn 칼럼에 unique=True를 걸어뒀기 때문에,
        # 이미 등록된 ISBN을 또 등록하려고 하면 db.commit() 시점에 IntegrityError가 발생함
        db.rollback()                   # 실패한 트랜잭션을 되돌려서 DB 상태를 깨끗하게 정리
        path.unlink(missing_ok=True)     # 방금 저장했던 사진 파일도 삭제(주인 없는 "고아 파일" 방지)
        raise HTTPException(409, "이미 등록된 ISBN입니다.")

    db.refresh(book)
    return book


@app.get("/books")
def list_books(db: Session = Depends(get_db)):
    return db.scalars(select(Book)).all()


# ─────────────────────────────────────────────
# 💡 오늘 수업에서 꼭 보여줄 라이브 데모 3가지 (Day73 최종)
# ─────────────────────────────────────────────
# 1) 정상 인식되는 책 사진 → confirmed, 실제 제목 확인
# 2) 인식 실패 유도 사진 → needs_review, 서비스는 안 죽음
# 3) 같은 ISBN(또는 같은 isbn_hint) 재등록 → 409 Conflict로 막히는지 확인
#
# 이 세 가지가 모두 통과하면 "서버프로그램구현 40h" 완료 기준을 충족합니다.