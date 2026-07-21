# ========================================================================
# ~/bigdata2026/fastapi/Streamlit/06_multiselect_slider.py
#   
#   Streamlit 라이브러리 기초 실습
#
#       - 입력 위젯 (다중 선택 박스, 숫자 슬라이더 등)
# ========================================================================
import streamlit as st
from datetime import time

# 다중 선택 박스
st.title('Streamlit 입력 위젯 실습')
st.divider()

st.subheader('1. 다중 선택 박스 퀴즈')

fruits = st.multiselect(
    'Q1. 과일을 모두 선택하세요.(복수 정답 가능):',
    ['사과', '토마토', '당근', '바나나']
)

correct = {'사과', '토마토', '바나나'}  # 세트(set)

if set(fruits) == correct:
    st.write('완벽해요! 모두 맞았습니다!')
else:
    st.write('다시 선택해보세요!')

st.divider()
st.subheader('2. 숫자 슬라이더')

# 0부터 100까지 점수를 슬라이더로 입력받는다.
score = st.slider('Your score is....', 0, 100, 1)  # 기본값은 1

st.text(f'Score : {score}')

st.divider()
if score >= 80:
    st.write('좋은 점수입니다!')
elif score >= 60:
    st.write('조금만 더 연습해 봅시다!')
else:
    st.write('기초부터 다시 복습해 봅시다!')


st.divider()
st.subheader('3. 시간 범위 슬라이더')

start_time, end_time = st.slider(
    'Working time is ...',
    min_value=time(0),
    max_value=time(23),
    value=(time(9), time(18)),
    format='HH:mm'
)

st.text(f'Working time : {start_time}, {end_time}')

st.divider()
st.subheader('추가 실습')

animals = st.multiselect(
    'Q. 동물을 모두 선택하세요.',
    ['강아지', '자동차', '고양이', '책상']
)

correct_animals = {'강아지', '고양이'}

if set(animals) == correct_animals:
    st.write('모두 맞았습니다!')
else:
    st.write('다시 선택해보세요!')



st.divider()
time1, time2 = st.slider(
    'Working time...', min_value=time(0), max_value=time(23), value=(time(10), time(17)),
    format='HH:mm'
)
st.text(f'Working time : {time1}, {time2}')