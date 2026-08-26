'''
home_library_v0 / services/recognition.py
-----------------------------
Version 4 - ISBN 체크섬 검증 추가
'''

import re

# ── v4에서 새로 추가된 함수 ──
def normalize_isbn(value: str) -> str | None:
    """
    숫자처럼 생긴 것과 진짜 유효한 ISBN은 다르다. --> 각각의 공식 체크섬 규칙으로 진위 검증
    ISBN-10 / ISBN-13
    """
    digits = re.sub(r"[^0-9Xx]", "", value) # 예)978-89-1234-567-8 --> 9788912345678

    if len(digits) == 10:
        # 각 자리 숫자에 10,9,8,..1을 곱해서 다 더한 값이 11의 배수여야 유효
        # upper() --> 대문자로 바꾸어라!
        total = sum((10 - i) * (10 if c.upper() == "X" else int(c)) for i, c in enumerate(digits))
        return digits.upper() if total % 11 == 0 else None

    if len(digits) == 13:
        # 홀수번째 자리는 1을 곱하고 짝수번째 자리는 3을 곱해서 다 더한 뒤 마지막 검증숫자와 비교
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(digits[:12]))
        return digits if (10 - total % 10) % 10 == int(digits[-1]) else None

    return None # 10자리도, 13자리도 아니면 애초에 ISBN이 아니다, None을 반환


def extract_isbn(image_path) -> str | None:
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return None  # pytesseract 패키지 자체가 설치 안 된 경우

    # ── PATH에 Tesseract가 등록 안 됐을 때를 대비해 경로를 직접 지정 ──
    import os
    default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_path):
        pytesseract.pytesseract.tesseract_cmd = default_path

    with Image.open(image_path) as source:
        image = ImageOps.grayscale(source)
        image = ImageEnhance.Contrast(image).enhance(2)
        try:
            # ── 추가된 부분: Tesseract "엔진"이 PC에 설치 안 된 경우도 함께 방어 ──
            text = pytesseract.image_to_string(image, config="--psm 11")
            print("=== OCR 원본 결과 ===")   # ← 임시 디버깅용
            print(repr(text))                  # ← 임시 디버깅용
        except pytesseract.TesseractNotFoundError:
            return None

	# ── v3 대비 추가된 부분 ──
    # :=   --> 바다코끼리 연산자 (walrus operator)
    #       대입과 조건 확인을 한 줄에서 동시에 처리
    #       normalize_isbn(candidate) 호출한 결과를 isbn에 담고,
    #       조건이 참이면 isnb을 리턴
    for candidate in re.findall(r"(?:97[89][\s-]?)?[0-9][0-9Xx\s-]{8,16}", text):
        if isbn := normalize_isbn(candidate):
            return isbn
    return None