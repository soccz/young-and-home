
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.ui import setup_page, draw_sidebar, T, card, badge_html, spacer

setup_page("Young & Home")
draw_sidebar()

# ============================
# ONBOARDING WIZARD (첫 방문)
# ============================
if not st.session_state.get("onboarding_complete"):
    st.markdown("""
    <div style="text-align:center; padding:20px 0;">
    <h1 style="font-size:36px; margin-bottom:8px;">🏠 Young & Home</h1>
    <p style="font-size:18px; color:#64748B;">처음 집 구하는 당신을 위한 AI 주거 파트너</p>
    </div>
    """, unsafe_allow_html=True)

    step = st.session_state.get("onboarding_step", 1)

    # Step indicator
    steps_html = ""
    for i in range(1, 5):
        color = "#6366F1" if i <= step else "#CBD5E1"
        steps_html += f'<div style="width:25%; height:4px; background:{color}; border-radius:2px;"></div>'
    st.markdown(f'<div style="display:flex; gap:4px; margin-bottom:24px;">{steps_html}</div>', unsafe_allow_html=True)

    if step == 1:
        card("""<h3 style="margin:0;">👋 반가워요! 먼저 알려주세요</h3>
<p style="color:#64748B;">3분이면 끝나요. 이 정보로 딱 맞는 집과 혜택을 찾아드릴게요.</p>""")

        c1, c2 = st.columns(2)
        with c1:
            ob_status = st.selectbox("지금 어떤 상황이에요?",
                ["대학생 (첫 자취)", "취업준비생", "사회초년생 (첫 직장)", "직장인 (이직/이사)", "신혼부부", "프리랜서/크리에이터"],
                key="ob_status")
        with c2:
            ob_age = st.number_input("만 나이", min_value=19, max_value=45, value=25, key="ob_age")

        if st.button("다음 →", use_container_width=True, type="primary", key="ob_next1"):
            # Map status
            status_map = {
                "대학생 (첫 자취)": "대학생", "취업준비생": "취업준비생",
                "사회초년생 (첫 직장)": "직장인", "직장인 (이직/이사)": "직장인",
                "신혼부부": "직장인", "프리랜서/크리에이터": "창업자"
            }
            st.session_state.user_status = status_map.get(ob_status, "대학생")
            st.session_state.user_age = ob_age
            st.session_state.ob_raw_status = ob_status
            # job_type/married 매핑
            job_map = {"대학생 (첫 자취)": "unemployed", "취업준비생": "unemployed",
                       "사회초년생 (첫 직장)": "sme", "직장인 (이직/이사)": "major",
                       "신혼부부": "sme", "프리랜서/크리에이터": "freelancer"}
            st.session_state.user_job_type = job_map.get(ob_status, "unemployed")
            st.session_state.user_married = "newlywed" if "신혼" in ob_status else "single"
            st.session_state.onboarding_step = 2
            st.rerun()

    elif step == 2:
        card("""<h3 style="margin:0;">📍 어디서 살고 싶어요?</h3>
<p style="color:#64748B;">학교나 직장 근처를 알려주세요.</p>""")

        ob_school = st.text_input("학교 또는 직장 이름/위치", placeholder="예: 서강대, 강남역, 마포구", key="ob_school")
        ob_commute = st.slider("최대 통근/통학 시간 (분)", 10, 60, 30, key="ob_commute")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 이전", use_container_width=True, key="ob_prev2"):
                st.session_state.onboarding_step = 1
                st.rerun()
        with c2:
            if st.button("다음 →", use_container_width=True, type="primary", key="ob_next2"):
                st.session_state.user_location = ob_school or "마포구"
                st.session_state.onboarding_step = 3
                st.rerun()

    elif step == 3:
        card("""<h3 style="margin:0;">💰 예산은 어느 정도예요?</h3>
<p style="color:#64748B;">대략적으로 괜찮아요. 나중에 바꿀 수 있어요.</p>""")

        c1, c2 = st.columns(2)
        with c1:
            ob_assets = st.number_input("보증금으로 쓸 수 있는 돈 (만원)", min_value=0, value=2000, step=100, key="ob_assets",
                                        help="부모님 지원 포함")
            ob_income = st.number_input("월 소득 (만원)", min_value=0, value=0, step=10, key="ob_income",
                                        help="알바비, 용돈, 월급 등 전부")
        with c2:
            ob_monthly = st.number_input("월세 한도 (만원)", min_value=0, value=50, step=5, key="ob_monthly")
            ob_yearly = st.number_input("연소득 (만원, 있으면)", min_value=0, value=0, step=100, key="ob_yearly",
                                        help="세전 연봉. 없으면 0")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 이전", use_container_width=True, key="ob_prev3"):
                st.session_state.onboarding_step = 2
                st.rerun()
        with c2:
            if st.button("다음 →", use_container_width=True, type="primary", key="ob_next3"):
                st.session_state.user_assets = ob_assets
                st.session_state.user_income = ob_yearly if ob_yearly > 0 else ob_income * 12
                st.session_state.user_max_monthly = ob_monthly
                st.session_state.user_max_deposit = ob_assets
                st.session_state.onboarding_step = 4
                st.rerun()

    elif step == 4:
        card("""<h3 style="margin:0;">😟 가장 걱정되는 건 뭐예요?</h3>
<p style="color:#64748B;">우선순위를 알면 더 잘 도와드릴 수 있어요.</p>""")

        ob_worry = st.radio("가장 걱정되는 것", [
            "🛡️ 전세사기/깡통전세 (안전이 최우선)",
            "💰 돈이 부족해요 (최대한 저렴하게)",
            "📍 어디가 좋은지 모르겠어요 (지역 추천)",
            "📋 뭘 해야 하는지 모르겠어요 (절차 가이드)"
        ], key="ob_worry", label_visibility="collapsed")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 이전", use_container_width=True, key="ob_prev4"):
                st.session_state.onboarding_step = 3
                st.rerun()
        with c2:
            if st.button("🏠 시작하기!", use_container_width=True, type="primary", key="ob_done"):
                st.session_state.user_worry = ob_worry
                st.session_state.onboarding_complete = True
                st.session_state.onboarding_step = 0
                st.rerun()

    st.stop()  # 온보딩 완료 전에는 대시보드 표시 안 함

# ============================
# HOME DASHBOARD (온보딩 완료 후)
# ============================
from src.utils.ui import load_housing_data
_all_houses = load_housing_data()

# 프로필 기반 매칭 매물 수 계산
_user_monthly = st.session_state.get("user_max_monthly", 50)
_user_deposit = st.session_state.get("user_max_deposit", 2000)
_matched = [h for h in _all_houses if h.get("monthly", 999) <= _user_monthly * 1.3 and h.get("deposit", 999) <= _user_deposit * 1.5 and h.get("risk_level") != "고위험"]
listings_count = len(_matched) if _matched else len(_all_houses)
alerts_count = len([h for h in _matched if h.get("risk_level") == "주의"])

# D-Day 카운터
import datetime
if "move_target_date" not in st.session_state:
    st.session_state.move_target_date = None

# Welcome Card
# D-Day 표시
if st.session_state.move_target_date:
    d_day = (st.session_state.move_target_date - datetime.date.today()).days
    if d_day >= 0:
        dday_color = "#22C55E" if d_day > 30 else "#F59E0B" if d_day > 7 else "#EF4444"
        dday_content = f"""<div style="display:flex; align-items:center; gap:16px;">
<div style="font-size:32px; font-weight:900; color:{dday_color};">D-{d_day}</div>
<div>
<div style="font-size:14px; font-weight:600; color:#1E293B;">이사 목표일까지</div>
<div style="font-size:12px; color:#64748B;">{st.session_state.move_target_date.strftime('%Y년 %m월 %d일')}</div>
</div>
</div>"""
        card(dday_content, style=f"border-left: 4px solid {dday_color}; padding:16px 20px;")
else:
    with st.expander("📅 이사 목표일 설정 (D-Day)", expanded=False):
        target = st.date_input("이사 목표일", value=datetime.date.today() + datetime.timedelta(days=30), key="dday_input")
        if st.button("설정", key="dday_set"):
            st.session_state.move_target_date = target
            st.rerun()

_welcome = T('home_welcome').replace('서강', st.session_state.user_name) if st.session_state.language == "KO" else T('home_welcome').replace('Seogang', st.session_state.user_name)
_badge_new = f"새 매물 {listings_count}건" if st.session_state.language == "KO" else f"{listings_count} New Listings"
welcome_content = f"""
<h2 class="no-margin-top">{_welcome}</h2>
<p>{T('home_desc')}</p>
<div class="flex-gap-12 mt-20">
    {badge_html(_badge_new, accent=True)}
    {badge_html(T('badge_system'))}
</div>
"""
card(welcome_content)

# ============================
# 맞춤 로드맵 (온보딩 결과 기반)
# ============================
worry = st.session_state.get("user_worry", "")
raw_status = st.session_state.get("ob_raw_status", "대학생 (첫 자취)")

st.markdown("### 🗺️ 나만의 이사 로드맵")

# 상태별 로드맵 생성
roadmap_steps = []

if "사기" in worry or "안전" in worry:
    roadmap_steps = [
        {"step": "1단계", "title": "안전 지식 익히기", "desc": "깡통전세 판별법, 등기부 읽는 법 배우기", "page": "pages/7_✅_체크리스트.py", "icon": "📚", "action": "체크리스트 보기"},
        {"step": "2단계", "title": "정부 혜택 확인", "desc": "내가 받을 수 있는 지원금·대출 확인", "page": "pages/1_🔍_스마트_검색.py", "icon": "💰", "action": "혜택 검색"},
        {"step": "3단계", "title": "매물 찾기 + 안전 진단", "desc": "관심 매물의 등기부등본 분석", "page": "pages/2_🛡️_안전_진단.py", "icon": "🛡️", "action": "안전 진단"},
        {"step": "4단계", "title": "계약 전 체크", "desc": "계약서 특약, 보증보험 가입", "page": "pages/3_📝_협상_도우미.py", "icon": "✍️", "action": "협상 도우미"},
        {"step": "5단계", "title": "입주 당일 처리", "desc": "전입신고 → 확정일자 → 보증보험", "page": "pages/7_✅_체크리스트.py", "icon": "🏠", "action": "입주 체크리스트"},
    ]
elif "돈" in worry or "저렴" in worry:
    roadmap_steps = [
        {"step": "1단계", "title": "정부 지원금 먼저 확인", "desc": "청년월세지원, 주거급여 등 자격 체크", "page": "pages/1_🔍_스마트_검색.py", "icon": "💰", "action": "지원금 검색"},
        {"step": "2단계", "title": "대출 한도 확인", "desc": "중기청/버팀목 대출 자격 + 한도 계산", "page": "pages/5_💰_금융_계산기.py", "icon": "🏦", "action": "대출 진단"},
        {"step": "3단계", "title": "예산 맞춤 지역 탐색", "desc": "내 예산으로 갈 수 있는 동네 찾기", "page": "pages/1_🔍_스마트_검색.py", "icon": "📍", "action": "매물 검색"},
        {"step": "4단계", "title": "집 보러 가기", "desc": "현장 체크리스트로 꼼꼼하게", "page": "pages/7_✅_체크리스트.py", "icon": "🔍", "action": "체크리스트"},
        {"step": "5단계", "title": "계약 + 입주", "desc": "안전하게 계약하고 이사하기", "page": "pages/7_✅_체크리스트.py", "icon": "🏠", "action": "계약 체크리스트"},
    ]
elif "어디" in worry or "지역" in worry:
    roadmap_steps = [
        {"step": "1단계", "title": "내 조건 정리", "desc": "통학/통근 시간, 예산, 선호 환경 정리", "page": "pages/2_👤_내_프로필.py", "icon": "👤", "action": "프로필 설정"},
        {"step": "2단계", "title": "지역 탐색", "desc": "AI가 추천하는 동네 + 시세 확인", "page": "pages/1_🔍_스마트_검색.py", "icon": "📍", "action": "지역 검색"},
        {"step": "3단계", "title": "혜택 매칭", "desc": "해당 지역의 공공임대·지원금 확인", "page": "pages/1_🔍_스마트_검색.py", "icon": "💰", "action": "혜택 검색"},
        {"step": "4단계", "title": "매물 비교 + 방문", "desc": "후보 3~5개 추리고 직접 가보기", "page": "pages/7_✅_체크리스트.py", "icon": "🔍", "action": "방문 체크리스트"},
        {"step": "5단계", "title": "안전 확인 + 계약", "desc": "등기부 분석 후 계약 진행", "page": "pages/2_🛡️_안전_진단.py", "icon": "🛡️", "action": "안전 진단"},
    ]
else:  # 절차 모름 / 기본
    roadmap_steps = [
        {"step": "1단계", "title": "내 상황 파악", "desc": "프로필 설정 + 받을 수 있는 혜택 확인", "page": "pages/2_👤_내_프로필.py", "icon": "👤", "action": "프로필 설정"},
        {"step": "2단계", "title": "예산 계획", "desc": "대출 한도, 전세 vs 월세 비교", "page": "pages/5_💰_금융_계산기.py", "icon": "💰", "action": "금융 계산기"},
        {"step": "3단계", "title": "매물 검색", "desc": "AI가 찾아주는 맞춤 매물 + 지역 가이드", "page": "pages/1_🔍_스마트_검색.py", "icon": "🔍", "action": "매물 검색"},
        {"step": "4단계", "title": "안전 확인", "desc": "등기부 위험 분석 + 계약서 교차 검증", "page": "pages/2_🛡️_안전_진단.py", "icon": "🛡️", "action": "안전 진단"},
        {"step": "5단계", "title": "계약 + 입주", "desc": "체크리스트 따라 안전하게 마무리", "page": "pages/7_✅_체크리스트.py", "icon": "🏠", "action": "체크리스트"},
    ]

# Render roadmap
for i, rs in enumerate(roadmap_steps):
    is_current = (i == 0)  # 첫 번째 단계가 현재
    border = "border-left: 4px solid #6366F1;" if is_current else "border-left: 4px solid #E2E8F0;"
    bg = "background: rgba(99, 102, 241, 0.03) !important;" if is_current else ""

    step_content = f"""<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
<span style="font-size:20px;">{rs['icon']}</span>
<span style="font-size:12px; color:#6366F1; font-weight:700;">{rs['step']}</span>
<span style="font-size:15px; font-weight:700; color:#1E293B;">{rs['title']}</span>
</div>
<div style="font-size:13px; color:#64748B;">{rs['desc']}</div>
</div>
</div>"""
    card(step_content, style=f"{border} {bg} padding:16px 20px;")

    if is_current:
        if st.button(f"▶ {rs['action']}", use_container_width=True, type="primary", key=f"roadmap_{i}"):
            st.switch_page(rs['page'])

spacer("10px")

# Quick Actions
st.markdown(f"### {T('quick_actions')}")
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    if st.button(T('btn_start_search'), use_container_width=True):
        st.switch_page("pages/1_🔍_스마트_검색.py")
with b_col2:
    if st.button(T('btn_analyze'), use_container_width=True):
        st.switch_page("pages/2_🛡️_안전_진단.py")
with b_col3:
    if st.button(T('btn_calc'), use_container_width=True):
        st.switch_page("pages/5_💰_금융_계산기.py")

# Subscription Section
st.markdown("### 🔔 매물 알림")
if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = []

with st.expander("📬 알림 설정 열기", expanded=False):
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        sub_location = st.text_input("희망 지역", value=st.session_state.get("user_location", "마포구"), key="home_sub_loc")
        sub_deposit = st.number_input("최대 보증금 (만원)", value=st.session_state.get("user_max_deposit", 3000), key="home_sub_dep")
    with sub_col2:
        sub_monthly = st.number_input("최대 월세 (만원)", value=st.session_state.get("user_max_monthly", 50), key="home_sub_mon")
        sub_notify = st.selectbox("알림 방식", ["kakao", "email", "slack"], key="home_sub_notify")

    if st.button("✅ 알림 구독하기", use_container_width=True, key="home_btn_sub"):
        st.session_state.subscriptions.append({
            "user_id": st.session_state.get("user_name", "test_user"),
            "location": sub_location, "max_deposit": int(sub_deposit),
            "max_monthly": int(sub_monthly), "notify_method": sub_notify
        })
        st.success(f"✨ 구독 완료! '{sub_location}' 매물을 '{sub_notify}'로 보내드릴게요.")

# 온보딩 리셋 (숨김)
with st.expander("⚙️ 설정", expanded=False):
    if st.button("온보딩 다시 하기"):
        st.session_state.onboarding_complete = False
        st.session_state.onboarding_step = 1
        st.rerun()
