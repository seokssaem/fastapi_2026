'''
=================================================================================
schema/response.py

서버가 클라이언트(사용자)에게 "돌려주는" 데이터의 형태를 정의하는 파일
request.py와 분리하는 이유: 회원가입 경우 "요청"에는 password가 있지만, 
    "응답"에는 절대 표함하면 안되기 때문이다. (보안 사고 방지)
=================================================================================
'''
from datetime import datetime
from pydantic import BaseModel

# --- 할 일 응답 모델 ------------------------------------------
class TodoResponse(BaseModel):
    id: int
    title: str
    is_done: bool
    # "이 할 일이 누구의 것인지"를 클라이언트가 화면에서 구분할 수 있도록 추가
    user_id: int | None
    # ===== ML 추가 =========
    predicted_category: str | None = None
    final_category: str | None = None

# --- 회원가입 응답 모델 ------------------------------------------
# Pydantic이 password를 필터링 시켜 제외
class UserSignUpResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

# --- ML 응답 모델 -------------------------------------------------
class ModelAccuracyResponse(BaseModel):
    # routers/ml.py 의 GET /admin/model-accuracy 응답 형태
    total_labeled: int      # final_category가 채워진(=사용자가 확인한)  Todo 개수
    correct: int            # 그 중 predicted_category와 final_category가 일치한 개수
    accuracy: float | None  # total_labeled가 0이면 나눗셈이 불가능하므로 None도 가능

    