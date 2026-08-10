# =============================================================
# 10장 의료 예약 노쇼 + 11장 주식 시계열 분석 + FastAPI 서버 연동 예제
# 교재: 데이터분석을 위한 전처리와 시각화 with 파이썬 (길벗캠퍼스)
# 접목: 의료 노쇼 분석 + 주식 이동평균 결과를 FastAPI 엔드포인트로 제공
#
# [실행 방법]
#   1. 패키지 설치: pip install fastapi uvicorn pandas finance-datareader matplotlib seaborn
#   2. 서버 실행:   uvicorn ch10_11_medical_stock_api:app --reload
#   3. 문서 확인:   http://127.0.0.1:8000/docs
# =============================================================

import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from fastapi import FastAPI, HTTPException, Query
from typing import Optional

# ── FastAPI 앱 생성 ──────────────────────────────────────────
app = FastAPI(
    title="10·11장 의료 노쇼 & 주식 시계열 분석 API",
    description="교재 10~11장 예제(의료 예약 노쇼 분석 + 주식 시계열)를 FastAPI로 확장한 실습입니다.",
    version="1.0.0",
)

# ── 전역 변수 ─────────────────────────────────────────────────
_medical: pd.DataFrame = None    # 의료 노쇼 데이터 (10장)
_stock: pd.DataFrame = None      # 주식 월별 데이터 (11장)


# ═══════════════════════════════════════════════════════════
# [10장] 의료 예약 노쇼 데이터 전처리 함수
# ═══════════════════════════════════════════════════════════
def load_medical() -> pd.DataFrame:
    """
    교재 10장의 medical.csv 전처리 과정을 함수로 구현합니다.
    - 나이 음수 제거
    - No-show를 0/1 숫자로 변환
    - 예약일과 진료일 차이(waiting_day) 계산
    - 이상치(나이>110, 대기일<0) 제거
    """
    try:
        df = pd.read_csv("medical.csv")

        # 나이가 0 미만인 이상 데이터 제거
        df = df[df["Age"] >= 0]

        # No-show: 'Yes'→1 (노쇼), 'No'→0 (정상 출석)
        df["No-show"] = df["No-show"].map({"Yes": 1, "No": 0})

        # 날짜 컬럼을 datetime으로 변환
        df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"])
        df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"])

        # 대기일(예약일 - 스케줄 등록일) 계산
        df["waiting_day"] = (
            df["AppointmentDay"].dt.dayofyear - df["ScheduledDay"].dt.dayofyear
        )

        # 대기일이 음수인 이상치 제거 (예약이 진료보다 늦게 잡힌 경우)
        df = df[df["waiting_day"] >= 0]

        # 나이 이상치 제거 (110세 초과)
        df = df[df["Age"] <= 110]

        return df

    except FileNotFoundError:
        print("[서버 시작] medical.csv 없음 → 샘플 데이터 사용")
        return _make_sample_medical()


def _make_sample_medical() -> pd.DataFrame:
    """의료 샘플 데이터 생성 (파일 없을 때 데모용)."""
    np.random.seed(1)
    n = 500
    return pd.DataFrame({
        "PatientId": np.arange(n),
        "Age": np.random.randint(0, 90, n),
        "Gender": np.random.choice(["F", "M"], n),
        "No-show": np.random.choice([0, 1], n, p=[0.8, 0.2]),
        "SMS_received": np.random.choice([0, 1], n),
        "waiting_day": np.random.randint(0, 60, n),
        "Hipertension": np.random.choice([0, 1], n, p=[0.7, 0.3]),
        "Diabetes": np.random.choice([0, 1], n, p=[0.85, 0.15]),
        "Scholarship": np.random.choice([0, 1], n, p=[0.9, 0.1]),
    })


# # ═══════════════════════════════════════════════════════════
# # [11장] 주식 데이터 로드 함수 (FinanceDataReader)
# # ═══════════════════════════════════════════════════════════
# def load_stock(ticker: str = "AAPL", start: str = "2022") -> pd.DataFrame:
#     """
#     교재 11장의 FinanceDataReader를 활용해 주식 월별 데이터를 수집합니다.
#     - 한 달 간격으로 다운샘플링 (resample BM)
#     - 수익률(pct_change) 및 이동평균(rolling) 컬럼 추가
#     """
#     try:
#         import FinanceDataReader as fdr
#         df = fdr.DataReader(ticker, start)

#         # 월말 기준으로 다운샘플링 (Business Month End)
#         df_month = df.resample("BM").mean()

#         # 수익률 = (이번 달 종가 - 지난 달 종가) / 지난 달 종가
#         df_month["rtn"] = df_month["Close"].pct_change().round(4)

#         # 2개월 이동평균선 (rolling window=2)
#         df_month["MA"] = df_month["Close"].rolling(2).mean().round(2)

#         # JSON 직렬화를 위해 인덱스를 문자열로 변환
#         df_month.index = df_month.index.astype(str)
#         return df_month

#     except Exception:
#         print("[서버 시작] FinanceDataReader 없음 또는 오류 → 샘플 주식 데이터 사용")
#         return _make_sample_stock()


# def _make_sample_stock() -> pd.DataFrame:
#     """주식 샘플 데이터 생성 (라이브러리 없을 때 데모용)."""
#     np.random.seed(42)
#     dates = pd.date_range("2022-01-01", periods=24, freq="BM")
#     close = 150 + np.cumsum(np.random.normal(0, 5, 24))
#     df = pd.DataFrame({
#         "Close": close.round(2),
#         "rtn": pd.Series(close).pct_change().round(4).values,
#         "MA": pd.Series(close).rolling(2).mean().round(2).values,
#     }, index=dates.astype(str))
#     return df


# # ── 서버 시작 시 데이터 로드 ────────────────────────────────
# @app.on_event("startup")
# def startup_event():
#     global _medical, _stock
#     _medical = load_medical()
#     _stock = load_stock()
#     print(f"[서버 시작] 의료 데이터: {len(_medical)}행 | 주식 데이터: {len(_stock)}행")


# ────────────────────────────────────────────────────────────
# [공통] 기본 엔드포인트
# ────────────────────────────────────────────────────────────
@app.get("/", summary="API 기본 정보")
def root():
    return {
        "chapters": ["10장: 의료 예약 노쇼 분석", "11장: 주식 시계열 분석"],
        "docs": "http://127.0.0.1:8000/docs",
    }


# ════════════════════════════════════════════════════════════
# [10장] 의료 노쇼 분석 엔드포인트
# ════════════════════════════════════════════════════════════

@app.get("/medical/summary", summary="[10장] 의료 노쇼 기술통계")
def medical_summary():
    """
    교재 df.describe() + No-show 비율을 반환합니다.
    전체 환자 수, 노쇼 환자 수, 노쇼 비율을 확인할 수 있습니다.
    """
    total = len(_medical)
    no_show_count = int(_medical["No-show"].sum())   # 노쇼 환자 수
    show_count = total - no_show_count               # 정상 출석 환자 수

    return {
        "total_patients": total,
        "no_show": no_show_count,
        "show": show_count,
        # 소수점 4자리로 반올림하여 비율 계산
        "no_show_rate": round(no_show_count / total, 4),
        "age_stats": {
            "mean": round(float(_medical["Age"].mean()), 2),
            "min":  int(_medical["Age"].min()),
            "max":  int(_medical["Age"].max()),
        },
    }


@app.get("/medical/sms_effect", summary="[10장] SMS 수신 여부에 따른 노쇼율")
def medical_sms_effect():
    """
    교재의 SMS_received 별 노쇼 비율 분석 결과를 반환합니다.
    SMS를 받은 그룹과 받지 않은 그룹의 노쇼율을 비교해 보세요.
    """
    result = {}
    for sms_val in [0, 1]:
        subset = _medical[_medical["SMS_received"] == sms_val]
        no_show = int(subset["No-show"].sum())
        total = len(subset)
        result[f"SMS_{sms_val}"] = {
            "total": total,
            "no_show": no_show,
            "no_show_rate": round(no_show / total, 4) if total > 0 else 0,
        }
    return result


@app.get("/medical/gender_effect", summary="[10장] 성별에 따른 노쇼율")
def medical_gender_effect():
    """
    교재의 성별(Gender) 별 노쇼 비율 분석 결과를 반환합니다.
    여성과 남성 중 어느 쪽의 노쇼율이 높은지 확인해 보세요.
    """
    result = {}
    for gender in ["F", "M"]:
        subset = _medical[_medical["Gender"] == gender]
        no_show = int(subset["No-show"].sum())
        total = len(subset)
        result[gender] = {
            "total": total,
            "no_show": no_show,
            "no_show_rate": round(no_show / total, 4) if total > 0 else 0,
        }
    return result


@app.get("/medical/waiting_filter", summary="[10장] 대기일 조건 필터링")
def medical_waiting_filter(
    waiting_min: int = Query(default=0, description="최소 대기일"),
    waiting_max: int = Query(default=10, description="최대 대기일"),
    no_show_only: bool = Query(default=False, description="노쇼 환자만 조회"),
):
    """
    교재에서 no_show[no_show['waiting_day']<=10] 처럼
    대기일 범위로 필터링한 결과를 반환합니다.
    """
    result = _medical[
        (_medical["waiting_day"] >= waiting_min) &
        (_medical["waiting_day"] <= waiting_max)
    ]
    if no_show_only:
        result = result[result["No-show"] == 1]

    return {
        "waiting_range": f"{waiting_min}~{waiting_max}일",
        "no_show_only": no_show_only,
        "count": len(result),
        "no_show_rate": round(result["No-show"].mean(), 4),
        "data_sample": result.head(10).to_dict(orient="records"),
    }


# # ════════════════════════════════════════════════════════════
# # [11장] 주식 시계열 분석 엔드포인트
# # ════════════════════════════════════════════════════════════

# @app.get("/stock/data", summary="[11장] 주식 월별 데이터 조회")
# def stock_data():
#     """
#     교재 11장의 df_month 데이터(종가·수익률·이동평균)를 반환합니다.
#     """
#     data = _stock.reset_index()
#     data.columns = ["date"] + list(data.columns[1:])
#     return {
#         "rows": len(data),
#         "data": data.to_dict(orient="records"),
#     }


# @app.get("/stock/signal", summary="[11장] 상승/하락 신호 판단")
# def stock_signal():
#     """
#     교재 11장의 이동평균선(MA) 기반 매매 신호 판단 로직을 API로 구현합니다.
#     - 오늘 종가 > 이동평균선 → 상승 장
#     - 오늘 종가 < 이동평균선 → 하락 장
#     - 같은 경우 → 변화없음
#     """
#     # 이동평균 계산이 완료된 마지막 두 행 사용
#     last_ma = float(_stock["MA"].dropna().iloc[-2])    # 이전 이동평균
#     last_close = float(_stock["Close"].iloc[-1])        # 최근 종가

#     if last_close > last_ma:
#         signal = "상승 장 📈"
#     elif last_close < last_ma:
#         signal = "하락 장 📉"
#     else:
#         signal = "변화없음 ➡️"

#     return {
#         "latest_close": round(last_close, 2),
#         "moving_avg_prev": round(last_ma, 2),
#         "signal": signal,
#     }


# @app.get("/stock/chart", summary="[11장] 주가 + 이동평균선 차트 이미지")
# def stock_chart():
#     """
#     교재 11장의 df_month.iloc[:,[3,7]].plot() 을 PNG 이미지(Base64)로 반환합니다.
#     종가(Close)와 이동평균선(MA)을 한 차트에서 비교할 수 있습니다.
#     """
#     fig, ax = plt.subplots(figsize=(12, 5))

#     # 종가 라인
#     ax.plot(_stock.index, _stock["Close"], marker="o", label="Close (종가)", color="steelblue")
#     # 이동평균선 라인
#     ax.plot(_stock.index, _stock["MA"], marker="s", linestyle="--",
#             label="MA (이동평균)", color="tomato")

#     ax.set_title("Apple 주식 월별 종가 및 이동평균선")
#     ax.set_xlabel("날짜")
#     ax.set_ylabel("가격 (USD)")
#     ax.legend()
#     # x축 레이블이 겹치지 않도록 회전
#     plt.xticks(rotation=45, ha="right")
#     plt.tight_layout()

#     buf = io.BytesIO()
#     fig.savefig(buf, format="png", dpi=100)
#     plt.close(fig)
#     buf.seek(0)
#     img_b64 = base64.b64encode(buf.read()).decode("utf-8")

#     return {"image_base64": img_b64}


# @app.get("/stock/rolling", summary="[11장] 이동평균 기간 동적 설정")
# def stock_rolling(
#     window: int = Query(default=2, ge=1, le=12, description="이동평균 기간 (개월 수, 1~12)"),
# ):
#     """
#     교재의 df.rolling(window).mean() 을 동적으로 계산하여 반환합니다.
#     window 파라미터를 바꾸면서 이동평균이 어떻게 달라지는지 확인해 보세요.
#     """
#     rolling_ma = _stock["Close"].rolling(window).mean().round(2)
#     result = pd.DataFrame({
#         "date": _stock.index,
#         "close": _stock["Close"].round(2),
#         f"MA_{window}": rolling_ma,
#     }).dropna()   # rolling 초기 NaN 제거

#     return {
#         "window": window,
#         "data": result.to_dict(orient="records"),
#     }
