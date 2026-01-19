
import streamlit as st
import os
import json
import time
from src.utils.lang import STRINGS

def load_css():
    st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">
    <style>
        /* ===== 1. Fonts & Reset ===== */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone');
        
        html, body, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .stButton, .stTextInput, .stSelectbox {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
        }
        
        /* Ensure Icons use their own Link */
        .material-icons, .material-icons-outlined, .material-symbols-rounded, .material-symbols-outlined {
            font-family: 'Material Icons' !important;
        }
        
        .material-icons { font-family: 'Material Icons' !important; }
        
        :root {
            --primary: #6366F1;
            --primary-dark: #4F46E5;
            --card-bg: rgba(255, 255, 255, 0.75);
            --card-border: rgba(255, 255, 255, 0.6);
            --text-main: #1E293B;
            --text-sub: #64748B;
            --shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
        }
        
        /* ===== 2. Global Layout ===== */
        .stApp {
            background: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 40%),
                linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%) !important;
            background-attachment: fixed !important;
        }
        header[data-testid="stHeader"] { background: transparent !important; }
        
        /* ===== Animations ===== */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ===== 3. UI Components ===== */
        .manus-card {
            background: var(--card-bg) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 28px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
            
            /* Phase 2: Polish (Animation) */
            animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        }
        .manus-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.12);
            border-color: rgba(99, 102, 241, 0.4);
        }
        
        /* Buttons */
        div[data-testid="stButton"] > button {
            border-radius: 12px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.95;
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            border: 1px solid rgba(0,0,0,0.08) !important;
            color: var(--text-main) !important;
            background: rgba(255, 255, 255, 0.8) !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            background: #FFFFFF !important;
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }
        
        /* Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
            border-radius: 14px !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(4px);
            color: var(--text-main) !important;
            transition: all 0.2s !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox > div > div:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
            background: #FFFFFF !important;
        }
        
        /* Badge/Chips */
        .manus-chip {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(241, 245, 249, 0.8);
            border: 1px solid rgba(203, 213, 225, 0.5);
            color: #475569;
        }
        .chip-accent {
            background: rgba(238, 242, 255, 0.9);
            border-color: rgba(199, 210, 254, 0.6);
            color: #4F46E5;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255,255,255,0.2);
            box-shadow: 20px 0 40px -20px rgba(0,0,0,0.05);
        }
        
        /* Metrics */
        div[data-testid="stMetricValue"] {
            font-weight: 700 !important;
            color: var(--text-main) !important;
        }
        
        /* Hide default footer */
        footer { visibility: hidden; }

        /* ===== 4. Helper Utils (Extracted from Inline) ===== */
        .stat-circle {
            position: absolute;
            top: -20px;
            right: -20px;
            width: 100px;
            height: 100px;
            border-radius: 50%;
        }
        .bg-blue-radial {
            background: radial-gradient(circle, rgba(60,140,231,0.2) 0%, rgba(0,0,0,0) 70%);
        }
        .bg-red-radial {
            background: radial-gradient(circle, rgba(231,76,60,0.2) 0%, rgba(0,0,0,0) 70%);
        }
        .no-margin-top { margin-top: 0 !important; }
        .mb-20 { margin-bottom: 20px !important; }
        .mt-20 { margin-top: 20px !important; }
        .text-sm-gray { font-size: 12px; opacity: 0.6; }
        .flex-gap-12 { display: flex; gap: 12px; }
        
        /* ===== 5. Page Specific Styles (Centralized) ===== */
        /* Calculators.py */
        .risk-card {
            text-align: left;
            border: 1px solid #E2E8F0;
            margin-bottom: 12px;
            padding: 20px;
            background: rgba(255,255,255,0.6);
            border-radius: 12px;
        }
        .box-blue {
            background:#EFF6FF; padding:15px; border-radius:12px; margin-bottom:10px;
        }
        .box-orange {
            background:#FFF7ED; padding:15px; border-radius:12px; margin-bottom:10px;
        }
        
        /* Monitoring.py */
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
        
        /* Legal_Help.py */
        [data-testid="stChatMessageContainer"] {
            padding-bottom: 120px !important; 
        }
        .stChatFloatingInputContainer {
            bottom: 30px !important; 
            background: transparent !important; 
            padding-bottom: 0 !important;
        }
        .stChatInputContainer {
            border-radius: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
            border: 1px solid #E2E8F0 !important;
            width: auto !important;
            margin: 0 auto !important;
            max-width: 800px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def setup_page(title="Young & Home"):
    if "language" not in st.session_state:
        st.session_state.language = "KO"
        
    st.set_page_config(
        page_title=title,
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    load_css()
    
    # Header
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(f"<h1>{T('header_title')}</h1>", unsafe_allow_html=True)
        st.caption(T('header_subtitle'))
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

def T(key):
    """Translation helper"""
    lang = st.session_state.get("language", "KO")
    return STRINGS[lang].get(key, key)

def draw_sidebar():
    # Hide default sidebar nav
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        .sidebar-link {
            text-decoration: none;
            color: #64748B;
            font-size: 14px;
            padding: 10px 12px;
            border-radius: 8px;
            display: block;
            margin-bottom: 4px;
            transition: all 0.2s;
        }
        .sidebar-link:hover {
            background: #F1F5F9;
            color: #1E293B;
        }
        .sidebar-link.active {
            background: #EEF2FF;
            color: #4F46E5;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # === 2. API Key Status (Moved to Top) ===
        if "api_key" not in st.session_state:
            st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")

        api_key = st.session_state.api_key
        
        if not api_key:
             st.error("🔑 OpenAI API Key를 입력해주세요")
             st.caption("⚠️ 기능 사용을 위해 필수입니다.")
             user_key = st.text_input("sk-... 형태로 입력", type="password", key="sidebar_api_key_top")
             if user_key:
                 os.environ["OPENAI_API_KEY"] = user_key
                 st.session_state.api_key = user_key
                 st.success("인증키 저장 완료!")
                 time.sleep(1)
                 st.rerun()
        else:
            # Sync env just in case
            if not os.getenv("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = api_key
                
            # Key exists
            with st.expander("✅ API Key 설정됨"):
                new_key = st.text_input("새로운 Key 입력", type="password", key="reset_api_key_top")
                if st.button("변경 저장"):
                    os.environ["OPENAI_API_KEY"] = new_key
                    st.session_state.api_key = new_key
                    st.rerun()
        
        st.markdown("---")

        # === 1. Custom Navigation ===
        st.markdown(f"### {T('header_title')}")
        
        # Define Pages
        pages = [
            {"page": "Home.py", "label": "menu_home", "icon": "🏠"},
            {"page": "pages/1_🔍_스마트_검색.py", "label": "menu_search", "icon": "🔍"},
            {"page": "pages/2_🛡️_안전_진단.py", "label": "menu_safety", "icon": "🛡️"},
            {"page": "pages/3_📝_협상_도우미.py", "label": "menu_neg", "icon": "📝"},
            {"page": "pages/4_⚖️_법률_상담.py", "label": "menu_legal", "icon": "⚖️"},
            {"page": "pages/5_💰_금융_계산기.py", "label": "btn_calc", "icon": "💰"},
            {"page": "pages/6_📡_모니터링.py", "label": "menu_monitor", "icon": "📡"},
        ]
        
        for p in pages:
            st.page_link(
                p["page"], 
                label=T(p["label"]), 
                icon=p["icon"] if p.get("icon") else None,
                use_container_width=True
            )
            
        st.markdown("---")
        


        # === 3. Language & Profile ===
        st.markdown(f"**{T('lang_settings')}**")
        
        # Language Selection
        opts = ["KO", "EN"]
        curr_lang = st.session_state.get("language", "KO")
        idx = 0 if curr_lang == "KO" else 1
        
        lang_choice = st.radio(
            "Language",
            opts,
            index=idx,
            format_func=lambda x: T("sidebar_option_ko") if x == "KO" else T("sidebar_option_en"),
            label_visibility="collapsed",
            key="lang_radio_widget"
        )
        
        if curr_lang != lang_choice:
            st.session_state.language = lang_choice
            st.rerun()
        
        st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)
        
        # Profile Section
        if "user_name" not in st.session_state:
            st.session_state.user_name = "김서강" if st.session_state.language == "KO" else "Seogang Kim"
        if "user_status" not in st.session_state:
            st.session_state.user_status = "대학생" if st.session_state.language == "KO" else "Student"
        if "user_assets" not in st.session_state:
            st.session_state.user_assets = 2000

        with st.expander(T("user_profile"), expanded=True):
            st.caption(f"{T('label_name')} & {T('label_status')}")
            new_name = st.text_input(T("label_name_input"), st.session_state.user_name, label_visibility="collapsed")
            
            # Status options need to match current language or be mapped
            status_opts = STRINGS[st.session_state.language]["status_options"]
            try:
                curr_status_idx = status_opts.index(st.session_state.user_status)
            except:
                curr_status_idx = 0
                
            new_status = st.selectbox(T("label_status_input"), status_opts, 
                                      index=curr_status_idx, label_visibility="collapsed")
            
            st.caption(T("label_assets"))
            new_assets = st.number_input(T("label_assets_input"), value=st.session_state.user_assets, step=100, label_visibility="collapsed")
            
            if st.button(T("btn_save"), key="save_profile", use_container_width=True):
                st.session_state.user_name = new_name
                st.session_state.user_status = new_status
                st.session_state.user_assets = new_assets
                st.success(T("msg_updated"))
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #888; font-size: 0.8rem;">
            🏠 <strong>Young & Home</strong><br>
            2026 Seogang Univ. AI Winter Camp<br>
            <br>
            {T('footer_made_by')}
        </div>
        """, unsafe_allow_html=True)

@st.cache_data
def load_housing_data():
    try:
        path = "data/housing/houses.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

@st.cache_data
def load_benefits_data():
    try:
        path = "data/welfare/benefits.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

# ==========================================
# UI Component Wrappers (Safe Refactoring)
# ==========================================

def spacer(height="20px"):
    """Inserts a vertical spacer."""
    st.markdown(f"<div style='margin-bottom: {height};'></div>", unsafe_allow_html=True)

def card(content, style="", height=None, use_markdown=True):
    """Wraps content in a manus-card div."""
    h_style = f"height:{height};" if height else ""
    full_style = f"{h_style} {style}".strip()
    html = f'<div class="manus-card" style="{full_style}">{content}</div>'
    if use_markdown:
        st.markdown(html, unsafe_allow_html=True)
    return html

def badge_html(text, accent=False):
    """Returns HTML for a single badge."""
    cls = "manus-chip chip-accent" if accent else "manus-chip"
    return f'<span class="{cls}">{text}</span>'

def divider(margin="20px 0"):
    """Inserts a custom divider."""
    st.markdown(f"<hr style='margin: {margin};'>", unsafe_allow_html=True)
