
import streamlit as st
import os
import requests
from src.utils.ui import setup_page, draw_sidebar, T, card

setup_page("Monitoring")
draw_sidebar()

st.markdown(f"## 🛡️ {T('mon_title')} (Security Center)")

with st.expander("ℹ️ 시스템 구동 원리 (n8n + LangGraph Architecture)", expanded=False):
    st.markdown("""
    **본 시스템은 n8n 워크플로우와 LangGraph Agent가 연동되어 작동합니다.**
    
    ```mermaid
    graph LR
        n8n[n8n Scheduler] --> API[FastAPI Backend]
        API --> Agent[SafetyAnalyzerAgent]
        Agent --> Alert[Slack/카카오톡]
    ```
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



if "monitor_status" not in st.session_state:
    st.session_state.monitor_status = "SAFE"
    st.session_state.monitor_logs = [
        "[n8n] Workflow connected: registry_alert.json", 
        "[API] FastAPI Backend Ready (port 8000)", 
        "[AGENT] SafetyAnalyzerAgent initialized"
    ]

def add_log(msg, alert=False):
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    prefix = "[ALERT]" if alert else "[INFO]"
    st.session_state.monitor_logs.append(f"[{ts}] {prefix} {msg}")
    if len(st.session_state.monitor_logs) > 8:
        st.session_state.monitor_logs.pop(0)

# --- 구독 설정 섹션 ---
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
        with st.spinner("구독 정보를 서버에 등록 중입니다..."):
            try:
                response = requests.post(
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
    
    status_content = f"""
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
    """
    card(status_content, style="text-align:center; padding: 40px;")
    
with c_action:
    st.markdown("### 🛠️ n8n 워크플로우 제어")
    mode = st.radio("System Mode", ["Live (n8n 연동)", "Simulation (Demo)"], label_visibility="collapsed")
    
    if mode == "Live (n8n 연동)":
        st.info("n8n 워크플로우가 12시간마다 자동 실행됩니다.")
        if st.button("🔍 지금 등기 체크 (API 호출)", use_container_width=True, type="primary"):
            try:
                response = requests.post(
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
    else:
        st.error("🚨 위험 감지! 즉시 대응 프로토콜 가동")
        st.markdown("""
        1. **[n8n]** 알림 워크플로우 트리거됨
        2. **[Agent]** NegotiatorAgent 경고 메시지 생성
        3. **[권고]** 법률 상담 연결 👇
        """)
        if st.button("⚖️ 법률 대응 센터 연결", type="primary"):
            st.switch_page("pages/4_⚖️_법률_상담.py")
