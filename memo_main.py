# main.py
# FastAPI 입문 실습 — 메모장 API
# DB 없이 메모리(리스트)만 사용 → 서버 재시작하면 데이터 초기화됨
#
# 실행: uvicorn main:app --reload
# 문서: http://127.0.0.1:8000/docs

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="메모장 API",
    description="FastAPI 입문 실습용 메모장 CRUD API",
    version="1.0.0",
)


# ─────────────────────────────────────────────────────────
# 임시 데이터 저장소 (메모리)
# 서버가 꺼지면 사라짐 — DB 연결 이전 단계 실습용
# ─────────────────────────────────────────────────────────
memos = []
next_id = 1  # 자동 증가 ID를 직접 관리 (전역 변수)


# ─────────────────────────────────────────────────────────
# Pydantic 모델 정의
# ─────────────────────────────────────────────────────────

class MemoCreate(BaseModel):
    """POST 요청 바디 — 메모 작성 시 받는 데이터"""
    content: str  # 내용만 받음. id, 시각은 서버에서 자동 부여


class MemoUpdate(BaseModel):
    """PATCH 요청 바디 — 메모 수정 시 받는 데이터
    
    content만 선택적으로 수정 가능.
    None이 기본값 → 보내지 않으면 기존 값 유지 (PATCH 방식)
    """
    content: str | None = None


class MemoResponse(BaseModel):
    """응답으로 내보내는 메모 형태
    
    response_model로 지정하면 /docs에 응답 스키마 자동 문서화
    """
    id: int
    content: str
    created_at: str  # 생성 시각
    updated_at: str  # 수정 시각


# ─────────────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────────────

def find_memo(memo_id: int):
    """ID로 메모 검색 — 없으면 None 반환
    
    여러 라우터에서 반복되는 검색 로직을 함수로 분리
    next(): 조건에 맞는 첫 번째 항목 반환, 없으면 두 번째 인수(None) 반환
    """
    return next((m for m in memos if m["id"] == memo_id), None)


def now():
    """현재 시각을 보기 좋은 문자열로 반환"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─────────────────────────────────────────────────────────
# 라우터 (엔드포인트)
# ─────────────────────────────────────────────────────────

@app.get("/")
def home():
    """루트 경로 — API 안내"""
    return {"message": "메모장 API입니다. /docs 에서 테스트해보세요."}


@app.get("/memos", response_model=list[MemoResponse])
def get_memos():
    """전체 메모 목록 조회
    
    GET /memos
    메모가 없으면 빈 리스트([]) 반환
    """
    return memos


@app.get("/memos/{memo_id}", response_model=MemoResponse)
def get_memo(memo_id: int):
    """특정 메모 1개 조회
    
    GET /memos/1
    - memo_id: URL 경로 파라미터, FastAPI가 자동으로 int 변환
    - 없는 ID면 404 반환
    """
    memo = find_memo(memo_id)
    if memo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{memo_id}번 메모를 찾을 수 없습니다.",
        )
    return memo


@app.post("/memos", response_model=MemoResponse, status_code=status.HTTP_201_CREATED)
def create_memo(body: MemoCreate):
    """새 메모 작성
    
    POST /memos
    - 요청 바디: { "content": "메모 내용" }
    - id, created_at, updated_at은 서버에서 자동 부여
    - 성공 시 201 Created 반환
    
    global next_id:
    함수 안에서 전역 변수를 수정하려면 global 선언 필수.
    선언 없이 수정하면 UnboundLocalError 발생.
    """
    global next_id

    memo = {
        "id": next_id,
        "content": body.content,
        "created_at": now(),
        "updated_at": now(),
    }
    memos.append(memo)
    next_id += 1  # 다음 메모를 위해 1 증가

    return memo


@app.patch("/memos/{memo_id}", response_model=MemoResponse)
def update_memo(memo_id: int, body: MemoUpdate):
    """메모 수정 (부분 수정 — PATCH)
    
    PATCH /memos/1
    - content만 보내면 content만 수정
    - 보내지 않으면 기존 값 유지
    - updated_at은 수정 시각으로 자동 갱신
    """
    memo = find_memo(memo_id)
    if memo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{memo_id}번 메모를 찾을 수 없습니다.",
        )

    # None 체크: 보낸 필드만 수정 (PATCH 핵심)
    if body.content is not None:
        memo["content"] = body.content

    # 수정 시각 갱신
    memo["updated_at"] = now()

    return memo


@app.delete("/memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memo(memo_id: int):
    """메모 삭제
    
    DELETE /memos/1
    - 성공 시 204 No Content (응답 바디 없음)
    - 없는 ID면 404 반환
    """
    memo = find_memo(memo_id)
    if memo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{memo_id}번 메모를 찾을 수 없습니다.",
        )

    memos.remove(memo)
    # 204이므로 return값 없음
