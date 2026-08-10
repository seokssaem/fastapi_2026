# ==================================================================================
# routers/user.py
# - 회원(User)과 관련된 API 엔드포인트를 모아놓은 라우터 파일
# - 현재는 회원가입 1개만 구현되어 있다. (로그인 추가 - JWT 인증 방식)
# ==================================================================================
from fastapi import APIRouter, status, HTTPException, Depends, BackgroundTasks, Request
from sqlalchemy import select
from schema.request import UserSignUpRequest, UserLoginRequest
from schema.response import UserSignUpResponse
from database.db_connection import SessionFactory, get_session
from models import User
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token

router = APIRouter(tags=['User'])

# 회원가입 --> POST 
#               /users/signup  요청이 오면 실행된다.
@router.post(
    '/users/signup',
    status_code=status.HTTP_201_CREATED,
    response_model=UserSignUpResponse
)
def signup_user_handler(body: UserSignUpRequest):  # 요청 데이터 검증
    with SessionFactory() as session:
        stmt = select(User).where(User.email == body.email) # 같은 이메일이 있다면
        existing_user = session.scalar(stmt) 
        if existing_user:  # True --> 같은 이메일이 있다
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='이미 사용 중인 이메일입니다!'
            )
        
        # 비밀번호 해시 생성 - 사용자가 입력한 평문 비밀번호를 그대로 저장하지 않고,
        # auth 모듈의 hash_password()를 통해 안전하게 암호화 시킨다. 
        hashed_password = hash_password(body.password)

        # User 모델 생성 후 DB 저장
        user = User(
            email=str(body.email),
            hashed_password=hashed_password,
        )
        session.add(user)  # 새 회원 등록
        session.commit() # 실제 INSERT 실행

        # 응답 반환
        # commit시점에 DB가 자동으로 채워준 값을 현재 user객체에 다시 읽어와서 최신 상태로 갱신
        session.refresh(user)  
        return user
