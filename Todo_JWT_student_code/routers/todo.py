from fastapi import HTTPException, APIRouter, Depends, UploadFile, File
from starlette import status

from database.db_connection import get_session
from schema.request import TodoCreateRequest, TodoUpdateRequest
from schema.response import TodoResponse
from auth.dependencies import get_current_user_id
from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService
from pathlib import Path
import shutil
from fastapi.responses import FileResponse

router = APIRouter(tags=["Todo"])
UPLOAD_DIR = Path("uploads")


def get_todo_service(session=Depends(get_session)) -> TodoService:
    return TodoService(TodoRepository(session))


@router.get("/todos", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
def get_todos_handler(
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.get_todos(user_id)


@router.get("/todos/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def get_todo_handler(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.get_todo(todo_id, user_id)


@router.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo_handler(
    body: TodoCreateRequest,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.create_todo(body, user_id)


@router.patch("/todos/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def update_todo_handler(
    todo_id: int,
    body: TodoUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    return service.update_todo(todo_id, body, user_id)


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_handler(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TodoService = Depends(get_todo_service),
):
    service.delete_todo(todo_id, user_id)


@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}


@router.get("/files/{filename}")
def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )
