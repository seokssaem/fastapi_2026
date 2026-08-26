'''
home_library_v0 / streamlit_app.py
-----------------------------
"실습 변형: ISBN 직접 조회 -> 사진 업로드" 2단계 구성

기존 streamlit_app.py에 1단계(ISBN 텍스트 조회) 섹션을 새로 추가하고,
기존 2단계(사진 업로드, v3~v6에서 써왔던 부분)는 그대로 아래에 둔다.
'''
import requests
import streamlit as st

API = 'http://localhost:8000'

st.title('우리집 책장 (개발 중)')

# ══════════════════════════════════════════════════════════
# ▼▼▼ 1단계: ISBN 코드만 입력해서 조회 결과 먼저 확인해보기 ▼▼▼
# ══════════════════════════════════════════════════════════
st.header('1단계: ISBN으로 바로 조회해보기')
st.caption('사진 없이 ISBN 숫자만 넣어서, 서지정보 API가 잘 연결됐는지 먼저 확인합니다.')

isbn_input = st.text_input('ISBN 입력 (예: 9791190090018)')

if st.button('조회하기'):
    if not isbn_input:
        # 아무것도 입력 안 하고 눌렀을 때 -> 경고만 띄우고 끝
        st.warning('ISBN을 입력해주세요!')
    else:
        # requests.get(...) --> FastAPI의 GET /books/lookup에 isbn을 쿼리파라미터로 실어 보낸다.
        # params={'isbn': isbn_input} --> 자동으로 ?isbn=9791190090018 형태의 URL로 만들어줌
        r = requests.get(f'{API}/books/lookup', params={'isbn': isbn_input})

        if r.ok:
            # 성공하면 JSON으로 온 title/author/publisher를 화면에 예쁘게 표시
            data = r.json()
            st.success(f'**{data["title"]}**')
            st.write(f'저자: {data["author"] or "정보 없음"}')
            st.write(f'출판사: {data["publisher"] or "정보 없음"}')
        else:
            # 404(등록 안 된 책), 422(잘못된 ISBN 형식) 등 -> 상태코드와 함께 실패 안내
            st.error(f'조회 실패 ({r.status_code}): 등록된 정보가 없거나 잘못된 ISBN입니다.')
# ══════════════════════════════════════════════════════════
# ▲▲▲ 1단계 끝 ▲▲▲
# ══════════════════════════════════════════════════════════

st.divider()

# ══════════════════════════════════════════════════════════
# ▼▼▼ 2단계: 사진 업로드로 전체 파이프라인(OCR -> 검증 -> 조회 -> 등록) 확인 ▼▼▼
# (v3~v6에서 계속 써왔던 부분, 로직 변경 없음)
# ══════════════════════════════════════════════════════════
st.header('2단계: 표지 사진으로 등록하기')

image = st.file_uploader('표지 사진')

if st.button('등록'):
    if image is None:
        st.warning('먼저 표지 사진을 선택해주세요!')
    else:
        r = requests.post(
            f'{API}/books/scan',
            files={'image': (image.name, image.getvalue(), image.type)}
        )
        if r.ok:
            st.success(f'등록됨: {r.json()["title"]}')
        else:
            st.error(f'실패: {r.status_code}')
# ══════════════════════════════════════════════════════════
# ▲▲▲ 2단계 끝 ▲▲▲
# ══════════════════════════════════════════════════════════

st.divider()

st.subheader('등록된 책')
for book in requests.get(f'{API}/books').json():
    st.write(f'{book["title"]} ({book["recognition_status"]})')
