'''
========================================================================================
routers/todo.py

Http 요청을 받고 응답을 돌려주는 것만 담당한다.
전부 TodoService에게 위임한다.
========================================================================================
'''
from fastapi import HTTPException, APIRouter, Depends, UploadFile, File
# starlette : FastAPI가 내부적으로 사용하는 ASGI프레임 워크
from starlette import status # status : HTTP 상태코드를 숫자 대신 읽기 쉬운 이름(상수)으로 사용하게 한다.
from database.db_connection import get_session
from schema.request import TodoCreateRequest, TodoUpdateRequest, CategoryUpdateRequest
from schema.response import TodoResponse
from auth.dependencies import get_current_user_id
from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService
from pathlib import Path
from fastapi.responses import FileResponse
import shutil  # 파일/폴더를 복사,이동,삭제,압축하는 고수준파일 작업을 제공하는 표준 라이브러리
from fastapi import Request 
from services.category_service import CategoryPredictionService

router = APIRouter(tags=['Todo'])
UPLOAD_DIR = Path('uploads')

def get_todo_service(request: Request, session=Depends(get_session)) -> TodoService:
    """라우터가 사용할 TodoService를 만들어주는 함수"""
    category_model = getattr(request.app.state, "category_model", None)
    category_service = CategoryPredictionService(category_model) if category_model else None
    return TodoService(TodoRepository(session), category_service)

# def get_todo_service(session=Depends(get_session)) -> TodoService:
#     """라우터가 사용할 TodoService를 만들어주는 함수"""
#     return TodoService(TodoRepository(session))

# Depens--> FastAPI의 의존성 주입 기능
#       이 엔드포인트가 실행되기 전에, 이 함수부터 먼저 실행해서 결과라 파라미터에 넣어줘.
# 요청이 들어오면 FastAPI가 처리하는 순서
# 1. get_current_user_id()를 먼저 실행 -> 반환값을 user_id에 대입
# 2. get_todo_service()를 먼저 실행 -> 반환값을 service에 대입
# 3. get_todos_handler 함수 본문이 실행된다. 
@router.get('/todos', response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
def get_todos_handler(
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    # 라우터는 받은 값을 service에 그대로 전달하고, service가 돌려준 결과를 그대로 반환한다.
    return service.get_todos(user_id)

@router.get('/todos/{todo_id}', response_model=TodoResponse, status_code=status.HTTP_200_OK)
def get_todo_handler(
    todo_id: int,
    user_id: int = Depends(get_current_user_id), 
    service: TodoService = Depends(get_todo_service)
):
    return service.get_todo(todo_id, user_id)

@router.post('/todos', response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo_handler(
    body: TodoCreateRequest,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.create_todo(body, user_id)

@router.patch('/todos/{todo_id}', response_model=TodoResponse, status_code=status.HTTP_200_OK)
def update_todo_handler(
    todo_id: int,
    body: TodoUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.update_todo(todo_id, body, user_id)

@router.delete('/todos/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_hander(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    service.delete_todo(todo_id, user_id)

# ==============
@router.patch("/todos/{todo_id}/category", response_model=TodoResponse)
def update_todo_category_handler(
    todo_id: int,
    request: CategoryUpdateRequest,
    todo_service: TodoService = Depends(get_todo_service),
    user_id: int = Depends(get_current_user_id),  # 기존 인증 의존성 그대로 재사용
):
    return todo_service.update_category(todo_id, request.category, user_id)    