
import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.utils.ui import setup_page, draw_sidebar, T, card, spacer

setup_page("My Profile")
draw_sidebar()

st.markdown(f"## 👤 {T('menu_profile')}")
st.caption("AI 에이전트가 이 정보를 바탕으로 최적의 대출과 지원금을 찾아냅니다." if st.session_state.language == "KO" else "AI agents use this info to find the best loans and subsidies for you.")

spacer("10px")

# Initialize profile fields in session_state
defaults = {
    "user_income": 0,
    "user_age": 25,
    "user_job_type": "unemployed",
    "user_married": "single",
    "user_location": "마포구",
    "user_max_deposit": 2000,
    "user_max_monthly": 50,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

with st.form("profile_form"):
    st.markdown("### 💰 재무 상태")
    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input("연소득 (만원)", min_value=0, value=st.session_state.user_income, step=100, help="세전 기준 연봉")
    with col2:
        assets = st.number_input("보유 자산 (만원)", min_value=0, value=st.session_state.user_assets, step=100, help="전세 보증금에 쓸 수 있는 현금")

    st.markdown("### 🏢 직장 및 신분")
    job_options = ["sme", "major", "public", "unemployed", "freelancer"]
    job_labels = {
        "sme": "중소기업 (청년 전용 대출 가능)",
        "major": "대기업/중견기업",
        "public": "공무원/공공기관",
        "unemployed": "무직/취업준비생",
        "freelancer": "프리랜서"
    }
    job_type = st.selectbox(
        "직장 유형",
        options=job_options,
        index=job_options.index(st.session_state.user_job_type),
        format_func=lambda x: job_labels.get(x, x)
    )

    col3, col4 = st.columns(2)
    with col3:
        age = st.number_input("만 나이", min_value=19, max_value=45, value=st.session_state.user_age)
    with col4:
        married_options = ["single", "married", "newlywed"]
        married_labels = {"single": "미혼", "married": "기혼", "newlywed": "신혼부부 (7년 이내)"}
        married = st.selectbox(
            "결혼 여부",
            options=married_options,
            index=married_options.index(st.session_state.user_married),
            format_func=lambda x: married_labels.get(x, x)
        )

    st.markdown("### 📍 희망 거주 조건")
    location = st.text_input("희망 지역", value=st.session_state.user_location)

    col5, col6 = st.columns(2)
    with col5:
        max_deposit = st.number_input("최대 보증금 (만원)", value=st.session_state.user_max_deposit, step=1000)
    with col6:
        max_monthly = st.number_input("최대 월세 (만원)", value=st.session_state.user_max_monthly, step=5)

    submitted = st.form_submit_button("💾 프로필 저장하기", use_container_width=True)

    if submitted:
        st.session_state.user_income = income
        st.session_state.user_assets = assets
        st.session_state.user_job_type = job_type
        st.session_state.user_age = age
        st.session_state.user_married = married
        st.session_state.user_location = location
        st.session_state.user_max_deposit = max_deposit
        st.session_state.user_max_monthly = max_monthly
        st.success("✅ 프로필이 저장되었습니다! AI가 이 정보를 기반으로 맞춤 분석합니다.")

# Show current profile summary
spacer("20px")
st.markdown("### 📋 현재 프로필 요약")

status_map = {"sme": "중소기업", "major": "대기업", "public": "공무원", "unemployed": "무직/취준", "freelancer": "프리랜서"}
married_map = {"single": "미혼", "married": "기혼", "newlywed": "신혼부부"}

summary_content = f"""
<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
<div><span style="color:#64748B; font-size:13px;">이름</span><br><b>{st.session_state.user_name}</b></div>
<div><span style="color:#64748B; font-size:13px;">나이</span><br><b>{st.session_state.user_age}세</b></div>
<div><span style="color:#64748B; font-size:13px;">연소득</span><br><b>{st.session_state.user_income:,}만원</b></div>
<div><span style="color:#64748B; font-size:13px;">보유자산</span><br><b>{st.session_state.user_assets:,}만원</b></div>
<div><span style="color:#64748B; font-size:13px;">직장</span><br><b>{status_map.get(st.session_state.user_job_type, st.session_state.user_job_type)}</b></div>
<div><span style="color:#64748B; font-size:13px;">결혼</span><br><b>{married_map.get(st.session_state.user_married, st.session_state.user_married)}</b></div>
<div><span style="color:#64748B; font-size:13px;">희망지역</span><br><b>{st.session_state.user_location}</b></div>
<div><span style="color:#64748B; font-size:13px;">예산</span><br><b>보증금 {st.session_state.user_max_deposit:,} / 월세 {st.session_state.user_max_monthly}만</b></div>
</div>
"""
card(summary_content)
