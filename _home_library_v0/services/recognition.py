'''
services/recognition.py
------------------------
OCR 기능을 삽입하는 기능을 넣은 파일
--> main.py에 넣지않고 별도 파일로 빼서 관심사를 분리
--> main.py : API 요청을 어떻게 처리할지에만 집중
--> recognition.py : OCR을 어떻게 돌릴지 집중 
                     나중에 OCR 방식을 바꾸더라도(다른 OCR 엔진으로 교체) 이 파일만 수정하면 된다.

uv add pytesseract
라이브러리 설치  --> OCR 인식해주는 라이브러리

'''
import re  # 정규표현식을 쉽게 사용할 수 있게 해주는 파이썬 표준 라이브러리

def extract_isbn(image_path) -> str | None: 
    """
    표지 사진에서 ISBN처럼 생긴 문자열을 뽑아내는 함수

    매개변수
    --------
    image_path : 이미지의 경로

    반환값
    -----
    isbn문자열 또는 못 찾으면 None이 반환   
    
    """
    try:
        # 함수안에서 import를 하는 이유 : Tesseract가 없는 pc에서도 서버가 죽지 않고 실행되게 하기 위해
        # OCR을 안 쓰는 다른 기능들은 영향을 받지 않고 원활하게 진행하기 위해
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return None

    with Image.open(image_path) as source:
        # ImageOps.grayscale(source) --> 컬러 사진을 흑백(그레이스케일)으로 변환
        #   OCR은 색상 정보가 필요없고, 흑백으로 바꾸면 글자와 배경의 명함 대비가 또렷해져서 인식률이 올라간다.
        image = ImageOps.grayscale(source)

        # ImageEnhance.Contrast(image).enhance(2) --> 명암 대비(contrast)를 2배로 강화
        #   책 표지는 화려한 경우가 많아서, 대비를 높이면 글자가 배경에서 더 잘 분리된다.
        image = ImageEnhance.Contrast(image).enhance(2)

        # config='--psm 11' --> PSM(페이지 분석 모드) 11번 --> 정해진 문단 구조 없이, 흩어진 텍스트를
        #                                                   최대한 다 찾아라!
        # pytesseract.image_to_string(...) --> 이미지를 Tesseract 엔진에 넘겨서
        #           이 안에 있는 글자를 다 텍스트로 뽑아줘!
        text = pytesseract.image_to_string(image, config='--psm 11')

    # 정규식으로 ISBN 처럼 생긴 부분만 후보로 골라내기
    # re.findall(...) --> 안의 패턴에 맞는 문자열 전체 찾아서 리스트로 돌려준다.
    candidates = re.findall(r'(?:97[89][\s-]?)?[0-9][0-9Xx\s-]{8,16}')

    return candidates[0] if candidates else None