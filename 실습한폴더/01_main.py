# FastAPI 클래스 불러오기
from fastapi import FastAPI

app = FastAPI()

# 서버 실행
@app.get('/') # / 경로로 GET요청이 오면 아래 함수를 실행하라는 데코레이터
def root_hander():
    # 딕셔너리를 반환하면 FastAPI가 자동으로 JSON으로 변환해서 응답
    return {'message':'Hello, FastAPI!!!'}