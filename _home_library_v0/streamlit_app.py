'''
home_library_v0 /streamlit_app.py
-----------------------------
예광탄 방식을 활용한 아주 얇은 코드
화면에 보여주는 역할
'''
import requests
import streamlit as st

# Streamlit이 이 주소로 HTTP 요청을 보내서 데이터를 주고 받는다.
# (FastAPI와 Streamlit은 완전히 다른 프로그램 두 개가 따로 실행되는 것 --> 서로 requests로 대화하는 구조)
API = 'http://localhost:8000' # 우리 FastAPI 서버 주소

st.title('우리집 책장 (개발 중)')

image = st.file_uploader('표지 사진')

# if st.button('등록') and image: # 등록 버튼을 누르고, 사진도 등록되어 있으면
#     # requests.post(...) --> FastAPI의 POST /books/scan 주소로 파일을 실러어서 요청을 보낸다.
#     # files={'image':(파일명, 파일내용바이트, 파일타입)} --> FastAPI에 uploadFile 매개변수 image와 일치
#     r = requests.post(
#         f'{API}/books/scan',
#         files={'image': (image.name, image.getvalue(), image.type)}
#     )

#     st.success(f'등록됨: {r.json()["title"]}' if r.ok else st.error('실패'))

# ----- and image 없애고, 버튼 클릭 안쪽에서 image 유무를 명시적으로 분기 -------
if st.button('등록'):
    if image is None:
        # 사진이 없는데 등록을 눌렀을 때 --> 경고만 띄우고 끝
        st.warning('먼저 표지 사진을 선택해주세요!')
    else:
        r = requests.post(
            f'{API}/books/scan',
            files={'image':(image.name, image.getvalue(), image.type)}
        )
        if r.ok:
            st.success(f'등록됨: {r.json()["title"]}')
        else:
            st.error(f'실패: {r.status_code}')

# -----------------------------------------------------------------------------------

st.subheader('등록된 책')

# requests.get(...) -> FastAPI의 GET /books를 호출해서 등록된 전체 목록(JSON)을 받아온다.
for book in requests.get(f'{API}/books').json():
    st.write(f'{book["title"]} ({book["recognition_status"]})')  # --> 책 제목 (상태)
