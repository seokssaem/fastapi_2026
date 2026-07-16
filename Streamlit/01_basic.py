# ========================================================================
# ~/bigdata2026/fastapi/Streamlit/01_basic.py
#   
#   Streamlit 라이브러리 기초 실습
#
#   Streamlit??
#       - 파이썬 코드만으로 웹페이지(대시보드, 데이터시각화 등)을 쉽게 만들
#         수 있도록 도와주는 파이썬 라이브러리
#       - 위젯 단위(버튼 클릭, 슬라이더 이동, 제목 등)
#
# ========================================================================

# 라이브러리 불러오기
import streamlit as st

st.title('내 생애 첫 대시보드!!')
st.write('파이썬 코드가 웹사이트가 되었습니다!!')

st.title('This is title')
st.title('_이탤릭체 제목_ :blue[파랑색] 그리고 선글라스 이모지 :sunglasses: ')

st.header('This is header')
st.header('_이탤릭체 제목_ :red[빨강색ㅋㅋ] 그리고 선글라스 이모지 :sunglasses: ')

st.subheader('This is subheader')
st.subheader('_이탤릭체 제목_ :green[초록색ㅎㅎ] 그리고 선글라스 이모지 :sunglasses: ')

# st.write() --> 텍스트, 숫자, 표, 마크다운 등 여러 자료형을 자동으로 출력
st.write('---')  # 구분선

st.text('이것은 텍스트입니다! ') # 일반 텍스트를 그대로 출력

st.divider()  # 구분선