"""SQLAlchemy 2.0 ORM 모델 정의."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Player(Base):
    """판타지 풋볼에서 선택할 수 있는 선수."""

    __tablename__ = "player"

    player_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gsis_id: Mapped[str | None] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    position: Mapped[str] = mapped_column(String)
    last_changed_date: Mapped[date] = mapped_column(Date)

    performances: Mapped[list[Performance]] = relationship(back_populates="player")

    # team_player에는 last_changed_date가 있으므로 단순 secondary가 아니라
    # TeamPlayer association object를 유일한 쓰기 경로로 사용한다.
    team_players: Mapped[list[TeamPlayer]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    # 기존 player.teams 읽기/추가 인터페이스는 association_proxy로 유지한다.
    teams: AssociationProxy[list[Team]] = association_proxy(
        "team_players",
        "team",
        creator=lambda team: TeamPlayer(team=team),
    )


class Performance(Base):
    """선수 한 명의 특정 주차 판타지 포인트."""

    __tablename__ = "performance"

    performance_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    week_number: Mapped[str] = mapped_column(String)
    fantasy_points: Mapped[float] = mapped_column(Float)
    last_changed_date: Mapped[date] = mapped_column(Date)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.player_id"))

    player: Mapped[Player] = relationship(back_populates="performances")


class League(Base):
    """여러 판타지 팀이 경쟁하는 리그."""

    __tablename__ = "league"

    league_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    league_name: Mapped[str] = mapped_column(String)
    scoring_type: Mapped[str] = mapped_column(String)
    last_changed_date: Mapped[date] = mapped_column(Date)

    teams: Mapped[list[Team]] = relationship(back_populates="league")


class Team(Base):
    """사용자가 선수들을 조합해 만든 판타지 팀."""

    __tablename__ = "team"

    team_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_name: Mapped[str] = mapped_column(String)
    last_changed_date: Mapped[date] = mapped_column(Date)
    league_id: Mapped[int] = mapped_column(ForeignKey("league.league_id"))

    league: Mapped[League] = relationship(back_populates="teams")
    team_players: Mapped[list[TeamPlayer]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
    players: AssociationProxy[list[Player]] = association_proxy(
        "team_players",
        "player",
        creator=lambda player: TeamPlayer(player=player),
    )


class TeamPlayer(Base):
    """팀-선수 연결과 그 연결의 마지막 변경일을 함께 저장한다."""

    __tablename__ = "team_player"

    team_id: Mapped[int] = mapped_column(
        ForeignKey("team.team_id"), primary_key=True, index=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("player.player_id"), primary_key=True, index=True
    )
    last_changed_date: Mapped[date] = mapped_column(Date, default=date.today)

    team: Mapped[Team] = relationship(back_populates="team_players")
    player: Mapped[Player] = relationship(back_populates="team_players")