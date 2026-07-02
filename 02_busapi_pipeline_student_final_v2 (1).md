# P7. 빅데이터 수집시스템 개발  
## 대구 버스 정류소 데이터 수집 파이프라인 — 학생용 완성본

**주제:** 공공 API로 대구 버스 정류소 데이터를 수집하고, 변환·검증한 뒤 PostgreSQL과 CSV로 저장하기  
**API:** 국토교통부_(TAGO)_버스정류소정보 — `getSttnNoList`  
**data.go.kr:** https://www.data.go.kr/data/15098534/openapi.do  
**대구 cityCode:** `22`  
**저장 DB:** `busapidb` → `bus_stop`

---

## 이번 예제에서 배우는 것

| 단계 | 핵심 내용 | Python 도구 |
|---|---|---|
| 01 | API 키와 기본 설정 준비 | `dotenv`, `os` |
| 02 | API 1회 호출 테스트 | `requests.get()` |
| 03 | JSON 구조 확인 | `dict`, `list` |
| 04 | 전체 페이지 수집 | `for`, `math.ceil()` |
| 05 | DataFrame 만들기 | `pd.DataFrame()` |
| 06 | 컬럼명·자료형 정리 | `rename`, `to_numeric` |
| 07 | 파생 컬럼 추가 | `date.today()`, `apply()` |
| 08 | 데이터 검증 | `isnull`, `duplicated`, `between` |
| 09 | DB 저장 | `SQLAlchemy`, `to_sql()` |
| 10 | CSV 저장 | `to_csv()` |

---

## 전체 흐름

```text
API 호출
  ↓
JSON 응답 확인
  ↓
페이지 반복 수집
  ↓
DataFrame 생성
  ↓
컬럼명 / 자료형 정리
  ↓
수집일시 / 위치구분 추가
  ↓
데이터 검증
  ↓
PostgreSQL 저장
  ↓
CSV 저장
```

> 이 파일은 학생들이 따라가기 쉽도록 셀을 잘게 나누고, 복잡한 컴프리헨션을 줄인 버전입니다.


---
# 00. 환경 설정

## `.env` 파일 준비

프로젝트 폴더에 `.env` 파일을 만들고 아래처럼 작성합니다.

```text
TAGO_API_KEY=발급받은Decoding키전체붙여넣기
```

주의할 점입니다.

- data.go.kr의 **일반 인증키(Decoding)** 를 사용합니다.
- Encoding 키를 넣으면 인증 오류가 날 수 있습니다.
- `.env` 파일은 GitHub에 올리지 않습니다.
- `.gitignore`에 `.env`를 꼭 추가합니다.


```python
import math
import os
import time
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env 파일에서 API 키 불러오기
load_dotenv()
API_KEY = os.getenv("TAGO_API_KEY")

if API_KEY:
    print(f"✅ API 키 로드 완료: {API_KEY[:6]}...{API_KEY[-4:]}")
else:
    print("⚠️ .env 파일에 TAGO_API_KEY를 설정하세요.")

# API 기본 설정
BASE_URL = "http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList"
CITY_CODE = 22
ROWS_PER_PAGE = 1000
REQUEST_TIMEOUT = 10

# 저장 경로
BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "bus_stop.csv")

# PostgreSQL 설정
DB_URL = "postgresql://postgres:1234@localhost:5432/busapidb"
TABLE_NAME = "bus_stop"

print(f"pandas 버전: {pd.__version__}")
print(f"CSV 저장 경로: {OUTPUT_PATH}")
```


---
# 01. API 연결 테스트

먼저 5건만 가져와서 API 키와 URL이 정상인지 확인합니다.

여기서 중요한 실무 습관은 두 가지입니다.

```python
response = requests.get(..., timeout=10)
response.raise_for_status()
```

- `timeout=10`: 서버가 응답하지 않을 때 무한 대기하지 않게 합니다.
- `raise_for_status()`: HTTP 오류가 있으면 바로 알려줍니다.


```python
params = {
    "serviceKey": API_KEY,
    "pageNo": 1,
    "numOfRows": 5,
    "cityCode": CITY_CODE,
    "_type": "json",
}

response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
response.raise_for_status()

print(f"HTTP 상태코드: {response.status_code}")
print("✅ API 호출 성공")
```


---
# 02. JSON 구조 확인

공공 API는 보통 여러 단계로 감싸진 JSON을 반환합니다.

이번 API의 핵심 데이터 위치는 아래와 같습니다.

```text
response
  └─ body
      ├─ totalCount
      └─ items
          └─ item
```


```python
data = response.json()
body = data["response"]["body"]

print("body에 들어있는 키:", list(body.keys()))
print(f"전체 정류소 수: {body['totalCount']:,}개")

items = body["items"]["item"]

# 데이터가 1건이면 dict, 여러 건이면 list로 올 수 있습니다.
# 그래서 항상 list 형태로 맞춰줍니다.
if isinstance(items, dict):
    items = [items]

print(f"이번 테스트에서 받은 데이터 수: {len(items)}개")
print("첫 번째 정류소 데이터:")
items[0]
```


---
# 03. 전체 데이터 수집

API는 한 번에 모든 데이터를 주지 않고, 여러 페이지로 나누어 줍니다.

전체 페이지 수는 `math.ceil()`로 계산합니다.

```python
total_pages = math.ceil(total_count / ROWS_PER_PAGE)
```

예를 들어 전체 4,259건이고 한 페이지에 1,000건씩 받으면 총 5페이지입니다.


```python
total_count = body["totalCount"]
total_pages = math.ceil(total_count / ROWS_PER_PAGE)

print(f"전체 건수: {total_count:,}개")
print(f"페이지당 건수: {ROWS_PER_PAGE:,}개")
print(f"총 페이지 수: {total_pages}페이지")
```


```python
all_items = []

for page_no in range(1, total_pages + 1):
    params = {
        "serviceKey": API_KEY,
        "pageNo": page_no,
        "numOfRows": ROWS_PER_PAGE,
        "cityCode": CITY_CODE,
        "_type": "json",
    }

    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    page_body = response.json()["response"]["body"]

    # 마지막 페이지나 오류 상황에서 items가 비어 있을 수 있습니다.
    if not page_body.get("items"):
        print(f"ℹ️ {page_no}/{total_pages} 페이지: 데이터 없음")
        continue

    page_items = page_body["items"].get("item", [])

    # 1건만 오면 dict로 올 수 있으므로 list로 통일합니다.
    if isinstance(page_items, dict):
        page_items = [page_items]

    all_items.extend(page_items)

    print(f"✅ {page_no}/{total_pages} 페이지 수집 완료 → 누적 {len(all_items):,}건")

    # 공공 API에 너무 빠르게 반복 요청하지 않도록 잠깐 쉬어줍니다.
    time.sleep(0.2)

print("-" * 50)
print(f"전체 수집 완료: {len(all_items):,}건")
```


---
# 04. DataFrame 만들기

수집한 JSON 리스트를 pandas DataFrame으로 변환합니다.


```python
df_raw = pd.DataFrame(all_items)

print(f"DataFrame 크기: {df_raw.shape[0]:,}행 × {df_raw.shape[1]}열")
print("컬럼 목록:")
print(df_raw.columns.tolist())

df_raw.head()
```


```python
# 처음 5개만 보면 데이터가 한쪽으로 치우쳐 보일 수 있습니다.
# sample()로 랜덤 데이터도 확인해봅니다.
df_raw.sample(5, random_state=42)
```


---
# 05. 컬럼명 정리

API에서 받은 컬럼명은 영어 축약어라서 학생들이 보기 어렵습니다.
한글 컬럼명으로 바꿉니다.

| 원본 컬럼 | 변경 컬럼 |
|---|---|
| `citycode` | 도시코드 |
| `nodeid` | 정류소ID |
| `nodenm` | 정류소명 |
| `nodeno` | 정류소번호 |
| `gpslati` | 위도 |
| `gpslong` | 경도 |

`rename(columns=딕셔너리)`는 없는 컬럼을 자동으로 무시하므로 복잡하게 처리하지 않아도 됩니다.


```python
COLUMN_RENAME = {
    "citycode": "도시코드",
    "nodeid": "정류소ID",
    "nodenm": "정류소명",
    "nodeno": "정류소번호",
    "gpslati": "위도",
    "gpslong": "경도",
}

df = df_raw.rename(columns=COLUMN_RENAME)

print("변경 후 컬럼 목록:")
print(df.columns.tolist())

df.head()
```


---
# 06. 자료형 변환

API 데이터는 숫자처럼 보여도 문자열로 들어오는 경우가 많습니다.

그래서 위도와 경도는 숫자로 변환합니다.

```python
pd.to_numeric(..., errors="coerce")
```

- 숫자로 바꿀 수 있으면 숫자로 변환합니다.
- 바꿀 수 없으면 `NaN`으로 처리합니다.

`정류소번호`는 비어 있는 경우가 많으므로, 결측치를 허용하는 `Int64` 자료형을 사용합니다.


```python
if "위도" in df.columns:
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")

if "경도" in df.columns:
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

if "정류소번호" in df.columns:
    df["정류소번호"] = pd.to_numeric(df["정류소번호"], errors="coerce").astype("Int64")

print("자료형 변환 결과:")
print(df.dtypes)
```


---
# 07. 파생 컬럼 추가

API로 받은 원본 데이터에 분석용 컬럼을 추가합니다.

| 새 컬럼 | 설명 |
|---|---|
| 수집일시 | 데이터를 수집한 날짜 |
| 위치구분 | 위도·경도를 기준으로 가장 가까운 대구 행정구 |

### 위치구분을 왜 정류소명이 아니라 위도·경도로 판단할까?

처음에는 정류소명에 구 이름이 들어있는지(`"북구" in 정류소명`)로 판단했습니다.  
하지만 실제 정류소명에는 `동대구역`, `칠성시장`처럼 **구 이름이 아예 없는 경우가 훨씬 많아서** `기타`로 빠지는 정류소가 너무 많았습니다.

그래서 **위도·경도로 가장 가까운 구를 찾는 방식**으로 바꿉니다.

```text
정류소의 (위도, 경도) 좌표
        ↓
8개 구청 좌표 각각과의 거리 계산
        ↓
거리가 가장 짧은 구를 위치구분으로 선택
```

> ⚠️ **주의:** 아래 구청 좌표는 참고용 추정치입니다.  
> 실제 수업 전에 정확한 좌표로 바꿔서 사용하는 것을 권장합니다. 아래 두 가지 방법 중 편한 것을 사용하세요.
>
> **방법 1 — 카카오맵**
> 1. [map.kakao.com](https://map.kakao.com) 접속
> 2. 검색창에 `대구광역시 OO구청` 입력 후 검색
> 3. 검색 결과를 클릭해 지도에 마커가 표시되면, 그 지점을 **마우스 우클릭**
> 4. 팝업 메뉴에서 **"이 지점 좌표 복사"** 클릭 → 위도, 경도가 클립보드에 복사됨
> 5. 복사된 값을 `GU_CENTERS` 딕셔너리에 붙여넣기 (순서: 위도, 경도)
>
> **방법 2 — 구글맵**
> 1. [maps.google.com](https://maps.google.com) 접속
> 2. 검색창에 `대구 OO구청` 검색
> 3. 지도에 표시된 위치를 **마우스 우클릭**
> 4. 팝업 맨 위에 좌표 숫자(예: `35.8949, 128.5825`)가 바로 표시됨 → 클릭하면 복사됨
> 5. 첫 번째 숫자가 위도, 두 번째 숫자가 경도
>
> 8개 구·군 모두 같은 방법으로 반복하면 5분 이내에 끝납니다. 확인한 값으로 아래 `GU_CENTERS` 코드의 숫자만 교체하면 됩니다.


```python
# 수집일시 추가
df["수집일시"] = str(date.today())

print(f"수집일시: {df['수집일시'].iloc[0]}")
```


```python
# 대구 8개 구·군의 대략적인 중심 좌표 (참고용 추정치)
# ⚠️ 실제 수업 전 카카오맵/구글맵에서 정확한 구청 좌표로 교체 권장
GU_CENTERS = {
    "중구":   (35.8693, 128.6064),
    "동구":   (35.8797, 128.6284),
    "서구":   (35.8722, 128.5480),
    "남구":   (35.8422, 128.5824),
    "북구":   (35.8949, 128.5825),
    "수성구": (35.8283, 128.6248),
    "달서구": (35.8534, 128.5615),
    "달성군": (35.8007, 128.4844),
}


def get_gu_by_distance(lat, lon):
    """
    위도·경도를 기준으로 가장 가까운 대구 행정구를 찾아 반환합니다.

    거리 계산은 정밀한 지도 계산(구면 거리 등)이 아니라
    단순 유클리드 거리를 사용합니다. 수업 목적으로는 이 정도면 충분합니다.
    """
    if pd.isna(lat) or pd.isna(lon):
        return "기타"

    nearest_gu = None
    min_distance = None

    for gu, (gu_lat, gu_lon) in GU_CENTERS.items():
        # 단순 유클리드 거리: 두 좌표 차이의 제곱합에 루트
        distance = ((lat - gu_lat) ** 2 + (lon - gu_lon) ** 2) ** 0.5

        if min_distance is None or distance < min_distance:
            min_distance = distance
            nearest_gu = gu

    return nearest_gu


if "위도" in df.columns and "경도" in df.columns:
    df["위치구분"] = df.apply(
        lambda row: get_gu_by_distance(row["위도"], row["경도"]),
        axis=1,
    )

print("위치구분 분포:")
print(df["위치구분"].value_counts())
```


```python
print("최종 데이터 미리보기")
df.head()
```


---
# 08. 데이터 검증

DB에 저장하기 전에 데이터가 이상하지 않은지 확인합니다.

초급 수업에서는 검증 함수를 여러 개로 나누면 오히려 복잡해질 수 있습니다.  
그래서 이번 완성본에서는 `validate_data()` 함수 하나 안에서 순서대로 검사합니다.

검증 기준은 아래와 같습니다.

| 결과 | 의미 | 저장 여부 |
|---|---|---|
| PASS | 정상 | 저장 가능 |
| WARN | 경고, 하지만 수업에서는 허용 | 저장 가능 |
| FAIL | 반드시 수정 필요 | 저장 중단 |


```python
def validate_data(df):
    """버스 정류소 데이터의 기본 품질을 검증하고 결과표를 반환합니다."""
    results = []

    # 1. 필수 컬럼 확인
    required_columns = ["정류소ID", "정류소명", "위도", "경도", "수집일시", "위치구분"]
    missing_columns = []

    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)

    if missing_columns:
        results.append({
            "검사항목": "필수 컬럼 확인",
            "결과": "FAIL",
            "상세": f"누락 컬럼: {missing_columns}",
        })
    else:
        results.append({
            "검사항목": "필수 컬럼 확인",
            "결과": "PASS",
            "상세": "모든 필수 컬럼 존재",
        })

    # 2. 결측치 확인
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]

    if len(null_counts) > 0:
        results.append({
            "검사항목": "결측치 확인",
            "결과": "WARN",
            "상세": null_counts.to_dict(),
        })
    else:
        results.append({
            "검사항목": "결측치 확인",
            "결과": "PASS",
            "상세": "결측치 없음",
        })

    # 3. 정류소ID 중복 확인
    if "정류소ID" in df.columns:
        duplicate_count = df["정류소ID"].duplicated().sum()

        if duplicate_count > 0:
            results.append({
                "검사항목": "정류소ID 중복 확인",
                "결과": "FAIL",
                "상세": f"중복 {duplicate_count:,}건",
            })
        else:
            results.append({
                "검사항목": "정류소ID 중복 확인",
                "결과": "PASS",
                "상세": "중복 없음",
            })

    # 4. 위도·경도 자료형 확인
    dtype_issues = []

    for col in ["위도", "경도"]:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                dtype_issues.append(f"{col}: {df[col].dtype}")

    if dtype_issues:
        results.append({
            "검사항목": "위도·경도 자료형 확인",
            "결과": "FAIL",
            "상세": " | ".join(dtype_issues),
        })
    else:
        results.append({
            "검사항목": "위도·경도 자료형 확인",
            "결과": "PASS",
            "상세": "위도·경도 숫자형",
        })

    # 5. 대구 근처 좌표 범위 확인
    # 실제 공공데이터에는 인접 지역 정류소가 일부 섞일 수 있으므로 WARN으로 처리합니다.
    gps_issues = []

    if "위도" in df.columns:
        out_lat = df[~df["위도"].between(35.7, 36.1)]
        if len(out_lat) > 0:
            gps_issues.append(f"위도 범위 이탈 {len(out_lat):,}건")

    if "경도" in df.columns:
        out_lng = df[~df["경도"].between(128.4, 128.8)]
        if len(out_lng) > 0:
            gps_issues.append(f"경도 범위 이탈 {len(out_lng):,}건")

    if gps_issues:
        results.append({
            "검사항목": "좌표 범위 확인",
            "결과": "WARN",
            "상세": " | ".join(gps_issues),
        })
    else:
        results.append({
            "검사항목": "좌표 범위 확인",
            "결과": "PASS",
            "상세": "대구 근처 좌표 범위 내",
        })

    return pd.DataFrame(results)
```


```python
validation_report = validate_data(df)
validation_report
```


```python
fail_count = (validation_report["결과"] == "FAIL").sum()
warn_count = (validation_report["결과"] == "WARN").sum()
pass_count = (validation_report["결과"] == "PASS").sum()

print(f"PASS: {pass_count}개")
print(f"WARN: {warn_count}개")
print(f"FAIL: {fail_count}개")

if fail_count == 0:
    print("✅ 치명적인 오류가 없으므로 저장을 진행할 수 있습니다.")
else:
    print("❌ FAIL 항목이 있으므로 저장 전에 수정해야 합니다.")
```


---
# 09. PostgreSQL 저장

`FAIL`이 없을 때만 PostgreSQL에 저장합니다.

실습 전 확인합니다.

1. PostgreSQL 서버가 실행 중인지 확인
2. `busapidb` 데이터베이스가 있는지 확인
3. `DB_URL`의 비밀번호가 본인 PC와 맞는지 확인

```python
DB_URL = "postgresql://postgres:1234@localhost:5432/busapidb"
```

비밀번호가 다르면 `1234` 부분을 수정합니다.


```python
def save_to_postgresql(df, db_url, table_name):
    """DataFrame을 PostgreSQL 테이블로 저장합니다."""
    df_save = df.copy()

    # pandas 버전 차이에 안전하게 대응하기 위해 문자열 컬럼을 str로 정리합니다.
    for col in df_save.columns:
        if pd.api.types.is_string_dtype(df_save[col]):
            df_save[col] = df_save[col].astype(str)

    engine = create_engine(db_url)

    # DB 연결 테스트
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).fetchone()[0]
        print("✅ PostgreSQL 연결 성공")
        print(version[:80] + "...")

    # DataFrame을 DB 테이블로 저장
    df_save.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )

    # 저장 건수 확인
    with engine.connect() as conn:
        saved_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).fetchone()[0]

    print(f"✅ 저장 완료: {saved_count:,}행")
    print(f"DB: busapidb / table: {table_name}")
```


```python
if fail_count == 0:
    save_to_postgresql(df, DB_URL, TABLE_NAME)
else:
    print("❌ FAIL 항목이 있어 PostgreSQL 저장을 건너뜁니다.")
```


---
# 10. CSV 저장

CSV 파일도 함께 저장합니다.

`utf-8-sig`를 사용하면 Windows Excel에서 한글이 깨질 가능성이 줄어듭니다.


```python
os.makedirs(OUTPUT_DIR, exist_ok=True)

df.to_csv(OUTPUT_PATH, encoding="utf-8-sig", index=False)

print("✅ CSV 저장 완료")
print(f"경로: {OUTPUT_PATH}")
print(f"크기: {len(df):,}행 × {len(df.columns)}열")
```


---
# 11. 최종 결과 요약

마지막으로 오늘 만든 파이프라인 결과를 한 번에 확인합니다.


```python
print("=" * 60)
print("P7. 대구 버스 정류소 API 수집 파이프라인 결과")
print("=" * 60)
print(f"수집 방식     : TAGO REST API - getSttnNoList")
print(f"도시 코드     : {CITY_CODE} (대구)")
print(f"수집 건수     : {len(df):,}건")
print(f"컬럼 수       : {len(df.columns)}개")
print(f"수집일시      : {df['수집일시'].iloc[0]}")
print(f"CSV 저장 위치 : {OUTPUT_PATH}")
print(f"DB 저장 위치  : busapidb.{TABLE_NAME}")

if "위치구분" in df.columns:
    print("-" * 60)
    print("위치구분 분포 (전체)")
    print(df["위치구분"].value_counts())

if "위도" in df.columns and "경도" in df.columns:
    print("-" * 60)
    print(f"위도 범위: {df['위도'].min():.4f} ~ {df['위도'].max():.4f}")
    print(f"경도 범위: {df['경도'].min():.4f} ~ {df['경도'].max():.4f}")

print("=" * 60)
```


---
# 학생 체크리스트

| 번호 | 확인 내용 | 체크 |
|---:|---|:---:|
| 1 | `.env`에 TAGO_API_KEY를 넣었다 | ☐ |
| 2 | API 연결 테스트에서 HTTP 200이 나왔다 | ☐ |
| 3 | 전체 페이지 수집이 완료되었다 | ☐ |
| 4 | DataFrame 컬럼명이 한글로 바뀌었다 | ☐ |
| 5 | 위도·경도가 숫자형으로 변환되었다 | ☐ |
| 6 | 수집일시, 위치구분 컬럼이 추가되었다 | ☐ |
| 7 | 위치구분에서 `기타` 비율이 크게 줄었다 (위도·경도 기준 판정) | ☐ |
| 8 | 검증 결과에서 FAIL이 없다 | ☐ |
| 9 | PostgreSQL `busapidb.bus_stop` 테이블을 확인했다 | ☐ |
| 10 | `output/bus_stop.csv` 파일을 확인했다 | ☐ |

---

## 수업 포인트

이번 예제에서 학생들이 꼭 가져가야 할 핵심은 두 가지입니다.

> API 수집도 결국 CSV 수집과 같은 데이터 파이프라인이다.  
> 다만 API는 인증키, 요청 파라미터, JSON 구조, 페이지네이션을 추가로 다룬다.

> 문자열 매칭(`in`)보다 좌표 기반 거리 계산이 훨씬 안정적인 분류 방법이 될 수 있다.  
> 다만 좌표값 자체의 정확도에 결과가 좌우되므로, 기준 좌표는 항상 검증이 필요하다.

