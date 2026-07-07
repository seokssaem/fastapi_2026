# 빅데이터 저장시스템 개발 - NCS
- 빅데이터 저장모델 설계
- 빅데이터 적재모듈 개발

---
## 대구 버스 노선 데이터 저장 시스템 실습

| 파일명 | 설명 |
|---|---|
|`medels.py` | SQRALchemy 테이블 모델 정의|
|`detabase.py` | DB 연결과 테이블 생성|
|`loader.py`|CSV 적재|
|`verify.py`|검증. 대상 테이블 정확히 조사|
|`pipeline.py`|통합 실행|
|`README.me`| 실행 방법과 설계 설명|
|`bus_nb.ipynb`|셀 단위로 실습(가장 먼저 실습)

---
### pgAdmin에서 데이터베이스 준비
```sql
CREATE DATABASE subapidb;
```

### 입력 파일 준비

|폴더|필요한 파일|
|---|---|
|`C:\Users\Administrator\bigdata2026\fastapi\storage_subway_busapi\02_sub\input\`|`sub_stop.csv`|


---

- 결과로 나온 파일 `sub_stop_.csv`를 사용한다.
- CSV 인코딩은 `utf-8-sig` 기준

---
#### 도입
> 지난 시간에는 데이터를 수집하고 변환하는 것이 목표!

> 그 데이터를 저장시스템에 맞게 다시 설계

    수집한 데이터를 그대로 넣는 것과 운영 가능한 저장 모델로 만드는 것은 다른다.

#### 지하철 모델 설명
> 지하철 데이터는 같은 역, 같은 날짜, 같은 시간대, 같은 승하차 구분이 한 번만 존재해야 한다.

>`id`가 있어도 UNIQUE 제약이 별도로 필요한다.

#### 검증 설명
> `verify.py` ---> SQL을 대신 실행하는 파일


