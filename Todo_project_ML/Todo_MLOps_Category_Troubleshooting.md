# Todo 카테고리 자동분류(MLOps) 트러블슈팅 

> `Todo_project_ML`에 카테고리 자동분류 기능을 붙이는 실습 중 실제로 발생했던 오류들을
> 발생 순서대로 정리한 문서입니다. 

---

## 문제 1 — 응답에 카테고리 필드가 아예 안 보임

**증상**: `GET /todos` 응답에 `predicted_category`, `final_category`가 없음. Swagger Schemas
목록에도 관련 필드가 안 보임.

**원인**: `models.py`(DB 컬럼)는 추가했지만 `schema/response.py`의 `TodoResponse`에는
필드를 추가하지 않음. Swagger/응답 형태는 DB가 아니라 **Pydantic 응답 스키마 기준**으로
결정되기 때문에, DB에 컬럼이 있어도 스키마에 없으면 절대 응답에 안 나옴.

**해결**:
```python
# schema/response.py
class TodoResponse(BaseModel):
    id: int
    title: str
    is_done: bool
    user_id: int | None
    predicted_category: str | None = None   # 추가
    final_category: str | None = None        # 추가
```

**포인트**: "DB 컬럼 추가 = API 응답에 자동 반영"이 아니라는 것, 즉
**모델(DB) → 스키마(응답) → 라우터**가 각각 독립적으로 관리된다라는 것을 알게 됨.

---

## 문제 2 — 요청(Request) 모델에 예측/확정 필드를 잘못 추가함

**증상**: `TodoCreateRequest`, `TodoUpdateRequest`에 `predicted_category`,
`final_category`를 추가하려고 시도함.

**원인**: "필드가 안 보이니 요청에도 추가해야 하나?"라는 오해. 하지만 이 두 필드는
**클라이언트가 직접 입력하면 안 되는 값**임.

- `predicted_category`: 반드시 서버 내부에서 `category_service.predict(title)`로만
  채워져야 함 (아니면 "모델의 예측"이라는 의미 자체가 깨짐)
- `final_category`: 반드시 전용 엔드포인트(`PATCH /todos/{id}/category`,
  `CategoryUpdateRequest`)로만 채워져야 함 (일반 수정과 경로를 분리해야
  "사용자가 확인/확정했다"는 의미가 유지됨)

**해결**: `TodoCreateRequest`/`TodoUpdateRequest`에서 두 필드 제거. 카테고리 확정
전용으로 이미 만들어둔 `CategoryUpdateRequest`만 사용.

```python
class TodoCreateRequest(BaseModel):
    title: str
    is_done: bool = False
    # predicted_category, final_category 없음 — 서버가 채우거나 별도 엔드포인트로만 입력
```

**포인트**: 요청/응답 스키마를 분리하는 이유(회원가입 password 예시와 동일한 원칙)를
카테고리 필드에도 그대로 적용해볼 수 있는 좋은 확장 질문거리.

---

## 문제 3 — `NameError: CategoryUpdateRequest`

**증상**: `routers/todo.py`에서 `CategoryUpdateRequest`를 타입으로 썼는데 이름을
찾을 수 없다는 에러 발생.

**원인**: `schema/request.py`에는 정의돼 있지만, `routers/todo.py` 상단 import 문에는
빠져 있었음.

**해결**:
```python
from schema.request import TodoCreateRequest, TodoUpdateRequest, CategoryUpdateRequest
```

**포인트**: 파일을 나눠서 관리할 때 가장 자주 나오는 실수. "정의했다"와
"가져다 썼다(import)"는 별개라는 걸 반복해서 짚어줄 필요 있음.

---

## 문제 4 — `PATCH /todos/{id}/category`가 404 (경로가 `/1/category`로 등록됨)

**증상**: Swagger에서 curl 명령이 `http://127.0.0.1:8000/1/category`로 나옴
(`/todos`가 빠짐). 호출하면 404.

**원인**: `routers/todo.py`의 다른 엔드포인트들은 전부 경로에 `/todos`를 직접
써주는 방식(`router = APIRouter(tags=['Todo'])`, prefix 없음)이었는데,
카테고리 엔드포인트만 그 규칙을 놓침.

```python
# 잘못된 코드
@router.patch("/{todo_id}/category", ...)   # /todos 빠짐
```

**해결**:
```python
@router.patch("/todos/{todo_id}/category", response_model=TodoResponse)
```

**포인트**: `router`에 `prefix`를 안 쓰고 각 경로에 `/todos`를 직접 붙이는
스타일을 택했다면, **엔드포인트를 새로 추가할 때마다 빠뜨리기 쉽다**는 걸
알아두기. ( `APIRouter(prefix='/todos')` 방식이
이런 실수를 원천 차단한다는 점을 생각하면 참고하기.)

---

## 문제 5 — `predicted_category`가 계속 `null` (핵심 트러블슈팅)

**증상**: 서버 로그에 `[INFO] 카테고리 예측 모델 로드 완료!`는 정상 출력되고,
`create_todo`의 predict 호출 코드도 맞게 작성되어 있는데, 실제로 Todo를 생성하면
`predicted_category`가 계속 `None`으로 INSERT됨.

**원인**: `get_todo_service()`가 `TodoService`를 만들 때 `category_service`를
아예 넘기지 않고 있었음.

```python
# 잘못된 코드
def get_todo_service(session=Depends(get_session)) -> TodoService:
    return TodoService(TodoRepository(session))   # category_service 없음 -> 기본값 None
```

`app.state.category_model`에 모델이 잘 로드돼 있어도, 그걸 꺼내서 `TodoService`에
전달하는 코드가 없으면 `self.category_service`가 항상 `None`이라
`create_todo`의 `if self.category_service is not None:` 분기를 절대 못 탐.

**해결**:
```python
from fastapi import Request
from services.category_service import CategoryPredictionService

def get_todo_service(request: Request, session=Depends(get_session)) -> TodoService:
    category_model = getattr(request.app.state, "category_model", None)
    category_service = CategoryPredictionService(category_model) if category_model else None
    return TodoService(TodoRepository(session), category_service)
```

**포인트**: 이번 실습에서 **가장 진단이 까다로웠던 문제**. "모델 로드 로그가
찍혔다"와 "그 모델이 실제로 요청 처리 흐름까지 전달됐다"는 서로 다른 단계라는 걸
알 필요 있음. `lifespan`(앱 전체 상태) → `Depends`(요청별 의존성 주입)로
이어지는 연결 고리 중 하나라도 빠지면 조용히(에러 없이) 기능만 안 먹힌다는 게
이 케이스의 특징 — 에러 로그가 안 남기 때문에 SQL 로그(`INSERT ... {'predicted_category': None}`)를
직접 봐야 원인이 보였음.

---

## 문제 6 (경미) — `update_category` 메서드 중복 정의

**증상**: `services/todo_service.py`에 `update_category`가 파일 안에 두 번 정의됨
(내용은 동일).

**원인**: 코드를 이어붙이는 과정에서 중복 삽입. 파이썬은 나중 정의가 앞을 덮어써서
당장 에러는 안 나지만, 이후 한쪽만 수정하고 다른 쪽을 놓치는 실수로 이어지기 쉬움.

**해결**: 중복분 삭제, 하나만 유지.

---

## 참고 — 아직 에러는 아니지만 짚어줄 만한 설계상 포인트 (Streamlit)

| 항목 | 내용 |
|---|---|
| "모델이 맞혔다" 확정 역설 | selectbox 초기값이 이미 `predicted`와 같아서, 사용자가 값을 바꾸지 않으면 `final_category`가 영영 안 채워짐. "예측이 맞다"를 확정할 명시적인 버튼이 없음 |
| 제목 공백 미제거 | `new_title.strip()`으로 빈 값만 검사하고, 실제 전송(`json={'title': new_title, ...}`)은 원본 그대로 보냄 |

---

## 전체 요약 체크리스트

| # | 파일 | 문제 | 상태 |
|---|---|---|---|
| 1 | `schema/response.py` | `TodoResponse`에 카테고리 필드 누락 | ✅ 해결 |
| 2 | `schema/request.py` | Create/Update Request에 잘못된 필드 추가 시도 | ✅ 해결 |
| 3 | `routers/todo.py` | `CategoryUpdateRequest` import 누락 | ✅ 해결 |
| 4 | `routers/todo.py` | PATCH 경로에 `/todos` prefix 누락 | ✅ 해결 |
| 5 | `routers/todo.py` | `get_todo_service`가 `category_service` 미주입 | ✅ 해결 |
| 6 | `services/todo_service.py` | `update_category` 중복 정의 | ✅ 해결 |
| 7 | `streamlit_app.py` | "확정" 역설 / 제목 공백 | 참고만, 필요 시 보완 |
