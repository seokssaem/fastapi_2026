# bus/verify.py
"""
적재 검증: NULL 여부, 대구 좌표 범위 이탈 여부, 위치구분 값 분포를 점검합니다.
대구 대략 경계: 위도 35.7~36.0 / 경도 128.4~128.8
"""

from sqlalchemy import text
from database import engine

GU_LIST = {"북구", "중구", "동구", "서구", "남구", "수성구", "달성군", "달서구", "기타"}


def verify():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bus_stop")).scalar()

        null_check = conn.execute(text("""
            SELECT COUNT(*) FILTER (WHERE 위도 IS NULL) AS null_lat,
                   COUNT(*) FILTER (WHERE 경도 IS NULL) AS null_lon
            FROM bus_stop
        """)).fetchone()

        out_of_range = conn.execute(text("""
            SELECT COUNT(*) FROM bus_stop
            WHERE 위도 NOT BETWEEN 35.7 AND 36.0
               OR 경도 NOT BETWEEN 128.4 AND 128.8
        """)).scalar()

        gu_values = conn.execute(text(
            "SELECT DISTINCT 위치구분 FROM bus_stop"
        )).fetchall()
        invalid_gu = [g[0] for g in gu_values if g[0] not in GU_LIST]

    print("===== 적재 검증 결과 =====")
    print(f"전체 건수          : {total:,}")
    print(f"위도 NULL 건수     : {null_check[0]}")
    print(f"경도 NULL 건수     : {null_check[1]}")
    print(f"좌표 범위 이탈 건수: {out_of_range}")
    print(f"위치구분 이상값    : {invalid_gu if invalid_gu else '없음'}")

    ok = (
        null_check[0] == 0
        and null_check[1] == 0
        and out_of_range == 0
        and not invalid_gu
    )
    print("검증 결과          :", "PASS ✅" if ok else "FAIL ❌")
    return ok


if __name__ == "__main__":
    verify()
