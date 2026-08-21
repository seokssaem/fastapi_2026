import io
import json
import re
import urllib.request


def normalize_isbn(value: str) -> str | None:
    digits = re.sub(r"[^0-9Xx]", "", value)
    if len(digits) == 10:
        total = sum((10 - i) * (10 if c.upper() == "X" else int(c)) for i, c in enumerate(digits))
        return digits.upper() if total % 11 == 0 else None
    if len(digits) == 13:
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(digits[:12]))
        return digits if (10 - total % 10) % 10 == int(digits[-1]) else None
    return None


def extract_isbn(image_path) -> str | None:
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return None

    with Image.open(image_path) as source:
        image = ImageOps.grayscale(source)
        image = ImageEnhance.Contrast(image).enhance(2)
        text = pytesseract.image_to_string(image, config="--psm 11")

    for candidate in re.findall(r"(?:97[89][\s-]?)?[0-9][0-9Xx\s-]{8,16}", text):
        if isbn := normalize_isbn(candidate):
            return isbn
    return None


# ── v5에서 새로 추가된 함수 ──
# ISBN 문자열 하나를 받아서, Open Library의 무료 공개 API로 실제 책 정보(제목/저자/출판사)를 조회
def lookup_metadata(isbn: str) -> dict | None:
    # bibkeys=ISBN:{isbn} → "이 ISBN에 해당하는 책 정보를 줘"라는 뜻의 쿼리 파라미터
    # jscmd=data → 상세 정보(제목, 저자, 출판사 등)를 포함해서 응답해달라는 옵션
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"

    try:
        # urllib.request.urlopen(...) → 외부 API에 실제 HTTP 요청을 보냄
        # timeout=5 → 5초 안에 응답이 없으면 포기(외부 API가 느리다고 우리 서버까지 무한정 멈추면 안 되므로)
        with urllib.request.urlopen(url, timeout=5) as response:
            # json.load(response) → 응답 본문을 파이썬 딕셔너리로 파싱
            # .get(f"ISBN:{isbn}") → 그 안에서 우리가 조회한 ISBN에 해당하는 항목만 꺼냄
            item = json.load(response).get(f"ISBN:{isbn}")
    except (OSError, ValueError):
        # 네트워크 문제(OSError)나 응답이 JSON이 아닌 경우(ValueError) → 조회 실패로 처리
        return None

    if not item:
        # API는 정상 응답했지만 그 ISBN에 대한 정보가 DB에 없는 경우(item이 없음)
        return None

    # 우리 Book 모델의 칼럼 이름(isbn, title, author, publisher)에 맞춰서 딕셔너리로 정리해서 반환
    return {
        "isbn": isbn,
        "title": item.get("title") or f"ISBN {isbn}",
        # authors는 [{"name": "저자1"}, {"name": "저자2"}] 형태의 리스트 → 이름만 뽑아서 쉼표로 이어붙임
        "author": ", ".join(a["name"] for a in item.get("authors", [])) or None,
        # publishers도 리스트 형태 → 첫 번째 출판사 이름만 사용
        "publisher": (item.get("publishers") or [{}])[0].get("name"),
    }