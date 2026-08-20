'''
========================================================================================
streamlit_app.py

FastAPI Todo API를 호출해서 화면으로 보여주는 프론트엔드
FastAPI는 계속 uvicorn으로 실행 중
Streamlit도 따로 streamlit run으로 실행을 해야 한다. 
========================================================================================
'''
import streamlit as st
import requests

# -----------------------------------------------------------------------------------------
# 기본 설정
# -----------------------------------------------------------------------------------------
API_BASE = 'http://127.0.0.1:8000'  # uvicorn으로 띄우는 FastAPI 주소

st.set_page_config(
    page_title='나의 할 일 관리',
    page_icon='📌',
    layout='centered',
)

st.markdown('''
<style>
.todo-card {
    padding: 14px 18px;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #e6e6e6;
}
.todo-done {
    background-color: #f0f7f0;
    text-decoration: line-through;
    color: #888;
}
.todo-pending {
    background-color: #fff;
}
</style>
''', unsafe_allow_html=True) # unsafe_allow_html=True --> html/css가 먼저 적용이 되도록

# -----------------------------------------------------------------------------------------
# 세션 상태(session_state) 초기화
#   
#   스트림릿은 버튼을 누를 때 마다 전체 스크립트가 위에서 아래로 다시 실행된다.
#   로그인을 했다라는 사실을 변수에 담아둔다.
#   st.session_state는 재실행되어도 값이 유지되는 유일한 저장공간이다.
#   여기에 토큰/로그인 여부를 저장한다.
# -----------------------------------------------------------------------------------------
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def get_headers() -> dict:
    """로그인 후 API요청에 매번 붙여야 하는 인증 헤더를 만들어 반환"""
    return {'Authorization': f'Bearer {st.session_state.access_token}'}

def logout():
    """세션 상태를 비워서 로그아웃 처리(서버에 요청 보낼 필요 없다 -> JWT는 Stateless방식)"""
    st.session_state.access_token = None
    st.session_state.user_email = None

def extract_error_message(res: requests.Response, fallback: str) -> str:
    """
    FastAPI 에러 응답에서 사람이 읽을 수 있는 메세지만 뽑아 낸다.

    - 일반적인 HTTPException: {"detail": [{"type": ..., "msg": "Value error, ..."}]} 형태(그대로 사용)
    - 깔끔하게 출력하기 위해서 리스트를 순회하며 msg만 뽑고, "Value error, " 접두어는 잘라낸다. 
    - 응답이 JSON이 아니거나(500 에러 페이지 등) 파싱 자체가 실패하는 경우도 대비
    """
    try:
        detail = res.json().get('detail', fallback)
    except requests.exceptions.JSONDecodeError:
        return f'서버 오류 (status {res.status_code}). uvicorn 터미널을 확인해주세요.'

    if isinstance(detail, list):
        messages = []
        for err in detail:
            # err이 dict라면(딕셔너리라면) msg키의 값을 msg변수에 넣어라, 아니면 err을 문자열로 형변환해서
            # msg변수에 넣어라.
            msg = err.get('msg', '') if isinstance(err, dict) else str(err)
            # 'Value error, '를 없애겠다. (단어를 치환한다. 바꾼다->replace())
            msg = msg.replace('Value error, ', '')
            messages.append(msg)

        # messages가 있다면 메시지 사이사이에 엔터를 삽입, 아니면 그냥 fallback변수에 있는 값이 반환
        return '\n'.join(messages) if messages else fallback

    return str(detail)

# -----------------------------------------------------------------------------------------
# 로그인 안 된 상태 - 로그인 / 회원가입 화면
# -----------------------------------------------------------------------------------------
if not st.session_state.access_token:
    st.title('나의 할 일 관리')
    st.caption('로그인하거나 새로 가입해주세요.')

    tab_login, tab_signup = st.tabs(['로그인', '회원가입'])

    # ------로그인 탭-----------------------------------------------------------------------------------
    with tab_login:
        with st.form('login_form'):
            email = st.text_input('이메일', key='login_email')
            password = st.text_input('비밀번호', type='password', key='login_pw')
            submitted = st.form_submit_button('로그인', use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f'{API_BASE}/users/login',
                    json={'email': email, 'password': password},
                )
                if res.status_code == 200: # 로그인 성공!
                    st.session_state.access_token = res.json()['access_token']
                    st.session_state.user_email = email
                    st.rerun()  # 화면을 즉시 새로고침해서 아래의 Todo화면으로 전환
                else:
                    st.error(extract_error_message(res, '로그인에 실패했습니다.'))
            except requests.exceptions.ConnectionError:
                st.error('서버에 연결할 수 없습니다. uvicorn이 실행중인지 확인해주세요!')

    # ------회원가입 탭-----------------------------------------------------------------------------------
    with tab_signup:
        st.caption('비밀번호는 대문자, 소문자, 숫자, 특수문자를 각 1개 이상 포함해야 합니다.')    

        # clear_on_submit=True : 제출 버튼을 누르면 입력창을 자동으로 비워준다. (성공, 실패 모두 해당)
        with st.form('signup_form', clear_on_submit=True):
            email = st.text_input('이메일', key='signup_email')
            password = st.text_input('비밀번호', type='password', key='signup_pw')
            submitted = st.form_submit_button('가입하기', use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f'{API_BASE}/users/signup',
                    json={'email': email, 'password': password},
                )
                if res.status_code == 201: # 회원가입 성공!
                    st.success('가입 완료! 로그인 탭에서 로그인해주세요.')
                else:
                    st.error(extract_error_message(res, '가입에 실패했습니다.'))
            except requests.exceptions.ConnectionError:
                st.error('서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인해주세요.')

    st.stop() # 로그인 전이면 아래 코드(Todo화면)는 아예 실행하지 않고 여기서 멈춘다. 

# -----------------------------------------------------------------------------------------
# 로그인 된 상태 - Todo 화면
# -----------------------------------------------------------------------------------------

# ----상단 헤더----------------------------------------------------------------------------
col1, col2 = st.columns([4, 1])
with col1:
    st.title('나의 할 일')
    st.caption(f'{st.session_state.user_email}님, 환영합니다.')
with col2:
    st.write('')  # 버튼 위치를 살짝 아래로 맞추기 위한 여백
    if st.button('로그아웃', use_container_width=True):
        logout()
        st.rerun()

# ----할 일 목록 가져오기----------------------------------------------------------------------------        
res = requests.get(f'{API_BASE}/todos', headers=get_headers())

if res.status_code == 401:
    # 토큰이 만료되었나, 유효하지 않으면 자동으로 로그아웃 처리
    st.warning('로그인 만료되었습니다. 다시 로그인해주세요.')
    logout()
    st.stop()

todos = res.json()

# ----할 일 목록 진행상황---------------------------------------------------------------------------- 
total = len(todos)  # 전체 할 일
done_count = sum(1 for t in todos if t['is_done'])  # 완료된 일

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric('전체', total)
metric_col2.metric('완료', done_count)
metric_col3.metric('남은 일', total - done_count)

if total > 0:
    # st.progress 위젯 : 진행률 표시 막대(progress bar)를 화면에 그려주는 위젯
    st.progress(done_count / total, text=f'{done_count}/{total} 완료')

st.divider()

# ----새 할 일 추가---------------------------------------------------------------------------- 
with st.form('add_todo_form', clear_on_submit=True):
    new_title = st.text_input('새로운 할 일', placeholder='할 일을 입력하세요.')
    add_submitted = st.form_submit_button('추가', use_container_width=True)

# .strip() : 문자열 앞뒤로 공백을 제거
if add_submitted and new_title.strip():
    requests.post(
        f'{API_BASE}/todos',
        json={'title': new_title, 'is_done': False},
        headers=get_headers(),
    )
    st.rerun()  # 추가 후 목록을 다시 불러오기 위해 새로고침

st.divider()

# ----할 일 목록 표시(카드 형태)--------------------------------------------------------------------------
if total == 0:
    st.info('아직 할 일이 없습니다. 위에서 추가해보세요!')

# ======== Streamlit 쪽에서 보여질 카테고리 선택지 목록 ================
CATEGORY_OPTIONS = ['업무', '개인', '긴급']
# ====================================================================

for todo in todos:
    card_class = 'todo-done' if todo['is_done'] else 'todo-pending'

    check_col, title_col, delete_col = st.columns([1, 6, 1])

    with check_col:
        # 체크박스 값이 바뀌는 순간(=클릭하는 순간) PATCH 요청을 보낸다.
        new_state = st.checkbox(
            '', value=todo['is_done'], key=f'check_{todo["id"]}'
        )
        if new_state != todo['is_done']:
            requests.patch(  # 수정 요청
                f'{API_BASE}/todos/{todo["id"]}',
                json={'is_done': new_state},
                headers=get_headers(),
            )
            st.rerun()

    with title_col:
        st.markdown(
            f'<div class="todo-card {card_class}">{todo["title"]}</div>',
            unsafe_allow_html=True,
        )

    with delete_col:
        if st.button('X', key=f'delete_{todo["id"]}'):
            requests.delete(f'{API_BASE}/todos/{todo["id"]}', headers=get_headers())
            st.rerun()

    # ========== 카레고리 자동분류 표시/확정 영역 (MLOps 확장 부분) ===================================
    predicted = todo.get('predicted_category')
    final = todo.get('final_category')

    # predicted가 None인 경우(=서버에 모델이 로드 안 되어 있던 시점에 생성된 Todo)는
    # 이 영역 자체를 표시하지 않는다.
    if predicted:
        cat_col1, cat_col2 = st.columns([2, 4])
        with cat_col1:
            if final:
                # 사용자가 이미 확인/수정을 완료한 경우
                st.caption(f'확정된 카테고리: **{final}**')
            else:
                # 아직 아무도 확인하지 않은, 모델의 예측 그대로의 상태
                st.caption(f'모델 예측: **{predicted}** (확인 필요)')
        with cat_col2:
            # 확정값이 있으면 있는 값을 사용하고, 없으면 예측값으로 selectbox의 초기 선택값으로 사용
            current_value = final if final else predicted
            selected = st.selectbox(
                '카테고리 확인/수정',
                CATEGORY_OPTIONS,
                index=CATEGORY_OPTIONS.index(current_value) if current_value in CATEGORY_OPTIONS else 0,
                key=f'category_{todo["id"]}',
                label_visibility='collapsed', # 라벨을 화면에 안보이게(위 caption이 라벨 역할을 대신한다.)
            )
            # 사용자가 selectbox에서 값을 바꾼 경우만 서버에 확정 요청을 한다.
            # --> Todo.final_category를 채우는 지점 --> 나중에 ml/retrain.py의 새 학습 데이터가 된다.
            if selected != current_value:
                requests.patch(
                    f'{API_BASE}/todos/{todo["id"]}/category',
                    json={"category": selected},
                    headers=get_headers(),
                )
                st.rerun()

    st.divider()

    