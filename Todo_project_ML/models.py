'''
=================================================================================
models.py

SQLAlchemy ORM 모델 정의 파일
파이썬 클래스와 DB 테이블을 매핑(Mapping)하는 부분

=================================================================================
'''
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.orm import Base

# --- Todo 모델 (할 일 테이블) ------------------------
class Todo(Base):
    __tablename__ = 'todo' # 실제 DB에 생성될 테이블 이름

    # 컬럼(열) --> id, title, is_done, user_id
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,  # 기본키
        autoincrement=True,  # 새 행이 추가될 때마다 1씩 자동 증가
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,  # 널 가능? 아니! --> 반드시 입력!
    )
    is_done: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False, # 새로 생성될 때마다 기본값은 '완료 안 함'
    )
    user_id: Mapped[int] = mapped_column(
        # Todo.user_id가 User.id를 참조한다. (이 할일은 어떤 회원의 것인지 연결)
        ForeignKey('user.id'), # user 테이블의 id를 참조하는 외래키
        nullable=True, # 담당 회원을 지정하지 않고도 생성 가능(널 가능?? 응!)
    )
    user: Mapped['User'] = relationship(
        back_populates='todos', # User.todos 속성과 양방향으로 연결
    )

    # ----- 카테고리 자동분류(MLOps) 관련 컬럼 ------
    # predicted_category : "모델이 뭐라고 예측했는가"의 기록, 절대 덮어쓰기하지 않는다.
    # final_category : "사람이 최종적으로 확인/수정한 값", 처음에는 비어 있다가
    #                   PATCH  /todos/{id}/category 호출 시에만 채워진다.
    # --> 두 컬럼으로 나눈 이유는??
    #   나중에 모델이 얼마나 자주 맞췄는가를 두 컬럼을 비교해서 계산할 수 있다.(정확도 측정)
    predicted_category: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
    ) # 모델이 예측한 카테고리(Todo 생성 시 자동 저장)
    final_category: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
    ) # 사용자가 직접 수정/확정한 카테고리(없으면 예측값을 그대로 신뢰한 것)





# --- User 모델 (회원 테이블) ----------------------------------------
class User(Base):
    __tablename__ = 'user'  # 테이블 이름

    id: Mapped[int] = mapped_column(primary_key=True) # 기본키
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,  # 같은 이메일로 중복 가입 불가
        index=True,  # 이메일로 조회가 자주 일어나므로 검색 속도 향상용 인덱스
        nullable=False,  # 널 가능?? 아니! --> 필수
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False, # 필수 --> 비밀번호는 평문이 아닌 '해시된 값'으로 저장 
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(), # 행 추가 시점에 DB가 자동으로 현재 시간을 채운다.
        nullable=False, # 필수
    )    
    refresh_token: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,  # 로그인 전이거나, 로그아웃한 사용자는 None
    )
    todos: Mapped[list['Todo']] = relationship(
        back_populates='user',
        # cascade='all, delete-orphan' --> 회원이 삭제되면 그 회원의 Todo들도 함께 자동삭제
        cascade='all, delete-orphan', 
    )