import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="나의 할 일 관리",
    page_icon="✅",
    layout="centered",
)

st.markdown("""
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
    background-color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None


def get_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def logout():
    st.session_state.access_token = None
    st.session_state.user_email = None


def extract_error_message(res: requests.Response, fallback: str) -> str:
    try:
        detail = res.json().get("detail", fallback)
    except requests.exceptions.JSONDecodeError:
        return f"서버 오류 (status {res.status_code}). uvicorn 터미널을 확인해주세요."

    if isinstance(detail, list):
        messages = []
        for err in detail:
            msg = err.get("msg", "") if isinstance(err, dict) else str(err)
            msg = msg.replace("Value error, ", "")
            messages.append(msg)
        return "\n".join(messages) if messages else fallback

    return str(detail)


if not st.session_state.access_token:
    st.title("✅ 나의 할 일 관리")
    st.caption("로그인하거나 새로 가입해주세요.")

    tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("이메일", key="login_email")
            password = st.text_input("비밀번호", type="password", key="login_pw")
            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f"{API_BASE}/users/login",
                    json={"email": email, "password": password},
                )
                if res.status_code == 200:
                    st.session_state.access_token = res.json()["access_token"]
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error(extract_error_message(res, "로그인에 실패했습니다."))
            except requests.exceptions.ConnectionError:
                st.error("서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인해주세요.")

    with tab_signup:
        st.caption("비밀번호는 대문자·소문자·숫자·특수문자를 각 1개 이상 포함해야 합니다.")
        with st.form("signup_form", clear_on_submit=True):
            email = st.text_input("이메일", key="signup_email")
            password = st.text_input("비밀번호", type="password", key="signup_pw")
            submitted = st.form_submit_button("가입하기", use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f"{API_BASE}/users/signup",
                    json={"email": email, "password": password},
                )
                if res.status_code == 201:
                    st.success("가입 완료! 로그인 탭에서 로그인해주세요.")
                else:
                    st.error(extract_error_message(res, "가입에 실패했습니다."))
            except requests.exceptions.ConnectionError:
                st.error("서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인해주세요.")

    st.stop()


col1, col2 = st.columns([4, 1])
with col1:
    st.title("✅ 나의 할 일")
    st.caption(f"{st.session_state.user_email}님, 환영합니다.")
with col2:
    st.write("")
    if st.button("로그아웃", use_container_width=True):
        logout()
        st.rerun()

res = requests.get(f"{API_BASE}/todos", headers=get_headers())

if res.status_code == 401:
    st.warning("로그인이 만료되었습니다. 다시 로그인해주세요.")
    logout()
    st.stop()

todos = res.json()

total = len(todos)
done_count = sum(1 for t in todos if t["is_done"])

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("전체", total)
metric_col2.metric("완료", done_count)
metric_col3.metric("남은 일", total - done_count)

if total > 0:
    st.progress(done_count / total, text=f"{done_count}/{total} 완료")

st.divider()

with st.form("add_todo_form", clear_on_submit=True):
    new_title = st.text_input("새로운 할 일", placeholder="할 일을 입력하세요")
    add_submitted = st.form_submit_button("➕ 추가", use_container_width=True)

if add_submitted and new_title.strip():
    requests.post(
        f"{API_BASE}/todos",
        json={"title": new_title, "is_done": False},
        headers=get_headers(),
    )
    st.rerun()

st.divider()

if total == 0:
    st.info("아직 할 일이 없습니다. 위에서 추가해보세요!")

for todo in todos:
    card_class = "todo-done" if todo["is_done"] else "todo-pending"
    check_col, title_col, delete_col = st.columns([1, 6, 1])

    with check_col:
        new_state = st.checkbox(
            "", value=todo["is_done"], key=f"check_{todo['id']}"
        )
        if new_state != todo["is_done"]:
            requests.patch(
                f"{API_BASE}/todos/{todo['id']}",
                json={"is_done": new_state},
                headers=get_headers(),
            )
            st.rerun()

    with title_col:
        st.markdown(
            f'<div class="todo-card {card_class}">{todo["title"]}</div>',
            unsafe_allow_html=True,
        )

    with delete_col:
        if st.button("🗑️", key=f"delete_{todo['id']}"):
            requests.delete(f"{API_BASE}/todos/{todo['id']}", headers=get_headers())
            st.rerun()
