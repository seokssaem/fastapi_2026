# bus/models.py
"""
대구 버스정류소 정보 - 저장모델 설계 (P08)

P07 노트북(02_bus_api.ipynb)의 df 컬럼을 그대로 이어받습니다.
컬럼: 위도, 경도, 정류소ID, 정류소명, 정류소번호, 수집일시, 위치구분

정류소ID(예: DGB7041046200)는 API가 부여하는 고유값이라 자연키로 그대로
기본키(PRIMARY KEY)로 사용합니다. 지하철처럼 서로게이트 키 + UNIQUE 제약을
따로 만들 필요가 없다는 점을 학생들에게 비교해서 설명해 주세요.
"""

from sqlalchemy import Column, String, Integer, Numeric, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BusStop(Base):
    __tablename__ = "bus_stop"

    정류소ID = Column(String(30), primary_key=True)
    정류소명 = Column(String(100), nullable=False)
    정류소번호 = Column(Integer, nullable=True)   # 결측치 존재(원본도 Int64 nullable)
    위도 = Column(Numeric(9, 5))
    경도 = Column(Numeric(9, 5))
    수집일시 = Column(Date, nullable=False)        # 원본은 문자열 → 저장 단계에서 DATE로 개선
    위치구분 = Column(String(10))                   # 거리 기반 대구 8개 구·군

    def __repr__(self):
        return f"<BusStop {self.정류소ID} {self.정류소명} ({self.위도}, {self.경도})>"
