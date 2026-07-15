"""SQLAlchemy 2.0 SELECT 기반 조회 함수."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

import models


def get_player(db: Session, player_id: int):
    """기본키로 선수 한 명을 조회한다."""
    return db.get(models.Player, player_id)


def get_players(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    min_last_changed_date: date | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
):
    """선수 목록에 선택 조건을 추가하고 페이지 단위로 조회한다."""
    stmt = select(models.Player)
    if min_last_changed_date:
        stmt = stmt.where(models.Player.last_changed_date >= min_last_changed_date)
    if first_name:
        stmt = stmt.where(models.Player.first_name == first_name)
    if last_name:
        stmt = stmt.where(models.Player.last_name == last_name)
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_performances(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    min_last_changed_date: date | None = None,
):
    stmt = select(models.Performance)
    if min_last_changed_date:
        stmt = stmt.where(
            models.Performance.last_changed_date >= min_last_changed_date
        )
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_league(db: Session, league_id: int | None = None):
    if league_id is None:
        return None
    return db.get(models.League, league_id)


def get_leagues(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    min_last_changed_date: date | None = None,
    league_name: str | None = None,
):
    stmt = select(models.League).options(joinedload(models.League.teams))
    if min_last_changed_date:
        stmt = stmt.where(models.League.last_changed_date >= min_last_changed_date)
    if league_name:
        stmt = stmt.where(models.League.league_name == league_name)
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).unique().all()


def get_teams(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    min_last_changed_date: date | None = None,
    team_name: str | None = None,
    league_id: int | None = None,
):
    stmt = select(models.Team).options(
        selectinload(models.Team.team_players).joinedload(models.TeamPlayer.player)
    )
    if min_last_changed_date:
        stmt = stmt.where(models.Team.last_changed_date >= min_last_changed_date)
    if team_name:
        stmt = stmt.where(models.Team.team_name == team_name)
    if league_id:
        stmt = stmt.where(models.Team.league_id == league_id)
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def _count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def get_player_count(db: Session):
    return _count(db, models.Player)


def get_team_count(db: Session):
    return _count(db, models.Team)


def get_league_count(db: Session):
    return _count(db, models.League)