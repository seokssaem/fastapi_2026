# ========================================================================
# ~/bigdata2026/fastapi/Streamlit/09_no_cache.py
#   
#   캐시가 없을 때의 경우
# ========================================================================
import streamlit as st
import pandas as pd
import time

def load_subway_data():
    time.sleep(2)
    return pd.read_csv('subway_long.csv', index_col=False)

st.title('캐싱 없이 실행해보기')

station = st.selectbox('역을 선택하세요.', ['동대구역', '반월당역', '범어역'])

# 역을 바꿀 때마다 매번 2초씩 다시 로딩
df = load_subway_data() 
st.write(f'{station} 데이터 로딩 완료')
st.dataframe(df.head())