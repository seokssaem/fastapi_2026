import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class TodoCreateRequest(BaseModel):
    title: str
    is_done: bool = False


class TodoUpdateRequest(BaseModel):
    title: str | None = None
    is_done: bool | None = None


class UserSignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., min_length=8, description="사용자 비밀번호(평문 입력)")

    @field_validator("password")
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에는 대문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에는 소문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[0-9]", value):
            raise ValueError("비밀번호에는 숫자가 최소 1개 포함되어야 합니다.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValueError("비밀번호에는 특수문자가 최소 1개 포함되어야 합니다.")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., min_length=8, description="사용자 비밀번호(평문 입력)")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="로그인 시 발급받은 refresh token")
