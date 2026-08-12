'''
main.py

작업일자: 2026-08-11
작업자: 김나현
목적: train.py로 만든 festival_model.joblib를 실제로 사용하는 사용자 화면 코드 (웹페이지 화면), 시각적
        조건에 따른 축제 방문자수를 예측한다.
'''
import sys
import os
import streamlit as st

# pages_src 폴더를 파이썬 import 경로(sys.path)에 직접 추가한다.
#   --> streamlit이 지원이 안되어서 우리가 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages_src'))

st.set_page_config(
    page_title='전국 축제 행사 기획지원 대시보드',
    page_icon='🎡',
    layout='wide'
)

# --- 페이지 등록 ---
predict_page = st.Page('pages/predict_visitor_app.py', title='방문객 수 예측', icon='🎡')
search_page = st.Page('pages/search_festival_app.py', title='전국 문화축제 행사 빠른검색', icon='🔎')
deep_search_page = st.Page('pages/deep_search_festival_app.py', title='전국 문화축제 행사 상세검색', icon='🔎')
trend_page = st.Page('pages/trend_festival_app.py', title='기간 및 대중교통 인프라 추이', icon='📊')

# --- 사이드바에 페이지 연결 : 각 섹션 제목이 함께 표시된다, 딕셔너리 형태로. ---
pg = st.navigation({ 
    '메인': [predict_page],
    '데이터 탐색': [search_page, deep_search_page],
    '기타': [trend_page]
})

pg.run()