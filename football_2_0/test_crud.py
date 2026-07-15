"""SQLAlchemy 도우미 함수 테스트"""
import pytest
from datetime import date

import crud
from database import SessionLocal

# min_last_changed_date 테스트를 위해 2024-04-01 테스트 날짜 사용
test_date = date(2024,4,1)

@pytest.fixture(scope="function")
def db_session():
    """데이터베이스 세션을 시작하고 완료 후 닫는다"""
    session = SessionLocal()
    yield session
    session.close()

def test_get_player(db_session):
    """첫 번째 선수를 가져올 수 있는지 테스트"""
    player = crud.get_player(db_session, player_id = 1001)
    assert player.player_id == 1001

def test_get_players(db_session):
    """데이터베이스의 선수 수가 예상과 일치하는지 테스트"""
    players = crud.get_players(db_session, skip=0, limit=10000,
                                min_last_changed_date=test_date)
    assert len(players) == 1018

def test_get_players_by_name(db_session):
    """이름으로 선수를 검색했을 때 예상과 일치하는지 테스트"""
    players = crud.get_players(db_session, first_name="Bryce", last_name="Young")
    assert len(players) == 1
    assert players[0].player_id == 2009


def test_get_all_performances(db_session):
    """데이터베이스의 모든 성적 기록 개수가 예상과 일치하는지 테스트"""
    performances = crud.get_performances(db_session, skip=0, limit=18000)
    assert len(performances) == 17306

def test_get_new_performances(db_session):
    """특정 날짜 이후 업데이트된 성적 기록 개수가 예상과 일치하는지 테스트"""
    performances = crud.get_performances(db_session, skip=0, limit=10000, 
                                         min_last_changed_date=test_date)
    assert len(performances) == 2711

def test_get_league(db_session):
    """특정 리그를 가져올 수 있는지 테스트"""
    league = crud.get_league(db_session, league_id = 5002)
    assert league.league_id == 5002
    assert len(league.teams) == 8



def test_get_leagues(db_session):
    """데이터베이스의 리그 수가 예상과 일치하는지 테스트"""
    leagues = crud.get_leagues(db_session, skip=0, limit=10000, min_last_changed_date=test_date)
    assert len(leagues) == 5


def test_get_teams(db_session):
    """데이터베이스의 팀 수가 예상과 일치하는지 테스트"""
    teams = crud.get_teams(db_session, skip=0, limit=10000, min_last_changed_date=test_date)
    assert len(teams) == 20

def test_get_teams_for_one_league(db_session):
    """데이터베이스의 리그 수가 예상과 일치하는지 테스트"""
    teams = crud.get_teams(db_session, league_id=5001)
    assert len(teams) == 12
    assert teams[0].league_id == 5001

def test_get_team_players(db_session):
    """팀 기록에서 선수를 조회할 수 있으며, 첫 번째 팀에 7명의 선수가 있는지 테스트"""
    first_team = crud.get_teams(db_session, skip=0, limit=1000, min_last_changed_date=test_date)[0]
    assert len(first_team.players) == 7

#test the count functions
def test_get_player_count(db_session):
    player_count = crud.get_player_count(db_session)
    assert player_count == 1018

def test_get_team_count(db_session):
    team_count = crud.get_team_count(db_session)
    assert team_count == 20

def test_get_league_count(db_session):
    league_count = crud.get_league_count(db_session)
    assert league_count == 5