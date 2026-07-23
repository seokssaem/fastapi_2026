# =======================================================================
# show_test_results.py  (수업 데모용 임시 파일)
#
# 목적:
#   test_main.py에 있는 11개 테스트 함수가 실제로 어떤 응답을 받아오는지,
#   assert로 검증되기 "전"의 날것의 데이터를 눈으로 직접 보여주기 위한 스크립트.
#
# 실행 방법:
#   1) main.py가 있는 football 폴더 안에 이 파일을 넣는다.
#   2) PostgreSQL에 데이터가 seed 되어 있어야 한다 (seed_postgres_basic.py 실행 완료 상태)
#   3) 터미널에서 실행: python show_test_results.py
#
# 주의:
#   이 파일은 pytest 테스트 파일이 아니다. 그냥 결과를 눈으로 보여주기
#   위한 "출력용" 스크립트라서, 함수 이름이 test_로 시작하지 않는다.
#   (pytest는 test_로 시작하는 함수만 자동으로 찾아서 실행하기 때문)
#
#   리스트(선수 1018명, 성적 17306건 등)처럼 항목이 아주 많은 응답은
#   화면을 뒤덮지 않도록 앞의 몇 개 항목만 미리보기로 잘라서 보여준다.
# =======================================================================

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def _print_status(response):
    print(f"\n상태 코드(status_code): {response.status_code}")
    print("  -> 200이면 요청 성공, 다른 값이면 에러 (404, 422, 500 등)")


def _print_list_preview(data, preview_count: int = 3):
    """리스트 응답은 항목이 많을 수 있으니 앞부분만 미리보기로 출력한다."""
    print(f"\n응답 데이터 미리보기 (전체 {len(data)}건 중 앞 {preview_count}건):")
    for item in data[:preview_count]:
        print(f"  {item}")
    if len(data) > preview_count:
        print(f"  ... (나머지 {len(data) - preview_count}건 생략)")


def show_read_main():
    _print_header("[1] test_read_main - 루트 헬스 체크")
    response = client.get('/')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON): {data}")

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 메시지 : {data}   (기대값: {{'message': 'API 상태 확인 성공'}})")


def show_read_players():
    _print_header("[2] test_read_players - 전체 선수 목록 조회")
    response = client.get('/v0/players/?skip=0&limit=10000')
    _print_status(response)

    data = response.json()
    _print_list_preview(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 1018)")


def show_players_by_name():
    _print_header("[3] test_read_players_by_name - 이름/성으로 검색")
    response = client.get('/v0/players/?first_name=Bryce&last_name=Young')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON):")
    print(data)

    print(f"\n--- assert가 확인하는 값들 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 1)")
    print(f"data[0]의 player_id 값       : {data[0].get('player_id')}   (기대값: 2009)")


def show_player_with_id():
    _print_header("[4] test_read_players_with_id - player_id=1001 단건 조회")
    response = client.get('/v0/players/1001')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON):")
    print(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"data의 player_id 값 : {data.get('player_id')}   (기대값: 1001)")


def show_read_performances():
    _print_header("[5] test_read_performances - 전체 성적 목록 조회")
    response = client.get('/v0/performances/?skip=0&limit=20000')
    _print_status(response)

    data = response.json()
    _print_list_preview(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 17306)")


def show_performances_by_date():
    _print_header("[6] test_read_performances_by_date - 2024-04-01 이후 증분 조회")
    response = client.get(
        '/v0/performances/?skip=0&limit=20000&minimum_last_changed_date=2024-04-01'
    )
    _print_status(response)

    data = response.json()
    _print_list_preview(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 2711)")


def show_leagues_with_id():
    _print_header("[7] test_read_leagues_with_id - league_id=5002 상세 조회 (teams 포함)")
    response = client.get('/v0/league/5002/')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON):")
    print(data)

    teams = data.get('teams', [])
    print(f"\n--- assert가 확인하는 값 ---")
    print(f"data['teams']의 길이 : {len(teams)}   (기대값: 8)")


def show_read_leagues():
    _print_header("[8] test_read_leagues - 전체 리그 목록 조회")
    response = client.get('/v0/leagues/?skip=0&limit=500')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON):")
    print(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 5)")


def show_read_teams():
    _print_header("[9] test_read_teams - 전체 팀 목록 조회")
    response = client.get('/v0/teams/?skip=0&limit=500')
    _print_status(response)

    data = response.json()
    _print_list_preview(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 20)")


def show_teams_for_one_league():
    _print_header("[10] test_read_teams_for_one_league - league_id=5001 소속 팀만 조회")
    response = client.get('/v0/teams/?skip=0&limit=500&league_id=5001')
    _print_status(response)

    data = response.json()
    _print_list_preview(data)

    print(f"\n--- assert가 확인하는 값 ---")
    print(f"응답 리스트의 길이(len(data)) : {len(data)}   (기대값: 12)")


def show_counts():
    _print_header("[11] test_counts - 분석용 counts 엔드포인트")
    response = client.get('/v0/counts/')
    _print_status(response)

    data = response.json()
    print(f"\n응답 데이터 전체(JSON): {data}")

    print(f"\n--- assert가 확인하는 값들 ---")
    print(f"league_count : {data.get('league_count')}   (기대값: 5)")
    print(f"team_count   : {data.get('team_count')}   (기대값: 20)")
    print(f"player_count : {data.get('player_count')}   (기대값: 1018)")


if __name__ == "__main__":
    show_read_main()
    show_read_players()
    show_players_by_name()
    show_player_with_id()
    show_read_performances()
    show_performances_by_date()
    show_leagues_with_id()
    show_read_leagues()
    show_read_teams()
    show_teams_for_one_league()
    show_counts()

    print("\n" + "=" * 60)
    print("정리: pytest로 test_main.py를 실행하면 위 11가지 값들을 사람이")
    print("직접 눈으로 안 보고도, assert가 자동으로 비교해서")
    print("통과(.)/실패(F)를 순식간에 알려준다.")
    print("=" * 60)