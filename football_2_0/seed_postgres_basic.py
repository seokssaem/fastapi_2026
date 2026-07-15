from __future__ import annotations
 
import csv
from datetime import date
from pathlib import Path

from sqlalchemy import Integer, text
from sqlalchemy.orm import Session
 
from database import Base, engine
import models
 
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def parse_date(value: str) -> date:
    """
    CSV에서 읽은 날짜 문자열을 Python date 객체로 변환한다.
    """
    return date.fromisoformat(value)

def read_rows(filename: str) -> list[dict[str, str]]:
    """
    CSV 파일 하나를 읽어서 딕셔너리 리스트로 변환
 
    """
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
    

def quote_identifier(identifier: str) -> str:
    """
    PostgreSQL 식별자(테이블명/컬럼명)를 안전하게 큰따옴표로 감싼다.

    """
    return '"' + identifier.replace('"', '""') + '"'
     
def reset_primary_key_sequences(connection, tables) -> None:
    """
    CSV로 명시적 id를 넣은 뒤, PostgreSQL 자동 증가 시퀀스를
    "테이블의 현재 최댓값" 기준으로 다시 맞춰준다.
 
    동작 원리를 한 줄씩 설명하면 다음과 같다.
    """
    # database.Base.metadata.sorted_tables로 넘어온 테이블들을
    # (player, league, team, team_player, performance) 순서로 하나씩 검사한다.
    for table in tables:
        # 이 테이블의 기본키 컬럼 목록. player처럼 컬럼 1개짜리 단일
        # 기본키도 있고, team_player처럼 (team_id, player_id) 두 개를
        # 묶어서 쓰는 복합 기본키도 있다.
        primary_key_columns = list(table.primary_key.columns)
 
        # team_player처럼 기본키가 2개 이상(복합키)이면 애초에 "자동 증가
        # 시퀀스"라는 개념 자체가 없다. 그런 값은 CSV에서 그대로 명시적으로
        # 넣는 값이지, PostgreSQL이 알아서 채워주는 값이 아니기 때문이다.
        # 그래서 복합키 테이블은 이 보정 대상에서 건너뛴다.
        if len(primary_key_columns) != 1:
            continue
 
        column = primary_key_columns[0]
 
        # 기본키가 하나뿐이어도, 그 타입이 정수(Integer)가 아니면
        # 자동 증가 시퀀스 대상이 아니므로 역시 건너뛴다.
        if not isinstance(column.type, Integer):
            continue
 
        # pg_get_serial_sequence(테이블명, 컬럼명)
        # --------------------------------------------------------------
        # "이 테이블의 이 컬럼이 SERIAL/IDENTITY로 만들어졌다면, 그 뒤에서
        # 실제로 값을 채워주는 시퀀스 객체의 이름이 뭐야?"를 PostgreSQL에게
        # 직접 물어보는 내장 함수다. 우리가 시퀀스 이름을 직접 외우거나
        # 추측할 필요 없이, DB가 정답을 알려준다.
        sequence_name = connection.execute(
            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": table.name, "column_name": column.name},
        ).scalar()
 
        # 만약 이 컬럼이 SERIAL/IDENTITY 방식으로 만들어진 게 아니라면
        # (예: 기본키인데 자동 증가가 아예 아닌 경우) None이 돌아온다.
        # 그런 경우는 보정할 시퀀스 자체가 없으므로 그냥 넘어간다.
        if not sequence_name:
            continue
 
        table_identifier = quote_identifier(table.name)
        column_identifier = quote_identifier(column.name)
 
        # MAX(컬럼) — 지금 테이블에 실제로 들어있는 가장 큰 id 값을 구한다.
        # 예: player 테이블에 1001~1050이 들어있다면 max_value는 1050이다.
        max_value = connection.execute(
            text(f"SELECT MAX({column_identifier}) FROM {table_identifier}")
        ).scalar()
 
        if max_value is None:
            connection.execute(
                text("SELECT setval(:sequence_name, 1, false)"),
                {"sequence_name": sequence_name},
            )
        else:
            connection.execute(
                text("SELECT setval(:sequence_name, :max_value, true)"),
                {"sequence_name": sequence_name, "max_value": int(max_value)},
            )
            print(
                f"[seed] sequence 재설정: {table.name}.{column.name} -> {max_value}"
            )
      

def seed() -> None:
    """
    PostgreSQL 테이블을 새로 만들고, CSV 데이터를 순서대로 적재한다.
 
    적재 순서가 중요하다.
    테이블 사이에는 외래키(ForeignKey) 관계가 있다.
 
    - team.league_id는 league.league_id를 참조한다.
    - performance.player_id는 player.player_id를 참조한다.
    - team_player.team_id는 team.team_id를 참조한다.
    - team_player.player_id는 player.player_id를 참조한다.
        참조 당하는 부모 테이블을 먼저 넣고,
            참조하는 자식 테이블을 나중에 넣어야 한다.
 
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
 
    # Session은 SQLAlchemy ORM 객체를 DB에 저장하는 작업공간
    # with블록을 쓰면 작업이 끝난 뒤 세션이 자동으로 정리된다.
    with Session(engine) as session:
        # 1. player 테이블 적재
        # player는 performance와 team_player에서 참조하므로 먼저 넣는다.
        players = [
            models.Player(
                player_id=int(row["player_id"]),
                gsis_id=row["gsis_id"] or None,
                first_name=row["first_name"],
                last_name=row["last_name"],
                position=row["position"],
                last_changed_date=parse_date(row["last_changed_date"]),
            )
            for row in read_rows("player_data.csv")
        ]
        session.add_all(players)
 
        # 2. league 테이블 적재 - league는 team에서 참조하므로 team보다 먼저
        leagues = [
            models.League(
                league_id=int(row["league_id"]),
                league_name=row["league_name"],
                scoring_type=row["scoring_type"],
                last_changed_date=parse_date(row["last_changed_date"]),
            )
            for row in read_rows("league_data.csv")
        ]
        session.add_all(leagues)
 
        # flush() 아직 commit은 하지 않았지만, 현재 세션에 쌓인 INSERT를 DB로 보낸다
        # player와 league 행이 같은 트랜잭션 안에서 실제 테이블에 먼저 보이게 된다.
        # 뒤에서 team, team_player처럼 외래키를 가진 테이블을 넣을 때
        # 참조할 부모행이 아직 없다는 오류를 피하고, 실행 순서 파악도 쉽다.
        session.flush()
 
        # 3. team 테이블 적재 - Team은 league_id를 통해 League에 속한다.
        teams = [
            models.Team(
                team_id=int(row["team_id"]),
                team_name=row["team_name"],
                league_id=int(row["league_id"]),
                last_changed_date=parse_date(row["last_changed_date"]),
            )
            for row in read_rows("team_data.csv")
        ]
        session.add_all(teams)
 
        session.flush()
 
        # 4. team_player 연결 테이블 적재
        # Team과 Player의 다대다 관계를 표현하는 중간 테이블
        team_players = [
            models.TeamPlayer(
                team_id=int(row["team_id"]),
                player_id=int(row["player_id"]),
                last_changed_date=parse_date(row["last_changed_date"]),
            )
            for row in read_rows("team_player_data.csv")
        ]
        session.add_all(team_players)
 
        # 5. performance 테이블 적재
        # Performance는 player_id로 Player를 참조한다.
        performances = [
            models.Performance(
                performance_id=int(row["performance_id"]),
                week_number=row["week_number"],
                fantasy_points=float(row["fantasy_points"]),
                player_id=int(row["player_id"]),
                last_changed_date=parse_date(row["last_changed_date"]),
            )
            for row in read_rows("performance_data.csv")
        ]
        session.add_all(performances)
 
        # SQLAlchemy 세션에 "저장 예정" 상태로 올라간 것이다.
        # commit() 을 호출해야 PostgreSQL 테이블에 INSERT가 반영된다.
        session.commit()      

    with engine.begin() as connection:
            reset_primary_key_sequences(connection, Base.metadata.sorted_tables)
    
    print('[seed] PostgreSQL 초기 데이터 적재 완료!')
    print(f'[seed] player: {len(players):,} rows')
    print(f'[seed] league: {len(leagues):,} rows')
    print(f'[seed] team: {len(teams):,} rows')
    print(f'[seed] team_player: {len(team_players):,} rows')
    print(f'[seed] performance: {len(performances):,} rows')
    
 
if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 seed() 를 호출한다.
    # 다른 파일에서 import할 때 DB초기화가 자동 실행되는 것을 막아준다.
    seed()        