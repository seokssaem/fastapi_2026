from fastapi import APIRouter, status, Depends, BackgroundTasks

from schema.request import UserSignUpRequest, UserLoginRequest, RefreshTokenRequest
from schema.response import UserSignUpResponse
from database.db_connection import get_session
from repositories.user_repository import UserRepository
from services.user_service import UserService

router = APIRouter(tags=["User"])


def get_user_service(session=Depends(get_session)) -> UserService:
    return UserService(UserRepository(session))


def send_welcome_email(email: str):
    import time
    time.sleep(5)
    print(f"Send welcome email to {email}...")


@router.post("/users/signup", status_code=status.HTTP_201_CREATED, response_model=UserSignUpResponse)
def signup_user_handler(
    body: UserSignUpRequest,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service),
):
    user = service.signup(body)
    background_tasks.add_task(send_welcome_email, user.email)
    return user


@router.post("/users/login", status_code=status.HTTP_200_OK)
def login_user_handler(
    body: UserLoginRequest,
    service: UserService = Depends(get_user_service),
):
    return service.login(body)


@router.post("/users/refresh", status_code=status.HTTP_200_OK)
def refresh_access_token_handler(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    return service.refresh(body.refresh_token)


@router.post("/users/logout", status_code=status.HTTP_200_OK)
def logout_user_handler(
    body: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    service.logout(body.refresh_token)
    return {"message": "로그아웃 완료"}
