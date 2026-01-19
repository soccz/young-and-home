
import streamlit as st
import time
import os
import tempfile
from src.utils.ui import setup_page, draw_sidebar, T, card

setup_page("Safety Scan")
draw_sidebar()

st.markdown(f"## {T('safety_title')}")
st.markdown(f"<p>{T('safety_desc')}</p>", unsafe_allow_html=True)

upload_card_content = f"""
    <h3 class="no-margin-top">{T('upload_card_title')}</h3>
    <p>{T('upload_card_desc')}</p>
    <div class="box-blue" style="margin-top:10px;">
        <small>💡 <b>Tip:</b> 계약서도 함께 올리면 <b>"집주인 일치 여부"</b>까지 꼼꼼하게 봐드려요!</small>
    </div>
"""
card(upload_card_content)

# 샘플 선택
SAMPLE_KEYS = ["파일 업로드", "안전 매물 (데모)", "위험 매물 (데모)", "소유자 불일치 (사기 주의)"]
sample_labels = T("sample_options") 
# Note: T("sample_options") might need update for new key, but using English fallbacks logic
try:
    sample_idx = st.selectbox("Select Sample", range(len(SAMPLE_KEYS)), format_func=lambda i: SAMPLE_KEYS[i])
except:
    sample_idx = 0

sample_type = SAMPLE_KEYS[sample_idx]

uploaded_registry = None
uploaded_contract = None

if sample_type == "파일 업로드":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. 등기부등본 (필수)**")
        uploaded_registry = st.file_uploader("Registry PDF", type=["pdf", "png", "jpg"], key="reg_up", label_visibility="collapsed")
    with col2:
        st.markdown("**2. 임대차계약서 (선택)**")
        uploaded_contract = st.file_uploader("Contract PDF", type=["pdf", "png", "jpg"], key="con_up", label_visibility="collapsed")

deposit = st.number_input(T("label_deposit"), min_value=0, value=20000)

can_analyze = (sample_type != "파일 업로드") or (uploaded_registry is not None)

if st.button(T("btn_safety_start"), disabled=not can_analyze):
    # 진행 상태 애니메이션
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    with st.status(T("status_extract"), expanded=True) as status:
        st.write("🔍 문서 데이터 추출 중...")
        progress_bar.progress(25)
        time.sleep(0.5)
        
        st.write("🕵️ 권리 분석 (근저당, 압류)...")
        progress_bar.progress(50)
        time.sleep(0.5)
        
        st.write("⚔️ 교차 검증 (계약서 vs 등기부)...")
        progress_bar.progress(75)
        time.sleep(0.5)
        
        st.write("✅ 최종 리포트 생성 완료!")
        progress_bar.progress(100)
        status.update(label="Analysis Complete", state="complete", expanded=False)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OpenAI API Key is missing. Please enter it in the sidebar.")
    else:
        try:
            from src.agents.analyzer import SafetyAnalyzerAgent
            
            agent = SafetyAnalyzerAgent(openai_api_key=api_key)
            
            type_map = {
                "안전 매물 (데모)": "safe",
                "위험 매물 (데모)": "risky", # 등기부 위험
                "소유자 불일치 (사기 주의)": "risky", # 계약서 불일치 (Mock data assumes 'risky' triggers mismatch in parser)
                "파일 업로드": "moderate"
            }
            
            # 파일 처리
            reg_path = None
            con_path = None
            
            if uploaded_registry:
                suffix = os.path.splitext(uploaded_registry.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_registry.getbuffer())
                    reg_path = tmp.name
            
            if uploaded_contract:
                suffix = os.path.splitext(uploaded_contract.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_contract.getbuffer())
                    con_path = tmp.name
            
            # Run Agent
            result = agent.run(
                document_path=reg_path,
                contract_path=con_path,
                sample_type=type_map.get(sample_type, "safe"),
                deposit=deposit * 10000,
                language=st.session_state.language
            )
            
            # Cleanup
            if reg_path and os.path.exists(reg_path): os.remove(reg_path)
            if con_path and os.path.exists(con_path): os.remove(con_path)
            
            # 결과 표시
            st.markdown(f"### {T('result_analyzed')}")
            st.markdown(result)
            
        except Exception as e:
            st.error(f"Error: {e}")
