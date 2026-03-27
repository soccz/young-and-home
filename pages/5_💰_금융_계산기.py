
import streamlit as st
import os
from src.utils.ui import setup_page, draw_sidebar, T, card, spacer, divider

setup_page("Finance")
draw_sidebar()

st.markdown(f"## 💰 {T('btn_calc')}")
st.markdown("금융 지식이 없어도 괜찮아요. AI가 내 상황에 맞는 전세대출과 자금 계획을 세워드립니다.")

spacer("20px")

# 4개의 탭
tab_rec, tab_vs, tab_dsr, tab_living, tab_dict = st.tabs(["🤖 AI 대출 추천", "📊 전월세 비교", "🏦 대출 한도 진단", "🏠 생활비 시뮬레이션", "📖 금융 용어 사전"])

from src.agents.finance_agent import FinancialSimulator
fin_agent = FinancialSimulator()

# [Tab 1] AI 대출 상품 추천
with tab_rec:
    st.markdown("### 🤖 내 상황에 딱 맞는 청년 대출 찾기")
    st.caption("복잡한 대출 상품, 내 조건만 선택하면 AI가 가장 유리한 상품을 찾아줍니다.")
    
    c1, c2 = st.columns(2)
    with c1:
        q_age = st.number_input("만 나이", value=29, step=1)
        q_income = st.number_input("연소득 (만원)", value=3200, step=100, help="세전 기준")
    
    with c2:
        q_job = st.selectbox("직업 상태", ["재직자", "취업준비생/무직", "프리랜서"])
        q_sme = st.checkbox("중소/중견기업 재직 중인가요?", value=(q_job=="재직자"))
        
    if st.button("내게 맞는 대출 찾기", type="primary", use_container_width=True):
        st.markdown("---")
        recs = fin_agent.recommend_loan_product(q_age, q_income, q_job, q_sme)
        
        st.markdown(f"### 🎉 추천 결과: {len(recs)}건")
        
        for rec in recs:
            risk_content = f"""<div class="risk-card">
<span style="background:#EEF2FF; color:#4F46E5; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{rec['tag']}</span>
<h3 style="margin:8px 0; color:#1E293B;">{rec['name']}</h3>
<div style="display:flex; gap:20px; color:#475569; font-size:14px;">
<span>💰 금리: <b>{rec['rate']}</b></span>
<span>📏 한도: <b>{rec['limit']}</b></span>
</div>
<p style="margin-top:8px; margin-bottom:0; color:#64748B; font-size:13px;">{rec['desc']}</p>
</div>"""
            st.markdown(risk_content, unsafe_allow_html=True)
            if rec.get("apply_url"):
                st.link_button(f"🚀 {rec['name']} 신청하기", rec["apply_url"], use_container_width=True)

        # === 대출 신청 Step-by-Step ===
        spacer("10px")
        st.markdown("### 📋 다음 단계: 신청 방법")

        # 대출 상품별 신청 가이드
        loan_guides = {
            "중소기업": {
                "steps": [
                    "1️⃣ **중소기업 확인서 발급** — 회사 인사팀에 요청 또는 [중소벤처기업부](https://sminfo.mss.go.kr) 조회",
                    "2️⃣ **기금e든든 온라인 예약** — [nhuf.molit.go.kr](https://nhuf.molit.go.kr) 접속 → 대출 예약",
                    "3️⃣ **취급 은행 방문** — 우리/신한/하나/기업은행 (예약번호 지참)",
                    "4️⃣ **서류 제출 + 심사** — 보통 3~5영업일 소요",
                    "5️⃣ **임대차계약서 제출 → 대출 실행**"
                ],
                "docs": ["재직증명서", "중소기업 확인서", "소득금액증명원 (홈택스)", "주민등록등본", "임대차계약서", "신분증"],
                "script": f"안녕하세요, **중소기업 취업청년 전월세보증금대출** 상담하러 왔습니다. 기금e든든에서 예약했고요, 현재 중소기업에 재직 중이며 연소득은 **{q_income}만원**입니다."
            },
            "버팀목": {
                "steps": [
                    "1️⃣ **기금e든든 온라인 예약** — [nhuf.molit.go.kr](https://nhuf.molit.go.kr)",
                    "2️⃣ **주거래 은행 방문** (국민/신한/우리/하나/농협)",
                    "3️⃣ **서류 제출 + 심사** — 3~7영업일",
                    "4️⃣ **임대차계약서 제출 → 대출 실행**"
                ],
                "docs": ["소득금액증명원", "주민등록등본", "임대차계약서", "무주택 확인서류", "신분증"],
                "script": f"안녕하세요, **청년전용 버팀목 전세자금대출** 상담입니다. 만 **{q_age}세**, 연소득 **{q_income}만원**이고 무주택자입니다."
            }
        }

        # 첫 번째 추천 상품 기준 가이드 표시
        top_rec_name = recs[0]["name"] if recs else ""
        guide_key = "중소기업" if "중소기업" in top_rec_name else "버팀목"
        guide = loan_guides.get(guide_key, loan_guides["버팀목"])

        for s in guide["steps"]:
            st.markdown(s)

        spacer("10px")
        with st.expander("📎 필요 서류 체크리스트"):
            for doc in guide["docs"]:
                st.checkbox(doc, key=f"doc_{doc}")

        with st.expander("🗣️ 은행에서 이렇게 말하세요"):
            st.info(guide["script"])
            st.caption("💡 이 스크립트를 복사해서 메모해 가세요!")

with tab_vs:
    st.markdown("### 📊 전세 vs 월세, 무엇이 더 이득일까요?")
    st.markdown("<p style='color:#64748B; margin-bottom:20px;'>보증금과 금리를 입력하면, 2년 동안 나가는 총 비용을 비교해드립니다.</p>", unsafe_allow_html=True)
    
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        st.markdown("""<div class="box-blue"><h4 style="margin:0; color:#1E3A8A;">🏠 전세 시나리오</h4></div>""", unsafe_allow_html=True)
        jeonse_amt = st.number_input("전세 보증금 (만원)", value=20000, step=1000)
        loan_rate = st.number_input("전세 대출 금리 (%)", value=4.0, step=0.1, format="%.1f")
        
    with c_in2:
        st.markdown("""<div class="box-orange"><h4 style="margin:0; color:#7C2D12;">🏘️ 월세 시나리오</h4></div>""", unsafe_allow_html=True)
        rent_deposit = st.number_input("월세 보증금 (만원)", value=1000, step=500)
        monthly_rent = st.number_input("월세 (만원)", value=60, step=5)
        
    manage_fee = st.number_input("관리비 (만원/월)", value=10, step=1)
    
    if st.button("💸 비용 비교 분석 (Calculate)", use_container_width=True, type="primary"):
        result = fin_agent.compare_rent_vs_jeonse(
            jeonse_deposit=jeonse_amt,
            monthly_rent_deposit=rent_deposit,
            monthly_rent=monthly_rent,
            management_fee=manage_fee,
            loan_rate_percent=loan_rate
        )
        
        st.markdown("---")
        
        is_jeonse_win = result['is_jeonse_cheaper']
        win_color = "#EFF6FF" if is_jeonse_win else "#FFF7ED"
        win_border = "#BFDBFE" if is_jeonse_win else "#FFEDD5"
        win_text = "#1E3A8A" if is_jeonse_win else "#7C2D12"
        winner_icon = "🏠 전세가 유리해요!" if is_jeonse_win else "🏘️ 월세가 유리해요!"
        save_amt = result['difference']
        
        win_content = f"""<h2 style="color:{win_text}; margin:0;">🎉 {winner_icon}</h2>
<p style="font-size:18px; color:#475569; margin-top:10px;">
한 달에 약 <b>{save_amt:.1f}만원</b>을 아낄 수 있습니다.
</p>"""
        card(win_content, style=f"background:{win_color} !important; border:2px solid {win_border}; text-align:center;")
        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"**전세 선택 시** (월 지출)")
            st.markdown(f"<span style='font-size:24px; font-weight:bold; color:#3B82F6'>{result['jeonse']['monthly_cost']:.1f}만원</span>", unsafe_allow_html=True)
            st.caption(f"이자 {result['jeonse']['breakdown']['interest']:.1f} + 관리비 {result['jeonse']['breakdown']['management']:.1f}")
        with m2:
            st.markdown(f"**월세 선택 시** (월 지출)")
            st.markdown(f"<span style='font-size:24px; font-weight:bold; color:#EA580C'>{result['rent']['monthly_cost']:.1f}만원</span>", unsafe_allow_html=True)
            st.caption(f"월세 {result['rent']['breakdown']['rent']} + 관리비 {result['rent']['breakdown']['management']}")

        # Chart
        import pandas as pd
        chart_data = pd.DataFrame({
            "비용 (만원)": [result['jeonse']['monthly_cost'], result['rent']['monthly_cost']],
            "유형": ["전세", "월세"]
        })
        st.bar_chart(chart_data.set_index("유형"), color=["#3B82F6"])
        
# [Tab 3] DSR 진단
with tab_dsr:
    st.markdown("### 🔍 내 소득으로 대출이 얼마나 나올까요? (DSR 간편 진단)")
    
    inc = st.number_input("연소득 (만원)", value=3500, step=100)
    exist_loan = st.number_input("현재 보유 대출금 (만원)", value=0, step=100)
    target_dep = st.number_input("목표 집 보증금 (만원)", value=20000, step=1000)
    
    if st.button("대출 한도 조회", use_container_width=True):
        res = fin_agent.check_loan_eligibility(inc, exist_loan, target_dep)
        
        st.markdown("---")
        
        color_map = {"안전": "green", "주의": "orange", "불가능": "red"}
        color = color_map.get(res['status'], "blue")
        
        st.markdown(f"### 진단 결과: :{color}[{res['status']}]")
        st.info(res['reason'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("예상 대출 가능 한도", f"{res['max_loan']:.0f}만원")
        with col2:
            st.metric("필요 대출금 (보증금 80%)", f"{target_dep*0.8:.0f}만원")

# [Tab 4] 생활비 시뮬레이션
with tab_living:
    st.markdown("### 🏠 이 집에 살면 생활이 가능할까?")
    st.caption("월세 + 관리비 + 생활비를 합산해서, 월급으로 생활이 되는지 즉시 확인합니다.")

    lc1, lc2 = st.columns(2)
    with lc1:
        st.markdown("**💰 수입**")
        _yearly = st.session_state.get("user_income", 0)
        _default_monthly = _yearly // 12 if _yearly > 0 else 0
        lv_income = st.number_input("월 소득 (만원)", min_value=0,
                                     value=_default_monthly,
                                     step=10, key="lv_income", help="알바비, 월급, 용돈 등 전부")
        lv_support = st.number_input("정부 지원금 (만원/월)", min_value=0, value=0, step=5, key="lv_support",
                                     help="청년월세지원 등 (모르면 0)")
    with lc2:
        st.markdown("**🏠 주거비**")
        lv_rent = st.number_input("월세 (만원)", min_value=0, value=50, step=5, key="lv_rent")
        lv_manage = st.number_input("관리비 (만원)", min_value=0, value=8, step=1, key="lv_manage")

    st.markdown("**🛒 생활비**")
    lc3, lc4, lc5 = st.columns(3)
    with lc3:
        lv_food = st.number_input("식비 (만원)", min_value=0, value=30, step=5, key="lv_food")
        lv_transport = st.number_input("교통비 (만원)", min_value=0, value=5, step=1, key="lv_transport")
    with lc4:
        lv_phone = st.number_input("통신비 (만원)", min_value=0, value=5, step=1, key="lv_phone")
        lv_util = st.number_input("전기/수도/가스 (만원)", min_value=0, value=5, step=1, key="lv_util")
    with lc5:
        lv_etc = st.number_input("기타 (만원)", min_value=0, value=10, step=5, key="lv_etc")
        lv_save = st.number_input("저축 목표 (만원)", min_value=0, value=0, step=5, key="lv_save")

    if st.button("💡 생활 가능 여부 진단", use_container_width=True, type="primary", key="lv_calc"):
        total_income = lv_income + lv_support
        total_housing = lv_rent + lv_manage
        total_living = lv_food + lv_transport + lv_phone + lv_util + lv_etc
        total_expense = total_housing + total_living + lv_save
        remaining = total_income - total_expense

        if remaining >= 10:
            emoji, color, verdict = "✅", "#22C55E", "생활 가능!"
        elif remaining >= 0:
            emoji, color, verdict = "⚠️", "#F59E0B", "빠듯하지만 가능"
        else:
            emoji, color, verdict = "🚨", "#EF4444", "생활 어려움"

        result_html = f"""<div style="text-align:center;">
<div style="font-size:42px; font-weight:900; color:{color};">{remaining:+,.0f}만원</div>
<div style="font-size:16px; font-weight:600; color:{color};">{emoji} {verdict}</div>
<div style="font-size:13px; color:#64748B; margin-top:4px;">수입 {total_income}만 - 지출 {total_expense}만</div>
</div>"""
        card(result_html)

        # 상세 breakdown
        st.markdown("**📊 상세 내역**")
        import pandas as pd
        breakdown = pd.DataFrame({
            "항목": ["월세", "관리비", "식비", "교통비", "통신비", "공과금", "기타", "저축"],
            "금액(만원)": [lv_rent, lv_manage, lv_food, lv_transport, lv_phone, lv_util, lv_etc, lv_save]
        })
        st.bar_chart(breakdown.set_index("항목"), color=["#6366F1"])

        housing_ratio = total_housing / total_income * 100 if total_income > 0 else 0
        st.metric("주거비 비율 (수입 대비)", f"{housing_ratio:.0f}%",
                  delta="적정" if housing_ratio <= 30 else "과부담" if housing_ratio <= 50 else "위험",
                  delta_color="normal" if housing_ratio <= 30 else "inverse")
        if housing_ratio > 30:
            st.warning(f"💡 주거비가 소득의 {housing_ratio:.0f}%입니다. 30% 이하가 권장됩니다. 정부 지원금이나 더 저렴한 매물을 검토해보세요.")

# [Tab 5] 금융 네비게이터
with tab_dict:
    st.markdown("### 🧭 금융 네비게이터 (Ensemble Engine)")
    st.markdown("<p style='margin-bottom: 20px;'>단어만 아는 것을 넘어, <b>내 상황에 필요한 행동</b>까지 연결해 드립니다.</p>", unsafe_allow_html=True)
    
    # --- 0. Ensemble Persona Analysis ---
    u_stat = st.session_state.get("user_status", "대학생")
    u_asset = st.session_state.get("user_assets", 2000)

    # Map English status to Korean for logic (internal keys are Korean)
    status_en_to_ko = {"Student": "대학생", "Worker": "직장인", "Job Seeker": "취업준비생", "Entrepreneur": "창업자"}
    u_stat_ko = status_en_to_ko.get(u_stat, u_stat)

    # Logic for Persona
    recs = []
    if u_stat_ko in ("대학생", "취업준비생"):
        persona_title = "🌱 사회초년생/학생을 위한 추천"
        recs = ["중기청 대출", "HUG 보증보험", "확정일자"]
        msg = f"**{u_stat}**이신가요? 금리가 낮은 **중기청 대출**과 보증금을 지킬 **HUG 보증보험**이 가장 중요합니다!"
    else:
        persona_title = "💼 직장인/신혼부부를 위한 추천"
        recs = ["버팀목 대출", "LTV", "DSR"]
        msg = f"**{u_stat}**이시군요! 소득 기반의 **대출 한도(LTV/DSR)** 확인이 필수입니다."

    st.info(f"💡 **[AI Ensemble Analysis]** {msg}")
    
    # --- 1. Filter ---
    # Using columns for filter buttons with callback to ensure single-click update
    
    if "dict_filter" not in st.session_state:
        st.session_state.dict_filter = "All"
        
    def set_filter(f):
        st.session_state.dict_filter = f
        
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
    
    current = st.session_state.dict_filter
    
    with f_col1:
        if st.button("All View", type="primary" if current == "All" else "secondary", use_container_width=True):
            set_filter("All")
            st.rerun()
    with f_col2:
        if st.button("🔍 집 찾기", type="primary" if current == "search" else "secondary", use_container_width=True):
            set_filter("search")
            st.rerun()
    with f_col3:
        if st.button("✍️ 계약하기", type="primary" if current == "contract" else "secondary", use_container_width=True):
            set_filter("contract")
            st.rerun()
    with f_col4:
        if st.button("🛡️ 거주/보증", type="primary" if current == "live" else "secondary", use_container_width=True):
            set_filter("live")
            st.rerun()
    with f_col5:
        if st.button("💰 대출/지원", type="primary" if current == "loan" else "secondary", use_container_width=True):
            set_filter("loan")
            st.rerun()

    divider("10px 0 20px 0")

    terms_data = [
        {
            "term": "LTV", 
            "full": "주택담보인정비율",
            "desc": "집값을 기준으로 최대로 빌릴 수 있는 대출 금액의 비율입니다.",
            "example": "내 집값에 LTV(%)를 곱하면 대출 한도가 나옵니다.",
            "icon": "analytics",
            "tags": ["loan", "search"],
            "interactive": "ltv_calc"
        },
        {
            "term": "DSR", 
            "full": "총부채원리금상환비율",
            "desc": "내 연봉에서 갚아야 할 모든 대출의 원금+이자가 차지하는 비율입니다.",
            "example": "연봉이 높을수록 대출 한도가 늘어납니다.",
            "icon": "account_balance_wallet",
            "tags": ["loan"],
            "interactive": "dsr_calc"
        },
        {
            "term": "확정일자", 
            "full": "보증금 안전벨트",
            "desc": "동사무소에서 '이 날짜에 계약이 있었다'고 증명해주는 도장입니다.",
            "example": "이사 당일 전입신고+확정일자를 받아야 경매 넘어가도 보호받아요!",
            "icon": "verified",
            "tags": ["contract"],
            "interactive": None
        },
        {
            "term": "특약사항", 
            "full": "계약서 추가 조항",
            "desc": "표준 계약서에 없는 추가 약속을 적는 곳입니다.",
            "example": "예: '입주 전 곰팡이 제거 완료' 등을 명시하세요!",
            "icon": "edit_note",
            "tags": ["contract"],
            "interactive": None
        },
        {
            "term": "HUG 보증보험", 
            "full": "전세금 반환 보증",
            "desc": "집주인이 보증금을 안 줄 때 HUG가 대신 갚아주는 보험입니다.",
            "example": "전세사기가 걱정된다면 가입 필수! (집주인 동의 필요 없음)",
            "icon": "shield",
            "tags": ["live"],
            "interactive": "hug_check",
            "action_label": "HUG 바로가기",
            "action_target": "https://www.khug.or.kr/"
        },
        {
            "term": "전입신고", 
            "full": "이사 신고",
            "desc": "새로운 집에 들어와서 산다고 관공서에 알리는 절차입니다.",
            "example": "정부24 앱으로 5분 만에 가능! 이사 후 14일 내 필수.",
            "icon": "home",
            "tags": ["live"],
            "action_label": "정부24 바로가기",
            "action_target": "https://www.gov.kr"
        },
        {
            "term": "중기청 대출", 
            "full": "중소기업 청년 전세대출",
            "desc": "금리가 매우 낮은(1.2%~) 꿀 대출 상품입니다. 생애 1회만 가능.",
            "example": "전세 1억까지 보증금 100% 대출 가능! (조건 확인 필수)",
            "icon": "savings",
            "tags": ["loan", "search"],
            "action_label": "기금e든든 신청",
            "action_target": "https://nhuf.molit.go.kr/"
        }
    ]
    
    filtered_terms = [t for t in terms_data if st.session_state.dict_filter == "All" or st.session_state.dict_filter in t["tags"]]
    
    cols = st.columns(2)
    for i, item in enumerate(filtered_terms):
        with cols[i % 2]:
            with st.container():
                is_rec = item['term'] in recs
                badge_html = f"<span class='manus-chip chip-accent' style='font-size:11px; margin-bottom:8px;'>👍 {u_stat} 추천</span>" if is_rec else ""
                
                term_content = f"""{badge_html}
<div style="display:flex; align-items:center; margin-bottom:12px; margin-top:4px;">
<span class="material-icons" style="font-size: 28px; color: #6366F1; margin-right: 12px;">{item['icon']}</span>
<div>
<h3 style="margin:0; font-size:18px; color:#1E293B;">{item['term']}</h3>
<span style="font-size:12px; color:#64748B;">{item['full']}</span>
</div>
</div>
<p style="font-size:14px; color:#475569; line-height:1.5; margin-bottom:16px;">
{item['desc']}
</p>"""
                
                # Prepare Example Content (Only if NOT interactive)
                example_html = ""
                if not item.get("interactive"):
                    example_html = f"""<div style="background:#F8FAFC; padding:12px; border-radius:8px; border:1px solid #E2E8F0; margin-top: 12px;">
<span style="font-size:12px; font-weight:600; color:#6366F1;">💡 실전 예시</span><br>
<span style="font-size:13px; color:#334155;">{item['example']}</span>
</div>"""

                # Render Card (Static Content + Example)
                border_style = '2px solid #818CF8' if is_rec else '1px solid #E2E8F0'
                
                # 1. Open Card
                st.markdown(f"""<div class="manus-card" style="min-height: 240px; padding: 24px; position: relative; border: {border_style};">
{term_content}
{example_html}
</div>""", unsafe_allow_html=True)

                # 2. Interactive Section (Outside Card)
                if item.get("interactive"):
                    with st.container():
                         if item.get("interactive") == "ltv_calc":
                            with st.expander("🧮 LTV 모의 계산", expanded=True):
                                house_price = st.slider("집값 (억원)", 1.0, 10.0, 3.0, 0.5, key=f"ltv_{i}")
                                ltv_ratio = 80 if u_stat in ["대학생", "신혼부부"] else 70
                                limit = house_price * (ltv_ratio / 100)
                                st.markdown(f"**최대 {limit:.1f}억** 대출 가능 (LTV {ltv_ratio}%)")
                                
                         elif item.get("interactive") == "dsr_calc":
                            with st.expander("📉 DSR 한도 체크", expanded=True):
                                income = st.slider("연봉 (천만원)", 20, 100, 40, 5, key=f"dsr_{i}")
                                limit_yr = income * 0.4
                                st.markdown(f"연간 원리금 **{limit_yr:.0f}만원** 넘으면 대출 불가")

                         elif item.get("interactive") == "hug_check":
                             with st.expander("🛡️ 가입 조건 확인", expanded=True):
                                 if st.checkbox("공시가 알리미 앱 확인했나요?", key=f"hug_{i}"):
                                     st.success("✅ 이제 보증보험 가입 가능!")
                                 else:
                                     st.caption("👉 공시가격의 126% 이내여야 가입 가능")


                if item.get("action_label"):
                     _, btn_col = st.columns([0.5, 0.5])
                     with btn_col:
                         st.link_button(f"🚀 {item['action_label']}", item['action_target'], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🤖 Fin-Bot (금융 비서)")
    st.caption(f"💡 {st.session_state.user_name}님의 상황(나이/소득/자산)을 분석하여 맞춤형 답변을 드립니다.")
    st.caption("⚠️ AI 참고용 정보이며, 실제 금융 결정은 전문가 상담을 권장합니다.")

    if "fin_chat_messages" not in st.session_state:
        st.session_state.fin_chat_messages = [{"role": "assistant", "content": "안녕하세요! 금융 용어나 전세/월세 관련된 궁금한 점을 물어보세요."}]

    for msg in st.session_state.fin_chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.fin_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    st.warning("⚠️ API Key가 설정되지 않았습니다.")
                else:
                    try:
                        from langchain_openai import ChatOpenAI
                        from langchain_core.messages import HumanMessage, SystemMessage

                        # LLM 캐싱
                        if "finbot_llm" not in st.session_state or st.session_state.get("_finbot_key") != api_key:
                            st.session_state.finbot_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
                            st.session_state._finbot_key = api_key
                        llm = st.session_state.finbot_llm

                        profile_context = f"이름: {st.session_state.user_name}, 신분: {st.session_state.user_status}, 자산: {st.session_state.user_assets}만원"

                        system_prompt = f"""당신은 'Young & Home'의 AI 금융 비서입니다.
한국 청년 주거 금융 전문가로서, 사용자의 상황에 맞춰 친절하고 구체적으로 답변합니다.

[사용자 프로필]
{profile_context}

[전문 지식]
- 중소기업 취업청년 전월세보증금대출 (중기청): 금리 1.2%, 최대 1억, 중소기업 재직 필수
- 청년전용 버팀목 전세자금대출: 금리 1.5~2.1%, 최대 2억
- DSR (총부채원리금상환비율): 연소득 대비 대출 원리금 비율, 40% 이하 유지 필요
- LTV (주택담보인정비율): 집값 대비 대출 한도 비율
- 전세보증보험 (HUG): 보증금 미반환 시 보호, 보증료 약 0.128%/년
- 확정일자: 전입신고 시 반드시 받아야 대항력 확보
- 청년월세지원: 월 최대 20만원, 소득 중위 60% 이하

[답변 원칙]
1. 사용자 프로필 기반으로 맞춤 조언
2. 구체적 숫자와 조건을 포함
3. 실질적인 행동 가이드 제시
4. 한국어로 답변"""

                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=prompt)
                        ]

                        response = llm.invoke(messages)
                        answer = response.content
                        st.write(answer)
                        st.session_state.fin_chat_messages.append({"role": "assistant", "content": answer})

                    except Exception as e:
                        st.error(f"오류 발생: {e}")
