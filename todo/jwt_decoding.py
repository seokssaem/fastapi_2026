# =========================================================================
# todo/jwt_decoding.py
# 
# - "서명 검증 없이" JWT의 헤더/페이로드로만 직접 풀어보는 실습 스크립트
# - base64/json 표준라이브러리만 사용해서 JWT가 암호화가 아니라 
#   "인코딩 + 서명"이라는 것을 확인해보자!
# =========================================================================
import base64
import json

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwiZXhwIjoxNzg2MzQwOTUzfQ.kM5q0gYKz9NgWFMTl4tEdMxlXuC8lOFg'

# 디코딩 테스트용도의 실습이므로 이번에는 서명이 부분이 없다. --> 밑줄로 받아서 무시
header_b64, payload_b64, _ = token.split('.') # .을 기준으로 분리

def decode(b64: str):
    """
    Base64 URL-safe 디코딩 함수
    JWT가 Base64가 아니라 'URL-safe'버전을 사용
            길이가 4의 배수가 아니면 디코딩 에러가 난다. 
    """
    padded = b64 + '=' * (-len(b64) % 4)
    decoded = base64.urlsafe_b64decode(padded)
    return json.loads(decoded)  # 디코딩한 바이트를 JSON(dict)으로 변환

header = decode(header_b64)
payload = decode(payload_b64)

print(f'Header: {header}')
print(f'Payload: {payload}')