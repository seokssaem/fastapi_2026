# bus/pipeline.py
"""
대구 버스정류소 저장 파이프라인 통합 실행 (P08)
실행 전: P07 output/bus_stop.csv를 이 폴더의 input/ 아래로 복사해 두세요.
실행: python pipeline.py
"""

from database import init_db
from loader import load_from_csv
from verify import verify


def main():
    print("1) 저장 구조 준비 (정류소ID 기본키)")
    init_db()

    print("\n2) P07 결과(bus_stop.csv) 적재 (merge upsert)")
    load_from_csv()

    print("\n3) 적재 검증")
    verify()


if __name__ == "__main__":
    main()
