import io
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError
from database import Base, engine, get_db
from models import Book

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="우리집 책장 API")


# ─────────────────────────────────────────────
# POST /books/scan  — [v2] 이제 "진짜 이미지인지" 검증이 추가됨
# ─────────────────────────────────────────────
# v1과 비교해서 바뀐 게 뭔지 먼저 짚고 갑니다:
#   - 함수 이름, 매개변수, return 하는 것 → 전부 동일 (시그니처 안 바뀜)
#   - 함수 몸통 "안쪽"에 검증 로직 한 덩어리만 새로 끼워짐
# 이게 예광탄 방식의 핵심입니다: 관통로(입력→출력 형태)는 유지한 채 내용물만 두꺼워짐
@app.post("/books/scan", status_code=status.HTTP_201_CREATED)
def scan_book(image: UploadFile = File(...), db: Session = Depends(get_db)):

    # ── v1과 달라진 첫 번째 지점 ──
    # v1에서는 image.file.read()를 바로 path.write_bytes()에 넘겼는데,
    # v2에서는 일단 raw라는 변수에 "받아만" 둡니다. 저장은 검증을 통과한 다음에 합니다.
    # (검증에 실패할 파일을 디스크에 미리 써버리면 나중에 지워야 하는 뒤처리가 생기므로,
    #  "검증 먼저, 저장은 그다음"이 더 안전한 순서입니다)
    raw = image.file.read()

    # ── 여기가 오늘 새로 추가되는 핵심 로직 ──
    try:
        # io.BytesIO(raw) → 방금 읽은 바이트 데이터를 "메모리 안의 파일"처럼 다루게 해주는 도구
        #                    (디스크에 진짜 파일을 만들지 않고도 파일인 것처럼 열어볼 수 있음)
        # Image.open(...) → PIL(Pillow) 라이브러리로 이 바이트가 이미지로 열리는지 시도
        # with ... as probe: → 확인이 끝나면 자동으로 메모리를 정리해줌(파일 열고 안 닫는 실수 방지)
        with Image.open(io.BytesIO(raw)) as probe:
            # probe.verify() → "이 파일이 진짜로 손상되지 않은 이미지 형식이 맞는지" PIL이 내부적으로 검사
            # 예를 들어 .txt 파일 내용을 .jpg인 척 보내면 여기서 걸러짐
            probe.verify()

    # UnidentifiedImageError → PIL이 아예 이미지 형식으로 인식조차 못했을 때 발생하는 에러
    # OSError → 파일이 중간에 잘렸거나 손상된 경우 등, 좀 더 넓은 범위의 파일 관련 에러
    # 이 두 가지를 한꺼번에 잡아서 "이미지가 아니거나 문제가 있는 파일"로 처리
    except (UnidentifiedImageError, OSError):
        # HTTPException(415, ...) → HTTP 상태코드 415(Unsupported Media Type, "지원하지 않는 파일 형식")를
        #                            응답으로 돌려주면서 함수 실행을 즉시 중단시킴
        # raise를 만나는 순간 아래 코드(저장, DB 등록)는 실행되지 않고 바로 클라이언트에게 에러가 감
        raise HTTPException(415, "올바른 이미지 파일이 아닙니다.")

    # ── 여기부터는 v1과 거의 동일 (검증을 통과한 진짜 이미지만 도달하는 지점) ──
    path = UPLOAD_DIR / image.filename
    path.write_bytes(raw)  # v1에서는 image.file.read()를 바로 넣었지만, v2는 이미 읽어둔 raw를 재사용

    # title은 아직 그대로 "테스트북(임시)"입니다.
    # v2의 역할은 "가짜 파일을 걸러내는 것"까지만이고, 진짜 제목을 채우는 건 다음 시간(v3, OCR) 몫입니다.
    book = Book(title="테스트북(임시)", cover_path=str(path), recognition_status="confirmed")
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.get("/books")
def list_books(db: Session = Depends(get_db)):
    return db.scalars(select(Book)).all()


# ─────────────────────────────────────────────
# 💡 오늘 수업에서 꼭 보여줄 데모 2가지
# ─────────────────────────────────────────────
# 1) .txt 파일을 사진인 척 업로드
#    → 415 에러가 뜨는지 확인 (Swagger 문서 /docs에서 직접 테스트하면 에러 메시지가 눈에 잘 보임)
#
# 2) 진짜 사진 파일을 업로드
#    → 여전히 정상적으로 "테스트북(임시)"이 등록되는지 확인
#    → "v1에서 되던 게 v2에서도 여전히 잘 된다"는 걸 보여주는 게 예광탄 방식에서 중요합니다.
#      (기능을 추가했다고 기존에 되던 게 깨지면 안 됨)
#
# ⚠️ 자주 나오는 질문: "그럼 image.filename이 없는 파일은요?"
#    → 지금 버전은 아직 그 경우까지는 안 다룹니다. 나중 버전(v6)에서 uuid로 파일명을
#      자동 생성하는 방식으로 아예 이 문제 자체를 없애버립니다. 지금은 신경 안 써도 됩니다.