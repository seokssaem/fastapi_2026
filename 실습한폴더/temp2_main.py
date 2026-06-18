from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, field_validator
from enum import Enum

# ─────────────────────────────────────────────────────────
# FastAPI 앱 인스턴스 생성
# title, description, version은 /docs 페이지에 자동으로 표시됨
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title="점심 메뉴 추천 API",
    description="오늘 뭐 먹을지 고민될 때 사용하는 메뉴 추천 API입니다.",
    version="1.0.0",
)


# ─────────────────────────────────────────────────────────
# Enum: 카테고리 허용값 제한
# str을 함께 상속하면 JSON 응답에서 "한식" 문자열로 출력됨
# str만 상속하면 "CategoryEnum.한식"으로 출력되어 보기 불편함
# ─────────────────────────────────────────────────────────
class CategoryEnum(str, Enum):
    한식 = "한식"
    일식 = "일식"
    중식 = "중식"
    양식 = "양식"


# ─────────────────────────────────────────────────────────
# Pydantic 모델: 저장소(DB 역할)에 사용할 메뉴 스키마
# 요청/응답 모두 동일한 구조로 일관성 유지
# ─────────────────────────────────────────────────────────
class Menu(BaseModel):
    id: int
    name: str
    category: CategoryEnum  # Enum으로 허용값 제한
    price: int
    like: int = 0           # 기본값 0 (생성 시 자동 설정)


# ─────────────────────────────────────────────────────────
# Pydantic 모델: POST 요청 바디 스키마 (메뉴 생성)
# id, like는 서버에서 자동 부여하므로 클라이언트가 보내지 않음
# ─────────────────────────────────────────────────────────
class MenuCreateRequest(BaseModel):
    name: str
    category: CategoryEnum  # "한식"/"일식"/"중식"/"양식" 외 값은 422 에러
    price: int

    # field_validator: 추가 유효성 검사
    # price가 0 이하이면 의미없는 데이터이므로 차단
    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("가격은 0보다 커야 합니다.")
        return v


# ─────────────────────────────────────────────────────────
# Pydantic 모델: PATCH 요청 바디 스키마 (메뉴 수정)
# PATCH는 일부 필드만 수정 → 모든 필드를 Optional로 선언
# None이 기본값 → 클라이언트가 보내지 않은 필드는 수정하지 않음
# PUT과의 차이: PUT은 전체 교체(모든 필드 필수), PATCH는 부분 수정
# ─────────────────────────────────────────────────────────
class MenuUpdateRequest(BaseModel):
    name: str | None = None
    category: CategoryEnum | None = None
    price: int | None = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("가격은 0보다 커야 합니다.")
        return v


# ─────────────────────────────────────────────────────────
# 임시 데이터 저장소 (메모리 기반)
# 실제 서비스에서는 PostgreSQL 등 DB로 대체
# Pydantic 모델 인스턴스로 저장 → 타입 일관성 유지
# ─────────────────────────────────────────────────────────
menus: list[Menu] = [
    Menu(id=1, name="김치찌개", category=CategoryEnum.한식, price=9000),
    Menu(id=2, name="돈까스",   category=CategoryEnum.일식, price=11000),
    Menu(id=3, name="마라탕",   category=CategoryEnum.중식, price=13000),
    Menu(id=4, name="햄버거",   category=CategoryEnum.양식, price=8500),
]


# ─────────────────────────────────────────────────────────
# 헬퍼 함수: 다음 id 계산
# len(menus) + 1 방식은 삭제 후 재추가 시 id 중복 발생
# 예: [1,2,3,4] → 4 삭제 → [1,2,3] → 추가 → id=4 중복!
# max() 방식은 항상 현재 최대값 기준으로 증가하여 중복 없음
# menus가 비어있는 경우 max()가 에러나므로 default=0 처리
# ─────────────────────────────────────────────────────────
def get_next_id() -> int:
    if not menus:
        return 1
    return max(menu.id for menu in menus) + 1


# ─────────────────────────────────────────────────────────
# 헬퍼 함수: id로 메뉴 검색
# 여러 라우터에서 반복되는 검색 로직을 함수로 분리
# next()는 조건에 맞는 첫 번째 항목 반환, 없으면 None 반환
# ─────────────────────────────────────────────────────────
def find_menu(menu_id: int) -> Menu | None:
    return next((menu for menu in menus if menu.id == menu_id), None)


# =============================================================
# 라우터 (엔드포인트) 정의
# 순서 주의: 구체적인 경로(/menus/random)가
#           동적 경로(/menus/{menu_id})보다 반드시 위에 있어야 함
# =============================================================

@app.get("/")
def home():
    """루트 경로 - API 안내 메시지 반환"""
    return {"message": "오늘 뭐 먹지? 점심 메뉴 추천 API입니다."}


@app.get("/menus", response_model=list[Menu])
def get_menus():
    """전체 메뉴 목록 반환
    
    response_model=list[Menu]: 응답 구조를 Pydantic으로 명시
    → /docs에서 응답 스키마 자동 문서화
    → 스키마 외 필드는 자동으로 제거 (보안상 유리)
    """
    return menus


@app.get("/menus/random", response_model=Menu)
def random_menu():
    """랜덤 메뉴 1개 반환
    
    ⚠️ 라우터 순서 중요:
    이 엔드포인트가 /menus/{menu_id} 아래에 있으면
    "random" 문자열이 menu_id(int) 자리에 매핑되어 422 에러 발생.
    FastAPI는 위에서부터 순서대로 라우터를 매칭하기 때문.
    """
    import random
    if not menus:
        raise HTTPException(status_code=404, detail="등록된 메뉴가 없습니다.")
    return random.choice(menus)


@app.get("/menus/{menu_id}", response_model=Menu)
def get_menu(menu_id: int):
    """특정 ID의 메뉴 1개 반환
    
    - menu_id: URL 경로 파라미터, FastAPI가 자동으로 int 변환
    - 문자열이 들어오면 422 Unprocessable Entity 자동 반환
    - 없는 ID면 404 Not Found 반환
    """
    menu = find_menu(menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")
    return menu


@app.post("/menus", response_model=Menu, status_code=status.HTTP_201_CREATED)
def create_menu(body: MenuCreateRequest):
    """새 메뉴 등록
    
    - 201 Created: 리소스가 새로 생성되었음을 명시 (200과 구별)
    - id, like는 서버에서 자동 부여
    - category는 Enum으로 검증 → 허용 외 값 자동 차단
    - price <= 0 이면 422 반환 (field_validator)
    """
    new_menu = Menu(
        id=get_next_id(),
        name=body.name,
        category=body.category,
        price=body.price,
        like=0,
    )
    menus.append(new_menu)
    return new_menu


@app.patch("/menus/{menu_id}", response_model=Menu)
def update_menu(menu_id: int, body: MenuUpdateRequest):
    """특정 메뉴 부분 수정
    
    PATCH vs PUT:
    - PATCH: 보낸 필드만 수정, 나머지 유지 → 이 방식
    - PUT: 전체 교체, 보내지 않은 필드는 기본값으로 초기화

    Pydantic 모델은 불변(immutable)에 가까우므로
    model_copy(update={...})로 새 인스턴스를 생성해 교체
    """
    menu = find_menu(menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")

    # 보낸 필드만 추출 (None 제외)
    update_data = body.model_dump(exclude_none=True)

    # 기존 데이터 기반으로 수정된 새 인스턴스 생성
    updated_menu = menu.model_copy(update=update_data)

    # 리스트에서 기존 항목 교체
    idx = menus.index(menu)
    menus[idx] = updated_menu

    return updated_menu


@app.patch("/menus/{menu_id}/like", response_model=Menu)
def like_menu(menu_id: int):
    """메뉴 좋아요 +1
    
    - 요청 바디 없음, URL만으로 동작
    - like 필드를 1 증가시키고 수정된 메뉴 반환
    - 중복 방지 없음 (교육용) → 실무에서는 세션/IP 체크 필요
    """
    menu = find_menu(menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")

    updated_menu = menu.model_copy(update={"like": menu.like + 1})
    idx = menus.index(menu)
    menus[idx] = updated_menu

    return updated_menu


@app.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: int):
    """특정 메뉴 삭제
    
    - 204 No Content: 성공했지만 돌려줄 내용 없음
    - response_model 지정하지 않음 (바디가 없으므로)
    - 삭제 후 id를 재정렬하지 않는 것이 올바른 동작
      → 실무에서도 id는 재사용하지 않음 (데이터 무결성)
    """
    menu = find_menu(menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")

    menus.remove(menu)
    # 204이므로 return값 없음 (FastAPI가 빈 바디로 응답)
