from fastapi import HTTPException, status
from models import Todo
from repositories.todo_repository import TodoRepository
from schema.request import TodoCreateRequest, TodoUpdateRequest


class TodoService:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def get_todos(self, user_id: int) -> list[Todo]:
        return self.repository.find_all_by_user(user_id)

    def get_todo(self, todo_id: int, user_id: int) -> Todo:
        todo = self.repository.find_by_id(todo_id, user_id)
        if todo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
        return todo

    def create_todo(self, body: TodoCreateRequest, user_id: int) -> Todo:
        todo = Todo(title=body.title, is_done=body.is_done, user_id=user_id)
        return self.repository.save(todo)

    def update_todo(self, todo_id: int, body: TodoUpdateRequest, user_id: int) -> Todo:
        todo = self.get_todo(todo_id, user_id)
        if body.title is not None:
            todo.title = body.title
        if body.is_done is not None:
            todo.is_done = body.is_done
        return self.repository.save(todo)

    def delete_todo(self, todo_id: int, user_id: int) -> None:
        todo = self.get_todo(todo_id, user_id)
        self.repository.delete(todo)
