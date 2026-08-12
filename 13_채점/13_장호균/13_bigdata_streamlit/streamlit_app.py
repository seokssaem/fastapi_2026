"""
streamlit_app.py

작업일자: 2026-08-03
작업자: 김나현
목적: train.py로 만든 churn_model.joblib를 실제로 사용하는 사용자 화면 코드 (웹페이지 화면), 시각적
데이터 파일: ml_data/telecom_churn.csv

실행:
streamlit run streamlit_app.py

"""
# 라이브러리 불러오기
from pathlib import Path
import joblib
import pandas as pd
import streamlit as st

# 경로 설정
MODEL_PATH = Path(__file__).resolve().parent / 'festival_model.joblib'

# 브라우저 탭 제목과 아이콘 설정 -  반드시 다른 st.명령어보다 먼저 호출해야 한다.
st.set_page_config(page_title='고객 이탈 위험', page_icon='🎯')

st.title('🎯 지역축제 방문객 수 예측 시스템')
st.caption('상담 우선순위를 정하기 위한 의사결정 보고 도구이며, 예측만으로 불이익을 주면 안됩니다.')

# 모델파일이 존재하는지 확인
if not MODEL_PATH.exists():
    st.error('모델 파일이 없습니다. 터미널에서 `python make_model.py`를 먼저 실행하세요.')
    st.stop() # 이 지점에서 스크립트 실행을 멈춘다. 추가 에러 방지

# 저장했던 전처리 + 모델 그대로 복원
model = joblib.load(MODEL_PATH)

with st.form('customer'):
    duration = st.number_input('행사기간',0,100,3)
    bus = st.number_input('버스정류장수',0,100000, 10000)
    site = st.checkbox('홈페이지 주소 유무')
    subway = st.checkbox('지하철유무')

    # selectbox 위젯 : 미리 정해진 값 중 하나만 고르게 한다.
    #                   train.py에서 학습할 때 지정한 데이터와 같아야 한다.
    # contract = st.selectbox('계약 유형',['month-to-month','one-year','tow-year'])
    # region = st.selectbox('지역',['Gyeonggi','Seoul','Other'])

    # 폼 안에서 유일하게 실행을 시작하게 하는 버튼
    submitted = st.form_submit_button('방문객수 예측')

# 버튼을 클릭 했다면
if submitted:
    # 사용자가 입력한 값들로 1행짜리 데이터 프레임 생성
    row = pd.DataFrame([{
        '행사기간': duration,
        '버스정류장수' : bus,
        '홈페이지주소' : int(site),
        '지하철유무' : int(subway),
    }])

    # predict_proba(row): [[비이탈 확률, 이탈 확률]] 형태의 2차원 배열 반환
    # [0,1] 0번째 행(유일한 입력 고객), 1번째 열 (이탈=1일 확률)
    pred = model.predict(row)[0]

    # st.metric 위젯 : 큰 숫자 형태로 강조 표시
    st.metric(f'예상 방문객 수 :', f'{pred}')

    # st.progress(probability) # 0~1사이의 값을 막대 형태로 시각화

    st.info('확률이 높다면 고객의 실제 불편을 먼저 확인하고 적절한 유지 상담을 진행하세요.')