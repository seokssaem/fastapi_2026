"""Pydantic 스키마"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List
from datetime import date

# API 응답으로 내보낼 선수 성적 데이터 모양이다.
class Performance(BaseModel):
    # from_attributes=True는 SQLAlchemy ORM 객체를 Pydantic 모델로 변환할 수 있게 한다.
    model_config = ConfigDict(from_attributes = True)
    performance_id : int
    player_id : int
    week_number : str
    fantasy_points : float
    last_changed_date : date      

# 선수 기본 정보. 다른 응답 모델에서도 재사용하기 위해 Base 클래스로 분리했다.
class PlayerBase(BaseModel):
    model_config = ConfigDict(from_attributes = True)    
    player_id : int
    gsis_id: str | None
    first_name : str
    last_name : str
    position : str
    last_changed_date : date

# 선수 상세 응답. 기본 정보에 성적 목록을 함께 포함한다.
class Player(PlayerBase):
    model_config = ConfigDict(from_attributes = True)
    performances: List[Performance] = Field(default_factory=list)

# 팀 기본 정보. 리그 응답 안에 팀 목록을 넣을 때도 이 모델을 재사용한다.
class TeamBase(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    league_id : int
    team_id : int
    team_name : str
    last_changed_date : date

# 팀 상세 응답. 팀 기본 정보에 선수 목록을 함께 포함한다.
class Team(TeamBase):
    model_config = ConfigDict(from_attributes = True)
    players: List[PlayerBase] = Field(default_factory=list)

# 리그 응답. 리그 기본 정보와 소속 팀 목록을 함께 반환한다.
class League(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    league_id : int
    league_name : str
    scoring_type : str
    last_changed_date : date
    teams: List[TeamBase] = Field(default_factory=list)

# 카운트 API 응답 전용 모델. 테이블별 전체 개수를 담는다.
class Counts(BaseModel):
    league_count : int
    team_count : int
    player_count : int