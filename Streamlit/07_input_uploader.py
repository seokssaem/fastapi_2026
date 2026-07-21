# ========================================================================
# ~/bigdata2026/fastapi/Streamlit/07_input_uploader.py
#   
#   Streamlit 라이브러리 기초 실습
#
#       - 입력 위젯 (텍스트 입력, 파일 업로더 등)
# ========================================================================
import streamlit as st
import pandas as pd

# 1. 텍스트 입력 : 좋아하는 포켓몬 이름 받기
string1 = st.text_input(
    '좋아하는 포켓몬은??',
    placeholder='당신이 가장 좋아하는 포켓몬 이름을 적어주세요!',
    max_chars=32
)
if string1:
    st.text(f'Your answer is {string1}')

# 2. 비밀번호 입력 : 싫어하는 음식 받기 (입력 내용을 숨긴다)
string2 = st.text_input(
    '싫어하는 음식은??',
    placeholder='당신이 가장 싫어하는 음식을 하나 적어주세요.',
    max_chars=32,
    type='password'
)
if string2:
    st.text(f'Your answer is {string2}')

st.divider()

# 3. 파일 업로더 : csv파일만 업로드 가능하도록 설정
file = st.file_uploader(
    'Choose a file',
    type='csv',
    accept_multiple_files=False
)

if file is not None:
    df = pd.read_csv(file)
    st.write(df)