
import streamlit as st
import os
from src.utils.ui import setup_page, draw_sidebar, T, card, spacer, divider

setup_page("Finance")
draw_sidebar()

st.markdown(f"## 💰 {T('btn_calc')}")
st.markdown("금융 지식이 없어도 괜찮아요. AI가 내 상황에 맞는 전세대출과 자금 계획을 세워드립니다.")

spacer("20px")

# 4개의 탭
tab_rec, tab_vs, tab_dsr, tab_dict = st.tabs(["🤖 AI 대출 추천", "📊 전월세 비교", "🏦 대출 한도 진단", "📖 금융 용어 사전"])

from src.agents.finance import FinancialAgent
fin_agent = FinancialAgent()

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
            risk_content = f"""
            <div class="risk-card">
                <span style="background:#EEF2FF; color:#4F46E5; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{rec['tag']}</span>
                <h3 style="margin:8px 0; color:#1E293B;">{rec['name']}</h3>
                <div style="display:flex; gap:20px; color:#475569; font-size:14px;">
                    <span>💰 금리: <b>{rec['rate']}</b></span>
                    <span>📏 한도: <b>{rec['limit']}</b></span>
                </div>
                <p style="margin-top:8px; margin-bottom:0; color:#64748B; font-size:13px;">{rec['desc']}</p>
            </div>
            """
            st.markdown(risk_content, unsafe_allow_html=True)

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
        
        win_content = f"""
        <h2 style="color:{win_text}; margin:0;">🎉 {winner_icon}</h2>
        <p style="font-size:18px; color:#475569; margin-top:10px;">
        한 달에 약 <b>{save_amt:.1f}만원</b>을 아낄 수 있습니다.
        </p>
        """
        card(win_content, style=f"background:{win_color} !important; border:2px solid {win_border}; text-align:center;")
        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"**전세 선택 시** (월 지출)")
            st.markdown(f"<span style='font-size:24px; font-weight:bold; color:#3B82F6'>{result['jeonse']['monthly_cost']:.1f}만원</span>", unsafe_allow_html=True)
            st.caption(f"이자 {result['jeonse']['breakdown']['interest']:.1f} + 관리비 10.0")
        with m2:
            st.markdown(f"**월세 선택 시** (월 지출)")
            st.markdown(f"<span style='font-size:24px; font-weight:bold; color:#EA580C'>{result['rent']['monthly_cost']:.1f}만원</span>", unsafe_allow_html=True)
            st.caption(f"월세 {result['rent']['breakdown']['rent']} + 관리비 10.0")

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

# [Tab 4] 금융 네비게이터
with tab_dict:
    st.markdown("### 🧭 금융 네비게이터 (Ensemble Engine)")
    st.markdown("<p style='margin-bottom: 20px;'>단어만 아는 것을 넘어, <b>내 상황에 필요한 행동</b>까지 연결해 드립니다.</p>", unsafe_allow_html=True)
    
    # --- 0. Ensemble Persona Analysis ---
    u_stat = st.session_state.user_status
    u_asset = st.session_state.user_assets
    
    # Logic for Persona
    recs = []
    if u_stat == "대학생" or u_stat == "취업준비생":
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
                
                term_content = f"""
                {badge_html}
                <div style="display:flex; align-items:center; margin-bottom:12px; margin-top:4px;">
                <span class="material-icons" style="font-size: 28px; color: #6366F1; margin-right: 12px;">{item['icon']}</span>
                <div>
                <h3 style="margin:0; font-size:18px; color:#1E293B;">{item['term']}</h3>
                <span style="font-size:12px; color:#64748B;">{item['full']}</span>
                </div>
                </div>
                <p style="font-size:14px; color:#475569; line-height:1.5; margin-bottom:16px;">
                {item['desc']}
                </p>
                """
                
                # Prepare Example Content (Only if NOT interactive)
                example_html = ""
                if not item.get("interactive"):
                    example_html = f"""
                    <div style="background:#F8FAFC; padding:12px; border-radius:8px; border:1px solid #E2E8F0; margin-top: 12px;">
                        <span style="font-size:12px; font-weight:600; color:#6366F1;">💡 실전 예시</span><br>
                        <span style="font-size:13px; color:#334155;">{item['example']}</span>
                    </div>
                    """

                # Render Card (Static Content + Example)
                border_style = '2px solid #818CF8' if is_rec else '1px solid #E2E8F0'
                
                # 1. Open Card
                st.markdown(f"""
                <div class="manus-card" style="min-height: 240px; padding: 24px; position: relative; border: {border_style};">
                    {term_content}
                    {example_html}
                </div>
                """, unsafe_allow_html=True)

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
                        from src.agents.recommender import RecommenderAgent
                        agent = RecommenderAgent(openai_api_key=api_key)
                    
                        profile_context = {
                            "name": st.session_state.user_name,
                            "status": st.session_state.user_status,
                            "assets": st.session_state.user_assets
                        }
                        
                        ai_query = f"""
                        내 상황: {profile_context}
                        질문: {prompt}
                        금융 전문가로서 친절하고 구체적으로 답변해줘.
                        """
                        response = agent.run(ai_query, language="KO", user_profile=profile_context)
                        st.write(response)
                        st.session_state.fin_chat_messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
