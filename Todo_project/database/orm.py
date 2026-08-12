'''
=================================================================================
database/orm.py

모든 ORM 모델 (테이블 클래스)의 부모가 되는 Base 클래스 정의

ORM (Object Relational Mapping)??
- SQL을 직접 작성하지 않고, 파이썬 클래스로 DB 테이블을 다루는 방식
- 예를 들어 Todo 클래스를 생성하면, DB에 todo 테이블이 자동으로 생성된다. 
=================================================================================
'''
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
