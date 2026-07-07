# bus/loader.py
"""
P07 결과 파일(bus_stop.csv, 약 4,259행)을 bus_stop 테이블에 적재합니다.
정류소ID가 자연키(기본키)이므로 session.merge()만으로 upsert가 됩니다.
"""

import pandas as pd
from database import get_session
from models import BusStop

INPUT_CSV = "input/bus_stop.csv"   # P07 output/bus_stop.csv를 복사해서 사용


def load_from_csv(path: str = INPUT_CSV) -> dict:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["수집일시"] = pd.to_datetime(df["수집일시"], errors="coerce").dt.date
    df["정류소번호"] = pd.to_numeric(df["정류소번호"], errors="coerce")

    db = get_session()
    success = 0
    failed = 0

    # ⚠️ 커밋을 맨 마지막 한 번만 하면, 중간에 한 행이라도 실패할 때
    #    세션이 abort 상태가 되어 이후 모든 행이 연쇄 실패할 수 있습니다.
    #    행 단위로 커밋해서 실패한 행만 롤백되고 이전 성공분은 안전하게 남도록 합니다.
    for _, row in df.iterrows():
        try:
            stop = BusStop(
                정류소ID=str(row["정류소ID"]),
                정류소명=str(row["정류소명"]),
                정류소번호=(
                    int(row["정류소번호"]) if pd.notna(row["정류소번호"]) else None
                ),
                위도=float(row["위도"]) if pd.notna(row["위도"]) else None,
                경도=float(row["경도"]) if pd.notna(row["경도"]) else None,
                수집일시=row["수집일시"],
                위치구분=str(row["위치구분"]) if pd.notna(row["위치구분"]) else None,
            )
            db.merge(stop)  # merge = upsert (동일 정류소ID면 갱신, 없으면 삽입)
            db.commit()
            success += 1
        except Exception as e:
            db.rollback()
            failed += 1
            print(f"[loader] 적재 실패 - {row.get('정류소명')} / {e}")

    db.close()

    print(f"[loader] 적재 완료 — 성공: {success:,}건 / 실패: {failed:,}건")
    return {"success": success, "failed": failed}


if __name__ == "__main__":
    load_from_csv()
