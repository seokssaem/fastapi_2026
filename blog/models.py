from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database.orm import Base

# Article 모델
class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    title: Mapped[str] = mapped_column(
        String(255)
    )
    content: Mapped[str] = mapped_column(
        String(1000)
    )
