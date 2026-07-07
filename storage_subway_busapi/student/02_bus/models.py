# ===================================================================
# fastapi/storage_subway_busapi/02_bus/models.py
#   2026-07-07
# 
# 저장 모델 설계(스키마)
# 기본키가 자연키 그대로 사용
#   정류소ID(API가 부여하는 고유값)
#
# 직접 실행되는 파일은 아니다.
#   database.py, loader.py 가 import해서 사용
# ===================================================================

from sqlalchemy import Column, Integer, String, Date, Numeric
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BusStop(Base):
    __tablename__ = 'bus_stop'

    정류소ID = Column(String(30), primary_key=True)   # 기본키
    정류소명 = Column(String(100), nullable=False)      # 필수입력사항- null 안됨
    정류소번호 = Column(Integer, nullable=True)         # null 허용
    위도 = Column(Numeric(9, 5))
    경도 = Column(Numeric(9, 5))
    수집일시 =Column(Date, nullable=False)
    위치구분 = Column(String(10))

    def __repr__(self):
        return f'<BustStop {self.정류소ID} {self.정류소명} {self.위도} {self.경도})>'
