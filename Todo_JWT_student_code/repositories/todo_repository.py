from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Todo


class TodoRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_all_by_user(self, user_id: int) -> list[Todo]:
        stmt = select(Todo).where(Todo.user_id == user_id)
        return list(self.session.execute(stmt).scalars().all())

    def find_by_id(self, todo_id: int, user_id: int) -> Todo | None:
        stmt = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        return self.session.execute(stmt).scalars().first()

    def save(self, todo: Todo) -> Todo:
        self.session.add(todo)
        self.session.commit()
        return todo

    def delete(self, todo: Todo) -> None:
        self.session.delete(todo)
        self.session.commit()
