from fastapi import HTTPException, status
from models import User
from repositories.user_repository import UserRepository
from schema.request import UserSignUpRequest, UserLoginRequest
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token, create_refresh_token, decode_token


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def signup(self, body: UserSignUpRequest) -> User:
        if self.repository.find_by_email(body.email):
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="이미 사용 중인 이메일입니다."
            )
        user = User(email=str(body.email), hashed_password=hash_password(body.password))
        return self.repository.save(user)

    def login(self, body: UserLoginRequest) -> dict:
        user = self.repository.find_by_email(body.email)
        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )

        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        user.refresh_token = refresh_token
        self.repository.save(user)

        return {"access_token": access_token, "refresh_token": refresh_token}

    def refresh(self, refresh_token: str) -> dict:
        user_id = decode_token(refresh_token, expected_type="refresh")
        user = self.repository.find_by_id(user_id)

        if not user or user.refresh_token != refresh_token:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 refresh token입니다. 다시 로그인해주세요."
            )

        return {"access_token": create_access_token(user_id=user.id)}

    def logout(self, refresh_token: str) -> None:
        user_id = decode_token(refresh_token, expected_type="refresh")
        user = self.repository.find_by_id(user_id)
        if user:
            user.refresh_token = None
            self.repository.save(user)
