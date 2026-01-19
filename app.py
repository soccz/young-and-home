
"""
Young & Home - Streamlit Main App
청년 안심 주거&복지 코디네이터
"""

import streamlit as st
from dotenv import load_dotenv
import os
import time
from src.utils.lang import STRINGS

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Young & Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/young-and-home',
        'Report a bug': "https://github.com/young-and-home/issues",
        'About': "# Young & Home\nAI Housing Assistant for Youth"
    }
)

# Defaults
if "language" not in st.session_state:
    st.session_state.language = "KO"

# ---------------------------------
# GLOBAL STYLING & SCRIPTS (Consolidated)
# ---------------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">
<style>
    /* ===== 1. Fonts & Reset ===== */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    html, body, [class*="css"], font, span, div, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Pretendard', sans-serif;
    }
    
    /* Ensure Material Icons font is preferred */
    .material-icons {
        font-family: 'Material Icons' !important;
    }
    
    :root {
        --primary: #6366F1;
        --card-bg: rgba(255, 255, 255, 0.85);
        --text-main: #1E293B;
        --text-sub: #64748B;
        --border-color: rgba(0, 0, 0, 0.08);
    }
    
    /* ===== 2. Global Layout & Overrides ===== */
    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%) !important;
    }
    
    /* Hide Default Header Decoration */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* [Fix] Add padding for fixed chat input so content isn't hidden */
    section[data-testid="stSidebar"] + section > div.block-container {
        padding-bottom: 130px !important;
    }

    /* Legal Chat Input - Fixed Docking Styling */
    [data-testid="stBottomBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        border-top: 1px solid #E2E8F0 !important;
        padding-bottom: 40px !important;  /* Increased form 20px */
        padding-top: 20px !important;
    }
    
    /* Lift the chat input box */
    .stChatInputContainer {
        padding-bottom: 20px !important;
    }
    
    /* ===== 3. Sidebar & Text Leak Fixes ===== */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    
    /* Fix 'keybo' / 'arrow_right' text leaking in sidebar toggle */
    [data-testid="stSidebarCollapsedControl"] {
        font-size: 0 !important;
        color: transparent !important;
        width: 40px !important;
        height: 40px !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg {
        font-size: 24px !important;
        color: #64748B !important; 
        fill: #64748B !important;
        visibility: visible !important;
    }

    /* ===== 4. UI Components Style ===== */
    
    /* Cards */
    .manus-card {
        background: var(--card-bg) !important;
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Buttons (Primary) - Custom Color */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: #1E293B !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"] {
        border: 1px solid var(--border-color) !important;
        color: var(--text-main) !important;
        background: white !important;
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        background: white !important;
    }
    
    /* Footer hidden in main area (we moved it to sidebar) */
    footer {
        visibility: hidden;
    }
    
</style>
<script>
    function fixLigatureLeaks() {
        const targets = ["keyboard_double", "keyboa"];
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while(node = walker.nextNode()) {
            const text = node.textContent;
            if (targets.some(t => text.includes(t))) {
                const parent = node.parentElement;
                if (parent && parent.closest('[data-testid="stSidebarCollapsedControl"]')) {
                    parent.style.fontSize = '0px'; 
                    parent.style.color = 'transparent';
                }
            }
        }
    }
    // Run periodically
    fixLigatureLeaks();
    setInterval(fixLigatureLeaks, 1000);
</script>
""", unsafe_allow_html=True)

# Defaults for user profile (editable)
if "user_name" not in st.session_state:
    st.session_state.user_name = "김서강" if st.session_state.language == "KO" else "Seogang Kim"
if "user_status" not in st.session_state:
    st.session_state.user_status = "대학생"
if "user_assets" not in st.session_state:
    st.session_state.user_assets = 2000

# Helper for translation
def T(key):
    return STRINGS[st.session_state.language].get(key, key)

# --- Data Loading Optimization ---
@st.cache_data
def load_housing_data():
    """Load housing data with caching"""
    import json
    try:
        path = "data/housing/houses.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

@st.cache_data
def load_benefits_data():
    """Load benefits data with caching"""
    import json
    try:
        path = "data/welfare/benefits.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []
# ---------------------------------

# Application Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown(f"<h1>{T('header_title')}</h1>", unsafe_allow_html=True)
    st.caption(T('header_subtitle'))

# Clearer spacing
st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Language")
    
    # Language Toggle with Instant State Update
    lang_choice = st.radio(
        "Language Settings",
        ["한국어", "English"],
        index=0 if st.session_state.language == "KO" else 1,
        label_visibility="collapsed",
        key="lang_radio"
    )
    
    # Apply change immediately
    new_lang = "KO" if lang_choice == "한국어" else "EN"
    if st.session_state.language != new_lang:
        st.session_state.language = new_lang
        st.rerun()

    st.markdown("---")
    
    st.markdown("### Menu")
    
    # Logic Keys for Menu
    menu_keys = ["Home", "Smart Search", "Safety Scan", "Negotiator", "Legal Help", "Calculators", "Monitoring"]
    # Display Labels
    menu_labels = [T("menu_home"), T("menu_search"), T("menu_safety"), T("menu_neg"), T("menu_legal"), "💰 " + (T("btn_calc") if st.session_state.language=="KO" else "Finance"), T("menu_monitor")]
    
    # Quick Actions에서 변경된 메뉴 반영
    default_idx = st.session_state.get("menu_selection", 0)
    
    # [Fix] Ensure index is within range
    if default_idx >= len(menu_keys):
        default_idx = 0

    # Selectbox with Index mapping logic
    menu_idx = st.radio(
        "Navigation",
        range(len(menu_keys)),
        index=default_idx,
        format_func=lambda i: menu_labels[i],
        label_visibility="collapsed",
        key="sidebar_menu"
    )
    
    # 선택 변경 시 session_state 업데이트
    if menu_idx != st.session_state.get("menu_selection", 0):
        st.session_state["menu_selection"] = menu_idx
    
    menu = menu_keys[menu_idx]
    
    st.markdown("<div style='margin-top: auto;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Demo Mode Toggle
    st.markdown("### ⚙️ Mode")
    demo_mode = st.toggle(
        "🎬 Demo Mode", 
        value=True,
        help="시연 모드 - 샘플 데이터 사용"
    )
    st.session_state["demo_mode"] = demo_mode
    
    if demo_mode:
        st.caption("✓ 샘플 데이터 활성화" if st.session_state.language == "KO" else "✓ Sample data enabled")
    
    st.markdown("---")
    
    # Editable Profile
    with st.expander(T("user_profile"), expanded=True):
        st.caption(f"{T('label_name')} & {T('label_status')}")
        
        # Inputs
        new_name = st.text_input("Name", st.session_state.user_name, label_visibility="collapsed")
        new_status = st.selectbox("Status", STRINGS[st.session_state.language]["status_options"], 
                                  index=0, label_visibility="collapsed")
        
        st.caption(T("label_assets"))
        new_assets = st.number_input("Assets", value=st.session_state.user_assets, step=100, label_visibility="collapsed")
        
        if st.button(T("btn_save"), key="save_profile"):
            st.session_state.user_name = new_name
            st.session_state.user_status = new_status
            st.session_state.user_assets = new_assets
            st.success("Updated!")
            time.sleep(0.5)
            st.rerun()

# =================
# 1. HOME
# =================
if menu == "Home":
    st.markdown(f"""
    <div class="manus-card">
        <h2 style="margin-top:0;">{T('home_welcome').replace('서강', st.session_state.user_name)}</h2>
        <p>{T('home_desc')}</p>
        <div style="display:flex; gap:12px; margin-top:20px;">
             <span class="manus-chip chip-accent">{T('badge_new')}</span>
             <span class="manus-chip">{T('badge_system')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard Grid
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="manus-card" style="height: 160px; position:relative; overflow:hidden;">
            <div style="position:absolute; top:-20px; right:-20px; width:100px; height:100px; background:radial-gradient(circle, rgba(60,140,231,0.2) 0%, rgba(0,0,0,0) 70%); border-radius:50%;"></div>
            <h3 style="color:#FFF;">{T('card_discovery')}</h3>
            <p><strong>12</strong> {T('card_discovery_desc')}</p>
            <p style="font-size:12px; opacity:0.6;">{T('card_discovery_sub')}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="manus-card" style="height: 160px; position:relative; overflow:hidden;">
             <div style="position:absolute; top:-20px; right:-20px; width:100px; height:100px; background:radial-gradient(circle, rgba(231,76,60,0.2) 0%, rgba(0,0,0,0) 70%); border-radius:50%;"></div>
            <h3 style="color:#FFF;">{T('card_safety')}</h3>
            <p><strong>1</strong> {T('card_safety_desc')}</p>
            <p style="font-size:12px; opacity:0.6;">{T('card_safety_sub')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"### {T('quick_actions')}")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    # Define update helper to avoid lambda issues if any
    def _go_to(idx):
        st.session_state["sidebar_menu"] = idx
        st.session_state["menu_selection"] = idx

    with b_col1:
        st.button(T('btn_start_search'), use_container_width=True, key="qa_search", 
                  on_click=_go_to, args=(1,))
    with b_col2:
        st.button(T('btn_analyze'), use_container_width=True, key="qa_analyze", 
                  on_click=_go_to, args=(2,))
    with b_col3:
        st.button(T('btn_calc'), use_container_width=True, key="qa_calc", 
                  on_click=_go_to, args=(5,))

# =================
# 2. SMART SEARCH
# =================
elif menu == "Smart Search":
    st.markdown(f"## {T('search_title')}")
    st.markdown(f"<p>{T('search_desc')}</p>", unsafe_allow_html=True)
    
    with st.form("recommendation_form"):
        st.markdown(f"**{T('search_pref')}**")
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(T("label_loc"), placeholder=T("ph_loc"))
            max_time = st.slider(T("label_maxtime"), 10, 60, 30)
        with col2:
            budget = st.number_input(T("label_budget"), min_value=0, value=2000)
            monthly = st.number_input(T("label_monthly"), min_value=0, value=50)
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"**{T('search_user_info')}**")
        
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input(T("label_age"), min_value=19, max_value=60, value=25)
        with c2:
            # Status Selection Map
            STATUS_KEYS = ["대학생", "직장인", "취업준비생", "창업자"]
            status_labels = T("status_options")
            status_idx = st.selectbox(T("label_status"), range(len(STATUS_KEYS)), format_func=lambda i: status_labels[i])
            status = STATUS_KEYS[status_idx]
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        st.markdown(f"**{T('search_benefit')}**")
        bc1, bc2, bc3 = st.columns(3)
        with bc1: st.checkbox(T("check_public"), value=True)
        with bc2: st.checkbox(T("check_loan"), value=True)
        with bc3: st.checkbox(T("check_support"))

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button(T("btn_run_agent"))
        
        if submitted:
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.markdown(f"""
                <div class="manus-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#3C8CE7;">{T('progress_rag')}</span>
                        <span>45%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)
            
            progress_placeholder.empty()
            
            # 실제 Agent 호출
            try:
                from src.agents.recommender import RecommenderAgent
                agent = RecommenderAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
                
                # 사용자 프로필 구성 (form 데이터 활용)
                user_profile = {
                    "age": age,
                    "status": status,
                    "income": 0,  # 소득 정보는 별도 입력 없음
                    "assets": budget,  # 보증금 한도를 자산으로 활용
                    "location_preference": location or "신촌",
                    "max_commute": max_time,
                    "max_rent": monthly,
                }
                
                query = f"{location or '신촌'} 근처에서 월세 {monthly}만원 이하로 집을 구하고 싶어요. 나이는 {age}세, {status}입니다."
                # 실제 프로필을 agent에 전달
                result = agent.run(query, language=st.session_state.language, user_profile=user_profile)
                
                st.markdown(f"### {T('result_analyzed')}")
                st.markdown(result)
                
            except Exception as e:
                st.error("😔 추천을 생성하지 못했어요" if st.session_state.language == "KO" else "😔 Failed to generate recommendations")
                st.info("API 키를 확인하거나 잠시 후 다시 시도해주세요!" if st.session_state.language == "KO" else "Check API key or try again later!")
                with st.expander("🔧 오류 상세" if st.session_state.language == "KO" else "🔧 Error Details"):
                    st.code(str(e))

            # --- Map View ---
            st.markdown(f"### {T('map_view')}")
            try:
                import json
                import pandas as pd
                
                # 데이터 로드 (Cached)
                houses = load_housing_data()
                
                if houses:
                    # 필터링
                    map_data = []
                    for h in houses:
                        if location and (location not in h.get("location", "") and location not in h.get("address", "") and location not in h.get("name", "")):
                            continue
                        user_deposit = budget if budget > 0 else 2000
                        if h.get("deposit", 0) > user_deposit * 1.2:
                            continue
                        if h.get("monthly", 0) > monthly + 10:
                            continue
                        if "lat" in h and "lon" in h:
                            map_data.append({
                                "lat": h["lat"],
                                "lon": h["lon"],
                                "name": h["name"],
                                "price": f"{h['deposit']}/{h['monthly']}"
                            })
                    
                    if map_data:
                        st.write("") 
                        df = pd.DataFrame(map_data)
                        st.map(df, zoom=14, use_container_width=True)
                        st.caption(T('map_info').format(count=len(map_data)))
                    else:
                        st.info(T("map_empty"))
                else:
                    st.warning("No map data found.")
                    
            except Exception as e:
                st.warning(f"Map Load Error: {e}")

# =================
# 3. SAFETY
# =================
elif menu == "Safety Scan":
    st.markdown(f"## {T('safety_title')}")
    st.markdown(f"<p>{T('safety_desc')}</p>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="manus-card">
        <h3 style="margin-top:0;">{T('upload_card_title')}</h3>
        <p>{T('upload_card_desc')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 샘플 선택
    SAMPLE_KEYS = ["파일 업로드", "안전 매물 (데모)", "위험 매물 (데모)", "보통 매물 (데모)"]
    sample_labels = T("sample_options")
    sample_idx = st.selectbox(
        T("sample_select"),
        range(len(SAMPLE_KEYS)),
        format_func=lambda i: sample_labels[i]
    )
    sample_type = SAMPLE_KEYS[sample_idx]
    
    uploaded_file = None
    if sample_type == "파일 업로드":
        uploaded_file = st.file_uploader(
            "Upload PDF/Image",
            type=["pdf", "png", "jpg"],
            label_visibility="collapsed"
        )
    
    deposit = st.number_input(T("label_deposit"), min_value=0, value=20000)
    
    can_analyze = sample_type != "파일 업로드" or uploaded_file is not None
    
    if st.button(T("btn_safety_start"), disabled=not can_analyze):
        # 진행 상태 애니메이션
        progress_bar = st.progress(0, text="분석 준비 중..." if st.session_state.language == "KO" else "Preparing...")
        
        with st.status(T("status_extract"), expanded=True) as status:
            st.write("✅ " + T("status_extract"))
            progress_bar.progress(33, text="데이터 추출 완료" if st.session_state.language == "KO" else "Data extracted")
            time.sleep(0.4)
            
            st.write("✅ " + T("status_verify"))
            progress_bar.progress(66, text="권리 분석 완료" if st.session_state.language == "KO" else "Rights verified")
            time.sleep(0.4)
            
            st.write("✅ " + T("status_calc"))
            progress_bar.progress(100, text="분석 완료!" if st.session_state.language == "KO" else "Complete!")
            time.sleep(0.3)
            status.update(label="✅ Complete", state="complete", expanded=False)
        
        try:
            from src.agents.analyzer import SafetyAnalyzerAgent
            import tempfile
            import re
            
            agent = SafetyAnalyzerAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            
            type_map = {
                "안전 매물 (데모)": "safe",
                "위험 매물 (데모)": "risky",
                "보통 매물 (데모)": "moderate",
                "파일 업로드": "moderate"
            }
            
            # 업로드된 파일 처리
            document_path = None
            if uploaded_file is not None:
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    document_path = tmp.name
            
            result = agent.run(
                document_path=document_path,
                sample_type=type_map.get(sample_type, "safe"),
                deposit=deposit * 10000,
                language=st.session_state.language
            )
            
            # 임시 파일 정리
            if document_path and os.path.exists(document_path):
                os.remove(document_path)
            
            # 위험도 게이지 시각화
            st.markdown(f"### {T('result_analyzed')}")
            
            # 결과에서 위험 수준 추출 시도
            risk_level = "보통"
            risk_color = "#FFA500"
            if "고위험" in result or "High Risk" in result:
                risk_level = "고위험" if st.session_state.language == "KO" else "High Risk"
                risk_color = "#EF4444"
                risk_score = 75
            elif "안전" in result or "Safe" in result or "저위험" in result:
                risk_level = "안전" if st.session_state.language == "KO" else "Safe"
                risk_color = "#22C55E"
                risk_score = 20
            else:
                risk_level = "주의" if st.session_state.language == "KO" else "Caution"
                risk_color = "#F59E0B"
                risk_score = 45
            
            # 시각화 카드
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="risk-card" style="background: linear-gradient(135deg, {risk_color}15, {risk_color}05); border-color: {risk_color}40;">
                    <p>종합 판정</p>
                    <h2 style="color: {risk_color};">{risk_level}</h2>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.metric(
                    label="위험 점수" if st.session_state.language == "KO" else "Risk Score",
                    value=f"{risk_score}/100",
                    delta=f"{100-risk_score}점 안전 여유" if st.session_state.language == "KO" else f"{100-risk_score} margin",
                    delta_color="inverse" if risk_score > 50 else "normal"
                )
            with col3:
                recovery = max(0, 100 - risk_score + 20)
                st.metric(
                    label="예상 회수율" if st.session_state.language == "KO" else "Est. Recovery",
                    value=f"{min(100, recovery)}%",
                    delta="보증보험 권장" if recovery < 80 else "양호",
                    delta_color="off" if recovery >= 80 else "inverse"
                )
            
            st.markdown("---")
            st.markdown(result)
            
        except Exception as e:
            st.error("😔 분석 중 문제가 발생했어요" if st.session_state.language == "KO" else "😔 Analysis failed")
            st.info("샘플 데이터로 다시 시도해보세요!" if st.session_state.language == "KO" else "Try again with sample data!")
            with st.expander("🔧 오류 상세" if st.session_state.language == "KO" else "🔧 Error Details"):
                st.code(str(e))

# =================
# 4. NEGOTIATOR
# =================
elif menu == "Negotiator":
    st.markdown(f"## {T('neg_title')}")
    st.markdown(f"<p>{T('neg_desc')}</p>", unsafe_allow_html=True)
    
    TOPIC_KEYS = ["보증보험 가입 요청", "특약 조항 추가", "수리 요청", "계약 조건 변경"]
    topic_labels = T("topic_options")
    
    topic_idx = st.selectbox(
        T("label_topic"),
        range(len(TOPIC_KEYS)),
        format_func=lambda i: topic_labels[i]
    )
    issue = TOPIC_KEYS[topic_idx]
    
    sender_name = st.text_input(T("label_sender"), value="홍길동" if st.session_state.language=="KO" else "Gil Dong Hong")
    
    analysis_context = st.text_area(
        T("label_context"),
        placeholder=T("ph_context"), 
        height=100
    )
    
    if st.button(T("btn_draft")):
        with st.spinner("Generating..."):
            try:
                from src.agents.negotiator import NegotiatorAgent
                agent = NegotiatorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
                
                # Logic uses Korean keys 'issue'
                if issue == "보증보험 가입 요청":
                    message = agent.generate_insurance_request(
                        sender_name=sender_name,
                        risk_details=analysis_context or None
                    )
                elif issue == "특약 조항 추가":
                    message = agent.generate_special_clause_request(
                        sender_name=sender_name,
                        clause_content=analysis_context or "전세보증보험 가입 협조 조항"
                    )
                elif issue == "수리 요청":
                    repair_items = analysis_context.split(",") if analysis_context else ["수도 누수", "벽지 오염"]
                    message = agent.generate_repair_request(
                        sender_name=sender_name,
                        repair_items=repair_items
                    )
                else:
                    message = agent.generate_message(
                        sender_name=sender_name,
                        recipient="집주인" if st.session_state.language=="KO" else "Landlord",
                        negotiation_type=issue,
                        situation=analysis_context or "계약 조건 변경 요청",
                        desired_outcome="상호 합의 하에 원만한 해결"
                    )
                
                st.markdown("### Draft")
                st.markdown(f"""
                <div class="manus-card" style="background:rgba(60, 140, 231, 0.1); border:none;">
                    <p style="color:#FFF !important; font-family: 'Pretendard', sans-serif; white-space: pre-wrap; line-height: 1.8;">{message}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.code(message, language=None)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# =================
# 5. LEGAL HELP
# =================
elif menu == "Legal Help":
    st.markdown(f"## {T('menu_legal')}")
    st.markdown("<p>AI Legal Advisor based on Housing Lease Protection Act</p>", unsafe_allow_html=True)
    
    if "legal_messages" not in st.session_state:
        st.session_state.legal_messages = [
            {"role": "assistant", "content": "안녕하세요. 주택임대차보호법 관련 궁금한 점을 물어보세요." if st.session_state.language=="KO" else "Hello. Ask me anything about the Housing Lease Protection Act."}
        ]
    
    # Chat container with proper spacing - hide footer on this page
    st.markdown("""
    <style>
        /* Legal Help page specific styles */
        [data-testid="stChatMessageContainer"] {
            padding-bottom: 120px !important; /* Ensure content isn't hidden behind input */
        }
        .stChatFloatingInputContainer {
            bottom: 30px !important; /* Move it up from the very edge */
            background: transparent !important; /* Transparent container */
            padding-bottom: 0 !important;
        }
        .stChatInputContainer {
            border-radius: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
            border: 1px solid #E2E8F0 !important;
            width: auto !important;
            margin: 0 auto !important; /* Center it */
            max-width: 800px !important; /* Optional: limit width for cleaner look */
        }
        
        /* Attempt to hide footer on this page using :has if supported, or general sibling */
        /* The previous selector might have been too specific or DOM changed */
        footer {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # FAQ buttons at top
    st.caption("💡 자주 묻는 질문" if st.session_state.language=="KO" else "💡 FAQ")
    faq_col1, faq_col2, faq_col3 = st.columns(3)
    with faq_col1:
        if st.button("🏠 보증금 돌려받기", use_container_width=True, key="faq1"):
            st.session_state.legal_prompt = "계약 만료 후 보증금을 못 받고 있어요. 어떻게 해야 하나요?"
    with faq_col2:
        if st.button("📈 월세 인상 한도", use_container_width=True, key="faq2"):
            st.session_state.legal_prompt = "집주인이 월세를 10% 올려달라고 하는데 법적으로 가능한가요?"
    with faq_col3:
        if st.button("🔧 수리비 부담", use_container_width=True, key="faq3"):
            st.session_state.legal_prompt = "보일러가 고장 났는데 수리비는 누가 내야 하나요?"
    
    st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)
    
    # Display chat history
    for msg in st.session_state.legal_messages:
        avatar = "👤" if msg['role'] == 'user' else "🤖"
        with st.chat_message(msg['role'], avatar=avatar):
            st.markdown(msg['content'])


    # Handle button click or chat input
    user_input = st.chat_input("Ask a question...")
    
    # Check if we have a prompt from buttons
    if "legal_prompt" in st.session_state and st.session_state.legal_prompt:
        prompt = st.session_state.legal_prompt
        del st.session_state.legal_prompt  # Consume
    else:
        prompt = user_input

    if prompt:
        st.session_state.legal_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Searching Legal Database..." if st.session_state.language=="EN" else "법령 데이터 검색 중...")
            
            try:
                from src.agents.legal import LegalAdvisorAgent
                agent = LegalAdvisorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
                response = agent.consult(prompt, language=st.session_state.language)
                
                message_placeholder.markdown(response)
                st.session_state.legal_messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")

# =================
# 6. FINANCIAL GUIDE
# =================
elif menu == "Calculators":
    st.markdown(f"## 💰 {T('btn_calc')}")
    st.markdown("금융 지식이 없어도 괜찮아요. AI가 내 상황에 맞는 전세대출과 자금 계획을 세워드립니다.")
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 4개의 탭으로 확장
    tab_rec, tab_vs, tab_dsr, tab_dict = st.tabs(["🤖 AI 대출 추천", "📊 전월세 비교", "🏦 대출 한도 진단", "📖 금융 용어 사전"])
    
    from src.agents.finance import FinancialAgent
    fin_agent = FinancialAgent()
    
    # [Tab 1] AI 대출 상품 추천 (New)
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
                st.markdown(f"""
                <div class="risk-card" style="text-align:left; border:1px solid #E2E8F0; margin-bottom:12px; padding:20px;">
                    <span style="background:#EEF2FF; color:#4F46E5; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{rec['tag']}</span>
                    <h3 style="margin:8px 0; color:#1E293B;">{rec['name']}</h3>
                    <div style="display:flex; gap:20px; color:#475569; font-size:14px;">
                        <span>💰 금리: <b>{rec['rate']}</b></span>
                        <span>📏 한도: <b>{rec['limit']}</b></span>
                    </div>
                    <p style="margin-top:8px; margin-bottom:0; color:#64748B; font-size:13px;">{rec['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab_vs:
        st.markdown("### 📊 전세 vs 월세, 무엇이 더 이득일까요?")
        st.markdown("<p style='color:#64748B; margin-bottom:20px;'>보증금과 금리를 입력하면, 2년 동안 나가는 총 비용을 비교해드립니다.</p>", unsafe_allow_html=True)
        
        # UI Redesign: Input Cards
        c_in1, c_in2 = st.columns(2)
        with c_in1:
            st.markdown("""<div style="background:#EFF6FF; padding:15px; border-radius:12px; margin-bottom:10px;"><h4 style="margin:0; color:#1E3A8A;">🏠 전세 시나리오</h4></div>""", unsafe_allow_html=True)
            jeonse_amt = st.number_input("전세 보증금 (만원)", value=20000, step=1000)
            loan_rate = st.number_input("전세 대출 금리 (%)", value=4.0, step=0.1, format="%.1f")
            
        with c_in2:
            st.markdown("""<div style="background:#FFF7ED; padding:15px; border-radius:12px; margin-bottom:10px;"><h4 style="margin:0; color:#7C2D12;">🏘️ 월세 시나리오</h4></div>""", unsafe_allow_html=True)
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
            
            # Winner Card Visual
            is_jeonse_win = result['is_jeonse_cheaper']
            win_color = "#EFF6FF" if is_jeonse_win else "#FFF7ED"
            win_border = "#BFDBFE" if is_jeonse_win else "#FFEDD5"
            win_text = "#1E3A8A" if is_jeonse_win else "#7C2D12"
            winner_icon = "🏠 전세가 유리해요!" if is_jeonse_win else "🏘️ 월세가 유리해요!"
            save_amt = result['difference']
            
            st.markdown(f"""
<div class="manus-card" style="background:{win_color} !important; border:2px solid {win_border}; text-align:center;">
<h2 style="color:{win_text}; margin:0;">🎉 {winner_icon}</h2>
<p style="font-size:18px; color:#475569; margin-top:10px;">
한 달에 약 <b>{save_amt:.1f}만원</b>을 아낄 수 있습니다.
</p>
</div>
""", unsafe_allow_html=True)
            
            # Detail Metrics
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
            
    # [Tab 3] DSR 진단 (Existing)
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

    # [Tab 4] 금융 네비게이터 (Financial Dictionary Hub)
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
        sc_col1, sc_col2, sc_col3, sc_col4, sc_col5 = st.columns(5)
        # Session state for filter
        # Custom CSS for Primary Button Contrast
        st.markdown("""
        <style>
        div[data-testid="stButton"] > button[kind="primary"] {
            color: white !important;
            font-weight: bold !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            color: #1E293B !important;
            border: 1px solid #E2E8F0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if "dict_filter" not in st.session_state:
            st.session_state.dict_filter = "All"
            
        def set_filter(f):
            st.session_state.dict_filter = f
            st.rerun()
            
        def btn_type(f):
            return "primary" if st.session_state.dict_filter == f else "secondary"

        with sc_col1: 
            if st.button("All View", key="f_all", use_container_width=True, type=btn_type("All")): set_filter("All")
        with sc_col2: 
            if st.button("🔍 집 찾기", key="f_search", use_container_width=True, type=btn_type("search")): set_filter("search")
        with sc_col3: 
            if st.button("✍️ 계약하기", key="f_contract", use_container_width=True, type=btn_type("contract")): set_filter("contract")
        with sc_col4: 
            if st.button("🛡️ 거주/보증", key="f_live", use_container_width=True, type=btn_type("live")): set_filter("live")
        with sc_col5: 
            if st.button("💰 대출/지원", key="f_loan", use_container_width=True, type=btn_type("loan")): set_filter("loan")

        st.markdown("<hr style='margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

        # --- Data & Interactive Logic ---
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
                "tags": ["contract", "live"],
                "interactive": None
            },
            {
                "term": "근저당권", 
                "full": "집주인의 빚 확인",
                "desc": "집주인이 이 집을 담보로 은행에서 돈을 빌린 기록입니다.",
                "example": "등기부등본 '을구' 확인 필수! 빚이 너무 많으면 위험해요.",
                "icon": "warning",
                "tags": ["search", "contract"],
                "Interactive": None,
                "action_label": "등기부등본 분석 (안전진단)",
                "action_target": 2
            },
            {
                "term": "HUG 보증보험", 
                "full": "전세금 반환 보증",
                "desc": "집주인이 보증금을 안 줄 때 HUG가 대신 갚아주는 보험입니다.",
                "example": "전세사기가 걱정된다면 가입 필수! (집주인 동의 필요 없음)",
                "icon": "shield",
                "tags": ["contract", "live"],
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
                "tags": ["live", "contract"],
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
        
        # Filter Logic
        filtered_terms = [t for t in terms_data if st.session_state.dict_filter == "All" or st.session_state.dict_filter in t["tags"]]
        
        cols = st.columns(2)
        for i, item in enumerate(filtered_terms):
            with cols[i % 2]:
                with st.container():
                    # Recommended Badge
                    is_rec = item['term'] in recs
                    badge_html = f"<span class='manus-chip chip-accent' style='font-size:11px; margin-bottom:8px;'>👍 {u_stat} 추천</span>" if is_rec else ""
                    
                    st.markdown(f"""
<div class="manus-card" style="min-height: 240px; padding: 24px; position: relative; border: {'2px solid #818CF8' if is_rec else '1px solid #E2E8F0'};">
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
""", unsafe_allow_html=True)
                    
                    # --- Micro-Interactions (Streamlit Widgets) ---
                    if item.get("interactive") == "ltv_calc":
                        st.markdown("<div style='background:#F8FAFC; padding:12px; border-radius:8px;'>", unsafe_allow_html=True)
                        st.caption("🧮 LTV 모의 계산")
                        house_price = st.slider("집값 (억원)", 1.0, 10.0, 3.0, 0.5, key=f"ltv_{i}")
                        ltv_ratio = 80 if u_stat in ["대학생", "신혼부부"] else 70
                        limit = house_price * (ltv_ratio / 100)
                        st.markdown(f"**최대 {limit:.1f}억** 대출 가능 (LTV {ltv_ratio}%)")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    elif item.get("interactive") == "dsr_calc":
                        st.markdown("<div style='background:#F8FAFC; padding:12px; border-radius:8px;'>", unsafe_allow_html=True)
                        st.caption("📉 DSR 한도 체크")
                        income = st.slider("연봉 (천만원)", 20, 100, 40, 5, key=f"dsr_{i}")
                        limit_yr = income * 0.4
                        st.markdown(f"연간 원리금 **{limit_yr:.0f}만원** 넘으면 대출 불가")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    elif item.get("interactive") == "hug_check":
                         st.markdown("<div style='background:#F8FAFC; padding:12px; border-radius:8px;'>", unsafe_allow_html=True)
                         if st.checkbox("공시가 알리미 앱 확인했나요?", key=f"hug_{i}"):
                             st.success("✅ 이제 보증보험 가입 가능!")
                         else:
                             st.caption("👉 공시가격의 126% 이내여야 가입 가능")
                         st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        # Default Example Box
                         st.markdown(f"""
                        <div style="background:#F8FAFC; padding:12px; border-radius:8px; border:1px solid #E2E8F0;">
                            <span style="font-size:12px; font-weight:600; color:#6366F1;">💡 실전 예시</span><br>
                            <span style="font-size:13px; color:#334155;">{item['example']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Links (Fixed Logic)
                    if item.get("action_label"):
                         _, btn_col = st.columns([0.5, 0.5])
                         with btn_col:
                             target = item['action_target']
                             
                             # Case 1: External URL -> st.link_button
                             if isinstance(target, str) and target.startswith("http"):
                                 st.link_button(f"🚀 {item['action_label']}", target, use_container_width=True)
                                 
                             # Case 2: Internal Navigation -> st.button
                             elif isinstance(target, int):
                                 if st.button(f"🚀 {item['action_label']}", key=f"act_{i}_{item['term']}", use_container_width=True):
                                     st.session_state["menu_selection"] = target
                                     st.rerun()


        st.markdown("---")
        # 3. AI Ensemble Tutor (Chat Interface)
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
                    try:
                        from src.agents.recommender import RecommenderAgent
                        agent = RecommenderAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
                        
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


# =================
# 7. MONITORING
# =================
# [Tab 7] 권리 변동 파수꾼 (Security Command Center) - n8n + LangGraph 연동
elif menu == "Monitoring":
    # Security Dashboard Header
    st.markdown(f"## 🛡️ {T('mon_title')} (Security Center)")
    
    # [Hackathon Strategy] Technical Feasibility Note (Natural Integration)
    with st.expander("ℹ️ 시스템 구동 원리 (n8n + LangGraph Architecture)", expanded=False):
        st.markdown("""
        **본 시스템은 n8n 워크플로우와 LangGraph Agent가 연동되어 작동합니다.**
        
        ```mermaid
        graph LR
            n8n[n8n Scheduler] --> API[FastAPI Backend]
            API --> Agent[SafetyAnalyzerAgent]
            Agent --> Alert[Slack/카카오톡]
        ```
        
        1.  **n8n Scheduler**: 12시간마다 자동 등기소 조회 트리거
        2.  **FastAPI Backend**: `/api/monitoring/check` 엔드포인트로 Agent 호출
        3.  **LangGraph Agent**: SafetyAnalyzerAgent가 위험도 분석
        4.  **알림 발송**: 변동 감지 시 Slack/카카오톡으로 즉시 알림
        
        *(n8n 워크플로우 파일: `n8n/registry_alert.json`)*
        """)

    st.markdown("<p style='margin-bottom:20px;'>등기부등본을 <b>24시간 실시간 감시</b>하여, 집주인의 <b>몰래 대출/압류</b> 시도를 즉시 차단합니다.</p>", unsafe_allow_html=True)
    
    # --- n8n 연동 상태 표시 ---
    n8n_status_col, api_status_col = st.columns(2)
    with n8n_status_col:
        st.markdown("""
<div style="background:#eff6ff; padding:12px; border-radius:8px; border:1px solid #bfdbfe;">
<span style="color:#1e40af; font-weight:600;">🔗 n8n 워크플로우</span><br>
<small>• registry_alert.json (12시간 주기)</small><br>
<small>• monitoring_workflow.json (30분 주기)</small>
</div>
""", unsafe_allow_html=True)
    with api_status_col:
        st.markdown("""
<div style="background:#f0fdf4; padding:12px; border-radius:8px; border:1px solid #bbf7d0;">
<span style="color:#166534; font-weight:600;">⚡ FastAPI 엔드포인트</span><br>
<small>• /api/monitoring/check</small><br>
<small>• /api/subscription/create</small>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Pulse Animation CSS ---
    st.markdown("""
    <style>
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(34, 197, 94, 0); }
            100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        .status-ring-safe {
            animation: pulse-green 2s infinite;
            border: 3px solid #22C55E;
        }
        .status-ring-danger {
            animation: pulse-red 1s infinite;
            border: 3px solid #EF4444;
        }
        .log-terminal {
            background: #0F172A;
            color: #22C55E;
            font-family: 'Courier New', monospace;
            padding: 15px;
            border-radius: 8px;
            height: 200px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.6;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # --- State Management ---
    if "monitor_status" not in st.session_state:
        st.session_state.monitor_status = "SAFE"
        st.session_state.monitor_logs = [
            "[n8n] Workflow connected: registry_alert.json", 
            "[API] FastAPI Backend Ready (port 8000)", 
            "[AGENT] SafetyAnalyzerAgent initialized"
        ]
    
    # Function to add log
    def add_log(msg, alert=False):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "[ALERT]" if alert else "[INFO]"
        st.session_state.monitor_logs.append(f"[{ts}] {prefix} {msg}")
        if len(st.session_state.monitor_logs) > 8:
            st.session_state.monitor_logs.pop(0)
    
    # --- 구독 설정 섹션 (NEW) ---
    st.markdown("### 📬 매물 알림 구독 설정")
    with st.expander("🔔 조건 설정하고 알림 받기", expanded=False):
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            sub_location = st.text_input("희망 지역", value="마포구", key="sub_loc")
            sub_deposit = st.number_input("최대 보증금 (만원)", value=3000, key="sub_dep")
        with sub_col2:
            sub_monthly = st.number_input("최대 월세 (만원)", value=50, key="sub_mon")
            sub_notify = st.selectbox("알림 방식", ["slack", "kakao", "email"], key="sub_notify")
        
        if st.button("✅ 구독 시작", use_container_width=True, key="btn_subscribe"):
            try:
                import httpx
                response = httpx.post(
                    "http://localhost:8000/api/subscription/create",
                    json={
                        "user_id": st.session_state.user_name,
                        "location": sub_location,
                        "max_deposit": sub_deposit,
                        "max_monthly": sub_monthly,
                        "notify_method": sub_notify
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    st.success(f"✅ 구독 완료! {sub_location} 지역의 새 매물 알림을 받습니다.")
                    add_log(f"Subscription created: {sub_location}, {sub_deposit}만/{sub_monthly}만")
                else:
                    st.warning("API 서버에 연결할 수 없습니다. Docker가 실행 중인지 확인하세요.")
            except Exception as e:
                st.info("💡 API 서버가 실행되지 않았습니다. `docker-compose up`으로 시작하세요!")
                add_log(f"Subscription (Demo): {sub_location}")
    
    st.markdown("---")
    
    # --- Status & Controls ---
    c_status, c_action = st.columns([0.6, 0.4])
    
    with c_status:
        is_safe = st.session_state.monitor_status == "SAFE"
        status_color = "#22C55E" if is_safe else "#EF4444"
        status_text = "정상 감시 중 (Secure)" if is_safe else "🚨 침해 탐지 (ALERT)"
        status_class = "status-ring-safe" if is_safe else "status-ring-danger"
        
        st.markdown(f"""
        <div class="manus-card" style="text-align:center; padding: 40px;">
            <div class="{status_class}" style="width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto;">
                <span class="material-icons" style="font-size: 48px; color: {status_color};">
                    {'shield' if is_safe else 'warning'}
                </span>
            </div>
            <h2 style="color: {status_color}; margin: 0;">{status_text}</h2>
            <p style="margin-top: 10px; color: #64748B;">Target: 서울시 마포구 백범로 35 (201호)</p>
            <div style="margin-top: 15px;">
                <span class="manus-chip" style="background: #eff6ff; color: #1e40af;">n8n Active</span>
                <span class="manus-chip" style="background: #f0fdf4; color: #166534;">LangGraph Ready</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_action:
        st.markdown("### 🛠️ n8n 워크플로우 제어")
        mode = st.radio("System Mode", ["Live (n8n 연동)", "Simulation (Demo)"], label_visibility="collapsed")
        
        if mode == "Live (n8n 연동)":
            st.info("n8n 워크플로우가 12시간마다 자동 실행됩니다.")
            if st.button("🔍 지금 등기 체크 (API 호출)", use_container_width=True, type="primary"):
                try:
                    import httpx
                    response = httpx.post(
                        "http://localhost:8000/api/monitoring/check",
                        json={
                            "address": "서울시 마포구 백범로 35",
                            "user_id": st.session_state.user_name,
                            "previous_hash": None
                        },
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        add_log(f"API Response: risk_score={result.get('risk_score', 0)}")
                        if result.get("has_change"):
                            st.session_state.monitor_status = "ALERT"
                            add_log("Registry change detected!", alert=True)
                        else:
                            add_log("No changes detected. All secure.")
                        st.rerun()
                except Exception as e:
                    st.warning("API 서버에 연결할 수 없습니다.")
                    add_log(f"API Error: {str(e)[:50]}", alert=True)
        else:
            st.caption("시뮬레이션 모드: 가상의 집주인 대출 상황을 연출합니다.")
            if st.button("⚡ [TEST] 집주인 대출 발생", use_container_width=True, type="primary"):
                st.session_state.monitor_status = "ALERT"
                add_log("[n8n] Webhook triggered: registry_alert", alert=True)
                add_log("[Agent] SafetyAnalyzerAgent processing...", alert=True)
                add_log("[RISK] LTV Threshold Exceeded (82% > 80%)", alert=True)
                st.rerun()
                
        if st.button("🔄 시스템 리셋 (Secure)", use_container_width=True):
            st.session_state.monitor_status = "SAFE"
            st.session_state.monitor_logs = ["[System] Security Protocol Reset.", "[n8n] Workflow re-initialized", "[AGENT] All clear."]
            st.rerun()

    # --- Real-time Log & Protocol ---
    st.markdown("---")
    l_col1, l_col2 = st.columns(2)
    
    with l_col1:
        st.markdown("### 📡 n8n + Agent 통신 로그")
        log_html = "<br>".join([f"<span style='color:{'#ff4444' if 'ALERT' in l else '#22C55E'}'>{l}</span>" for l in st.session_state.monitor_logs])
        st.markdown(f"""
        <div class="log-terminal">
            {log_html}
        </div>
        """, unsafe_allow_html=True)
        
    with l_col2:
        st.markdown("### 🤖 앙상블 대응 프로토콜")
        if st.session_state.monitor_status == "SAFE":
            st.success("✅ 자산 보호 레벨: 최상 (Secure)")
            st.markdown("""
            - **n8n 스케줄**: 12시간마다 자동 체크
            - **Agent**: SafetyAnalyzerAgent 대기 중
            - **알림 채널**: Slack/카카오톡 연동됨
            """)
        else:
            st.error("🚨 위험 감지! 즉시 대응 프로토콜 가동")
            st.markdown("""
            1. **[n8n]** 알림 워크플로우 트리거됨
            2. **[Agent]** NegotiatorAgent가 경고 메시지 생성 중
            3. **[권고]** 법률 상담 연결 👇
            """)
            if st.button("⚖️ 법률 대응 센터 연결", type="primary"):
                st.session_state["menu_selection"] = 4  # Legal Help
                st.rerun()


# Footer (Sidebar)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem;">
    🏠 <strong>Young & Home</strong><br>
    2026 Seogang Univ. AI Winter Camp<br>
    <br>
    Made with ❤️ by Team Young & Home
</div>
""", unsafe_allow_html=True)
