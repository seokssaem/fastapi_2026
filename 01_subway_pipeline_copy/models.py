# subway/models.py
"""
대구 지하철 시간대별 승하차인원 - 저장모델 설계 (P08)

P07 노트북(01_subway.ipynb)에서 만든 df_long의 컬럼을 그대로 이어받습니다.
컬럼: 월, 일, 역번호, 역명, 승하차, 시간대컬럼, 인원수, 시작시, 날짜, 요일코드, 주말여부

P07은 pandas to_sql(if_exists='replace')로 subway_raw 테이블에 원본을 그대로 밀어넣기만
했고 기본키·제약조건이 없습니다. P08에서는 여기에 서로게이트 기본키(id)와
"동일 역·날짜·시간대·승하차구분은 하나만 존재해야 한다"는 UNIQUE 제약조건을 추가해서
정식 저장 구조로 설계합니다.
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SubwayRaw(Base):
    __tablename__ = "subway_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    월 = Column(Integer, nullable=False)
    일 = Column(Integer, nullable=False)
    역번호 = Column(Integer, nullable=False)
    역명 = Column(String(50), nullable=False)
    승하차 = Column(String(10), nullable=False)       # 승차 / 하차
    시간대컬럼 = Column(String(20), nullable=False)    # 예: '05시-06시'
    인원수 = Column(Integer, nullable=False)
    시작시 = Column(Integer, nullable=False)           # 0~23
    날짜 = Column(Date, nullable=False)
    요일코드 = Column(String(5), nullable=False)        # 월/화/수/목/금/토/일
    주말여부 = Column(Boolean, nullable=False)

    __table_args__ = (
        # 같은 역 + 날짜 + 시간대 + 승하차구분 조합은 한 번만 존재해야 함
        UniqueConstraint(
            "역번호", "날짜", "시간대컬럼", "승하차",
            name="uq_subway_raw_key",
        ),
    )

    def __repr__(self):
        return f"<SubwayRaw {self.역명} {self.날짜} {self.시간대컬럼} {self.승하차}={self.인원수}>"
