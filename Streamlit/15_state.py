# =====================================================================================
# ~/bigdata2026/fastapi/Streamlit/15_state.py
#   
# session state 
#   - 위젯을 조작할 때마다 일반 파이썬 변수가 초기화 되는 문제를 해결한다.
#   - st.sesstion_state로 재실행 사이의 값을 유지할 수 있다.
#   - 콜백 함수와 함께 사용할 수 있다.
# ====================================================================================
import streamlit as st

st.title('카운터 (sesstion state 적용)')

# st.session_state : 브라우저 탭(세션) 하나에 묶여서 재실행되어도 값이 사라지지 않는 
#                       딕셔너리 형태의 특수 저장소
if 'count' not in st.session_state:
    st.session_state.count = 0 

if st.button('+1'):
    st.session_state.count += 1  

st.write(f'현재 카운트 : {st.session_state.count}')