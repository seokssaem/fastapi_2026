'''
====================================================================================================
routers/user.py

HTTP 요청/응답 담당
회원가입/로그인/토큰재발급/로그아웃 --> UserSevice에서 진행한다. 
=====================================================================================================
'''
# BackgroundTasks : 응답을 먼저 클라이언트에게 보내고, 그 이후에도 처리해도 되는 작업을 뒤에서 실행하게.
from fastapi import APIRouter, status, Depends, BackgroundTasks
from schema.request import UserSignUpRequest, UserLoginRequest, RefreshTokenRequest
from schema.response import UserSignUpResponse
from database.db_connection import get_session
from repositories.user_repository import UserRepository
from services.user_service import UserService

router = APIRouter(tags=['User'])

def get_user_service(session=Depends(get_session)) -> UserService:
    """라우터가 사용할 UserService를 만들어주는 함수"""
    return UserService(UserRepository(session))

def send_welcome_email(email: str):
    """
    회원가입 성공 후 백그라운드로 실행되는 함수
    실제 메일 발송 대신 5초 걸리는 작업으로 대신 <- BackgroundTasks로 등록하면
    클라이언트는 이 5초를 안 기다리고 바로 응답을 받는다.
    """
    import time
    time.sleep(5)  
    print(f'Send welcome email to {email}...')

@router.post('/users/signup', status_code=status.HTTP_201_CREATED, response_model=UserSignUpResponse)
def signup_user_handler(
    body: UserSignUpRequest,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service),
):
    user = service.signup(body) # 이메일 중복 체크, 비밀번호 해싱 등 처리
    # 라우터는 그 결과(user)를 받아서 백그라운드 태스크만 등록하고 반환
    background_tasks.add_task(send_welcome_email, user.email)
    return user

@router.post('/users/login', status_code=status.HTTP_200_OK)
def login_user_handler(
    body: UserLoginRequest,
    service: UserService = Depends(get_user_service),
):
    return service.login(body) # 이메일/비밀번호 검증부터 토큰 발급, refresh_toke, DB저장까지 처리 후 리턴

@router.post('users/refresh', status_code=status.HTTP_200_OK)
def refresh_access_token_handler(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    return service.refresh(body.refresh_token)

@router.post('/users/logout', status_code=status.HTTP_200_OK)
def logout_user_handler(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    service.logout(body.refresh_token)
    return {'message': '로그아웃 완료'}