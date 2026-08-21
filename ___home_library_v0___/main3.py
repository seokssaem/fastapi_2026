import io
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError
from database import Base, engine, get_db
from models import Book

# ── v3에서 새로 추가된 import ──
# 방금 만든 app/services/recognition.py 파일에서 extract_isbn 함수를 가져옴
# .services.recognition → app 폴더 밑의 services 폴더 밑의 recognition.py라는 뜻
from services.recognition import extract_isbn

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="우리집 책장 API")


@app.post("/books/scan", status_code=status.HTTP_201_CREATED)
def scan_book(image: UploadFile = File(...), db: Session = Depends(get_db)):
    # ── 여기까지는 v2와 완전히 동일 (이미지 검증 로직 그대로) ──
    raw = image.file.read()
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "올바른 이미지 파일이 아닙니다.")

    path = UPLOAD_DIR / image.filename
    path.write_bytes(raw)

    # ── v3에서 새로 추가된 부분: 하드코딩된 "테스트북(임시)" 대신 OCR 결과 사용 ──

    # extract_isbn(path) → 방금 저장한 사진 파일 경로를 넘겨서 ISBN처럼 생긴 문자열을 뽑아옴
    # 결과는 문자열(성공) 또는 None(실패, 혹은 Tesseract 미설치) 둘 중 하나
    isbn = extract_isbn(path)

    # ── 3항 표현식(조건부 표현식) 두 줄 ──
    # "if 조건 else" 형태: 조건이 참이면 앞의 값, 거짓이면 뒤의 값
    #
    # title = f"인식된 ISBN: {isbn}" if isbn else "확인 필요: 인식 실패"
    #   → isbn에 값이 있으면(즉, None이 아니면) "인식된 ISBN: 9788936434267" 같은 문자열을 title로
    #   → isbn이 None이면(인식 실패) "확인 필요: 인식 실패"를 title로
    title = f"인식된 ISBN: {isbn}" if isbn else "확인 필요: 인식 실패"

    # status_value도 같은 원리: 인식 성공했으면 "confirmed"(확정), 실패했으면 "needs_review"(확인 필요)
    # 여기서 처음으로 needs_review 상태가 실제로 쓰이기 시작합니다.
    # → "미리 설계해서 넣은 게 아니라, OCR이라는 진짜 로직을 넣다 보니 실패 케이스가 자연스럽게 드러난" 것
    status_value = "confirmed" if isbn else "needs_review"

    # Book(...) 만들 때 title, isbn, recognition_status 세 값 모두 이제 "진짜 로직"의 결과물입니다.
    # v1~v2에서는 title="테스트북(임시)"로 고정이었는데, 오늘부터는 매번 사진에 따라 값이 달라집니다.
    book = Book(title=title, isbn=isbn, cover_path=str(path), recognition_status=status_value)
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
# 1) ISBN이 크고 또렷하게 보이는 책 표지 사진 업로드
#    → title이 "인식된 ISBN: 97889..." 형태로, recognition_status가 "confirmed"로 뜨는지 확인
#
# 2) 글자가 잘 안 보이거나 흐릿한 사진(또는 표지가 아닌 아무 사진) 업로드
#    → title이 "확인 필요: 인식 실패"로, recognition_status가 "needs_review"로 뜨는지 확인
#    → 여기서 서버가 에러 없이 정상적으로 응답한다는 게 핵심입니다.
#      (OCR이 실패해도 서비스 전체가 죽지 않는다는 걸 눈으로 보여주는 순간)
#
# ⚠️ 만약 Tesseract가 설치 안 된 학생 PC라면?
#    → extract_isbn 내부에서 ImportError를 잡아서 None을 반환하도록 이미 설계되어 있으므로
#      이 학생도 똑같이 "확인 필요: 인식 실패"로 정상 동작합니다.
#      즉, Tesseract 유무와 관계없이 오늘 실습은 모두 진행 가능합니다.