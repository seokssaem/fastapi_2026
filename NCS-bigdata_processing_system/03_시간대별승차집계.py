# ================================================================================
# NCS-bigdata_processing_system/03_시간대별승차집계.py
#   [오늘의 복습 문제] 배치 처리 3번
#
#   - 승차 데이터만 사용하여 시간대별 승차 인원을 집계합니다.
#
# 실행결과 : python 03_시간대별승차집계.py
# [batch] 시간대별 배치 처리 시작
# [batch] 입력 테이블 확인 완료: subway_raw 1,260,000건
# [batch] 시간대별 승차 집계 완료: traffic_hour_summary
# [batch] 시간대별 배치 처리 완료
# ================================================================================
from database import subway_engine, execute_sql, table_count

# 1. 실행 전에 subway_raw 테이블의 존재 여부와 데이터 건수를 확인합니다.
def check_subway_input() -> None:
    """subway_raw 테이블의 존재 여부와 데이터 건수를 확인하는 함수"""
    try:
        count = table_count(subway_engine, 'subway_raw')
    except Exception as exc:
        raise RuntimeError("subway_raw 테이블을 확인할 수 없습니다."
                           "DB 연결과 원본 데이터 적재 여부를 확인하세요.") from exc
    
    if count == 0:
        raise RuntimeError("subway_raw 테이블에 데이터가 없습니다.")
    
    print(f'[batch] 입력 테이블 확인 완료: subway_raw {count:,}건')

