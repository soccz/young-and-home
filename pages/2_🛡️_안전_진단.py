
import streamlit as st
import time
import os
import tempfile
from src.utils.ui import setup_page, draw_sidebar, T, card, spacer

setup_page("Safety Scan")
draw_sidebar()

st.markdown(f"## {T('safety_title')}")
st.markdown(f"<p>{T('safety_desc')}</p>", unsafe_allow_html=True)

tab_analysis, tab_selfcheck, tab_sos = st.tabs([
    "🛡️ 등기부 분석 (AI)",
    "🧮 깡통전세 자가진단",
    "🚨 SOS 비상 대응"
])

# ============================================
# TAB 1: 등기부 분석 (기존 기능)
# ============================================
with tab_analysis:
    upload_card_content = f"""<h3 class="no-margin-top">{T('upload_card_title')}</h3>
<p>{T('upload_card_desc')}</p>
<div class="box-blue" style="margin-top:10px;">
<small>💡 <b>Tip:</b> 계약서도 함께 올리면 <b>"집주인 일치 여부"</b>까지 꼼꼼하게 봐드려요!</small>
</div>"""
    card(upload_card_content)

    sample_labels = T("sample_options")
    sample_idx = st.selectbox(T("sample_select"), range(len(sample_labels)),
                              format_func=lambda i: sample_labels[i])
    SAMPLE_TYPE_MAP = {0: "upload", 1: "safe", 2: "risky", 3: "moderate"}
    sample_type = SAMPLE_TYPE_MAP.get(sample_idx, "upload")

    uploaded_registry = None
    uploaded_contract = None

    if sample_type == "upload":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. 등기부등본 (필수)**")
            uploaded_registry = st.file_uploader("Registry PDF", type=["pdf", "png", "jpg"], key="reg_up", label_visibility="collapsed")
        with col2:
            st.markdown("**2. 임대차계약서 (선택)**")
            uploaded_contract = st.file_uploader("Contract PDF", type=["pdf", "png", "jpg"], key="con_up", label_visibility="collapsed")

    deposit = st.number_input(T("label_deposit"), min_value=0, value=20000, key="analysis_deposit")
    can_analyze = (sample_type != "upload") or (uploaded_registry is not None)

    if st.button(T("btn_safety_start"), disabled=not can_analyze):
        progress_bar = st.progress(0)
        with st.status(T("status_extract"), expanded=True) as status:
            st.write("🔍 문서 데이터 추출 중...")
            progress_bar.progress(25); time.sleep(0.5)
            st.write("🕵️ 권리 분석 (근저당, 압류)...")
            progress_bar.progress(50); time.sleep(0.5)
            st.write("⚔️ 교차 검증 (계약서 vs 등기부)...")
            progress_bar.progress(75); time.sleep(0.5)
            st.write("✅ 최종 리포트 생성 완료!")
            progress_bar.progress(100)
            status.update(label="Analysis Complete", state="complete", expanded=False)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("⚠️ OpenAI API Key를 사이드바에서 입력해주세요.")
        else:
            reg_path = con_path = None
            try:
                from src.agents.analyzer import SafetyAnalyzerAgent
                agent = SafetyAnalyzerAgent(openai_api_key=api_key)
                if uploaded_registry:
                    suffix = os.path.splitext(uploaded_registry.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_registry.getbuffer()); reg_path = tmp.name
                if uploaded_contract:
                    suffix = os.path.splitext(uploaded_contract.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_contract.getbuffer()); con_path = tmp.name

                result = agent.run(
                    document_path=reg_path, contract_path=con_path,
                    sample_type={"safe": "safe", "risky": "risky", "moderate": "moderate", "upload": "moderate"}.get(sample_type, "safe"),
                    deposit=deposit * 10000, language=st.session_state.language
                )

                if reg_path and os.path.exists(reg_path): os.remove(reg_path)
                if con_path and os.path.exists(con_path): os.remove(con_path)

                st.markdown(f"### {T('result_analyzed')}")
                st.markdown(result)

                # === SOS 연결 (위험 감지 시) ===
                if "위험" in result or "고위험" in result or "불일치" in result:
                    spacer("10px")
                    st.error("🚨 위험 신호가 감지되었습니다!")
                    sos_content = """<h3 style="margin:0; color:#DC2626;">⚡ 지금 바로 해야 할 것</h3>
<ol style="color:#334155; line-height:2; margin-top:12px;">
<li><b>계약금 입금 절대 금지</b> — 아직 안 보냈다면 절대 보내지 마세요</li>
<li><b>전세보증보험(HUG) 가입 가능 여부 확인</b> — <a href="https://www.khug.or.kr/" target="_blank">HUG 홈페이지</a> 또는 안심전세앱</li>
<li><b>전세사기 피해지원센터 상담</b> — ☎️ <b>1533-8119</b> (무료)</li>
<li><b>대한법률구조공단</b> — ☎️ <b>132</b> (무료 법률 상담)</li>
</ol>"""
                    card(sos_content, style="border: 2px solid #FCA5A5; background: #FEF2F2 !important;")

                    if st.button("📝 내용증명 초안 생성 (협상 도우미로)", use_container_width=True, type="primary"):
                        st.switch_page("pages/3_📝_협상_도우미.py")

            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                # Cleanup temp files even on error
                if reg_path and os.path.exists(reg_path): os.remove(reg_path)
                if con_path and os.path.exists(con_path): os.remove(con_path)

# ============================================
# TAB 2: 깡통전세 자가진단
# ============================================
with tab_selfcheck:
    card("""<h3 style="margin:0;">🧮 깡통전세 자가진단</h3>
<p style="color:#64748B;">등기부등본 없이도 3개 숫자만 입력하면 즉시 위험도를 확인할 수 있어요.</p>""")

    st.markdown("#### 📝 숫자 3개만 입력하세요")

    c1, c2, c3 = st.columns(3)
    with c1:
        sc_deposit = st.number_input("내 보증금 (만원)", min_value=0, value=20000, step=1000, key="sc_dep",
                                     help="내가 집주인에게 주는/준 보증금")
    with c2:
        sc_market = st.number_input("매매 시세 (만원)", min_value=0, value=35000, step=1000, key="sc_market",
                                    help="네이버 부동산/KB시세에서 확인")
    with c3:
        sc_mortgage = st.number_input("근저당 설정액 (만원)", min_value=0, value=0, step=1000, key="sc_mort",
                                      help="등기부등본 을구에서 확인")

    with st.expander("❓ 이 숫자들 어디서 확인하나요?", expanded=False):
        st.markdown("""
- **매매 시세**: [네이버 부동산](https://land.naver.com) → 아파트명 검색 → 실거래가/호가 확인
- **근저당 설정액**: [인터넷등기소](https://www.iros.go.kr) → 열람하기 → 을구 "채권최고액" 합계
- **선순위 임차인**: 등기부등본 을구의 전세권 설정 금액
""")

    sc_prior_lease = st.number_input("선순위 임차인 보증금 (만원, 없으면 0)", min_value=0, value=0, step=1000, key="sc_prior")

    if st.button("⚡ 즉시 진단", use_container_width=True, type="primary", key="sc_run"):
        if sc_market <= 0:
            st.warning("매매 시세를 입력해주세요.")
        else:
            total_debt = sc_mortgage + sc_prior_lease + sc_deposit
            ratio = total_debt / sc_market * 100
            safe_limit = sc_market * 0.7

            # 게이지 시각화
            if ratio <= 60:
                level, color, emoji = "안전", "#22C55E", "✅"
                msg = "채권 비율이 시세의 60% 이하로 안전한 수준입니다."
            elif ratio <= 80:
                level, color, emoji = "주의", "#F59E0B", "⚠️"
                msg = "채권 비율이 높은 편입니다. 전세보증보험 가입을 강력 권장합니다."
            else:
                level, color, emoji = "위험 (깡통전세 의심)", "#EF4444", "🚨"
                msg = "총 채권이 시세를 초과하거나 근접합니다. 경매 시 보증금 회수가 어렵습니다."

            result_content = f"""
<div style="text-align:center; margin-bottom:16px;">
<div style="font-size:48px; font-weight:900; color:{color};">{ratio:.0f}%</div>
<div style="font-size:14px; color:#64748B;">총 채권 / 매매 시세</div>
<div style="background:#E2E8F0; border-radius:99px; height:12px; margin:12px auto; max-width:400px;">
<div style="background:{color}; border-radius:99px; height:12px; width:{min(ratio, 100):.0f}%;"></div>
</div>
<div style="font-size:20px; font-weight:700; color:{color};">{emoji} {level}</div>
</div>"""
            card(result_content)

            # 상세 분석
            detail_content = f"""
<div style="font-size:14px; line-height:2; color:#334155;">
<b>📊 상세 내역</b><br>
• 내 보증금: <b>{sc_deposit:,}만원</b><br>
• 근저당 설정액: <b>{sc_mortgage:,}만원</b><br>
• 선순위 보증금: <b>{sc_prior_lease:,}만원</b><br>
• <b>총 채권: {total_debt:,}만원</b><br>
• 매매 시세: {sc_market:,}만원<br>
• 안전 기준 (시세 70%): {safe_limit:,.0f}만원<br>
<br>
<b>💡 판단:</b> {msg}
</div>"""
            card(detail_content)

            if ratio > 70:
                spacer("10px")
                st.warning("🛡️ 전세보증보험(HUG) 가입을 반드시 검토하세요!")
                st.markdown("- HUG 가입: [안심전세앱](https://www.khug.or.kr/) 또는 주거래 은행")
                st.markdown("- 보증료: 보증금의 약 **0.128%/년** (2억 기준 연 25.6만원)")

            if ratio > 90:
                st.error("🚨 이 조건에서는 계약을 **재고**하시길 강력히 권장합니다.")
                if st.button("🚨 SOS 비상 대응 보기", key="sc_sos"):
                    st.info("'SOS 비상 대응' 탭을 확인하세요 →")

# ============================================
# TAB 3: SOS 비상 대응
# ============================================
with tab_sos:
    card("""<h3 style="margin:0; color:#DC2626;">🚨 SOS 비상 대응 센터</h3>
<p style="color:#64748B;">전세사기가 의심되거나, 보증금을 못 돌려받고 있다면 즉시 행동하세요.</p>""")

    st.markdown("### 📞 긴급 연락처")
    contacts = [
        ("전세사기 피해지원센터", "1533-8119", "무료 상담 + 법률 지원 연결", "#DC2626"),
        ("대한법률구조공단", "132", "무료 법률 상담 (소득 기준 무관)", "#2563EB"),
        ("경찰 사이버수사", "182", "사기 의심 시 즉시 신고", "#7C3AED"),
        ("주택도시보증공사(HUG)", "1566-9009", "전세보증금 반환 보증 관련", "#059669"),
    ]

    for name, phone, desc, color in contacts:
        contact_content = f"""<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="font-weight:700; color:#1E293B;">{name}</div>
<div style="font-size:12px; color:#64748B;">{desc}</div>
</div>
<div style="font-size:24px; font-weight:900; color:{color};">📞 {phone}</div>
</div>"""
        card(contact_content, style="padding:16px 20px;")

    spacer("20px")
    st.markdown("### ⚡ 상황별 즉시 행동 가이드")

    with st.expander("😰 계약 전인데, 이 집이 의심돼요", expanded=False):
        st.markdown("""
1. **계약금 입금 절대 금지** — 한 번 보내면 돌려받기 매우 어려움
2. **등기부등본 직접 발급** — [인터넷등기소](https://www.iros.go.kr)에서 직접 (집주인이 준 것은 신뢰 X)
3. **위 '깡통전세 자가진단' 탭에서 즉시 체크**
4. 근저당 비율 80% 이상이면 → **다른 매물을 찾으세요**
5. 판단이 어려우면 → **1533-8119** 전화 (무료)
""")

    with st.expander("😱 이미 계약했는데, 불안해요", expanded=False):
        st.markdown("""
1. **전입신고 + 확정일자** 받았는지 확인 (안 했으면 오늘 당장!)
   - [정부24](https://www.gov.kr) → 전입신고 → 확정일자 동시 처리
2. **전세보증보험(HUG) 가입** — [안심전세앱](https://www.khug.or.kr/) 또는 은행
   - 가입 조건: 전세금 수도권 7억 이하, 공시가격 126% 이내
3. **등기부등본 정기 확인** — 계약 기간 중 근저당 추가 여부 모니터링
   - 이 앱의 '모니터링' 기능 활용
4. 추가 근저당이 잡히면 → 즉시 **내용증명 발송** (협상 도우미 활용)
""")

    with st.expander("💸 보증금을 못 돌려받고 있어요", expanded=False):
        st.markdown("""
1. **내용증명 발송** (14일 기한 명시)
   - 이 앱의 '협상 도우미'에서 자동 생성 가능
2. **HUG 보증보험 가입자** → HUG에 보증금 반환 청구 (HUG가 대신 지급)
3. **임차권등기명령 신청** (법원) — 이사 나가도 대항력 유지
   - 관할 법원에 직접 또는 대한법률구조공단(132) 도움
4. **지급명령 신청** (간편 소송) — 법원에 서면으로 신청, 변호사 없이 가능
5. **긴급복지 주거지원** 신청 — 주민센터 또는 ☎️ 129
   - 최대 월 64만원 주거비 긴급 지원
""")

    # === 피해 복구 타임라인 ===
    spacer("20px")
    st.markdown("### 📋 피해 복구 로드맵 (체크하며 진행)")
    st.caption("전세사기 인지 시점부터 보증금 회수까지, 순서대로 따라가세요.")

    if "recovery_state" not in st.session_state:
        st.session_state.recovery_state = {}

    recovery_steps = [
        {"step": "1", "title": "경찰 신고", "deadline": "즉시 (24시간 내)", "detail": "가까운 경찰서 방문 또는 ☎️ 182. 사기 혐의 접수. 접수번호 반드시 보관.", "icon": "🚔"},
        {"step": "2", "title": "전입신고 + 확정일자 확인", "deadline": "즉시", "detail": "정부24에서 확인. 안 했으면 지금 당장. 대항력의 기본.", "icon": "📋"},
        {"step": "3", "title": "내용증명 발송", "deadline": "3일 내", "detail": "집주인에게 보증금 반환 요구. 14일 기한 명시. 아래 버튼으로 자동 생성 가능.", "icon": "📮"},
        {"step": "4", "title": "임차권등기명령 신청", "deadline": "이사 전 필수", "detail": "관할 법원에 신청. 이사 나가도 대항력 유지. 비용 약 3만원.", "icon": "⚖️"},
        {"step": "5", "title": "HUG 보증금 반환 청구", "deadline": "보증보험 가입자", "detail": "HUG가 보증금 대신 지급 후 집주인에게 구상. ☎️ 1566-9009", "icon": "🛡️"},
        {"step": "6", "title": "지급명령 신청", "deadline": "14일 경과 후", "detail": "법원에 서면 신청. 변호사 없이 가능. 비용 약 5만원. 법률구조공단(132) 도움.", "icon": "📄"},
        {"step": "7", "title": "긴급복지 주거지원 신청", "deadline": "주거 불안정 시", "detail": "주민센터 또는 ☎️ 129. 최대 월 64만원 주거비 지원.", "icon": "🏠"},
    ]

    completed_count = 0
    for rs in recovery_steps:
        key = f"recovery_{rs['step']}"
        is_done = st.session_state.recovery_state.get(key, False)
        if is_done:
            completed_count += 1

        col_check, col_content = st.columns([0.05, 0.95])
        with col_check:
            checked = st.checkbox("x", key=key, value=is_done, label_visibility="collapsed")
            st.session_state.recovery_state[key] = checked
        with col_content:
            done_style = "opacity:0.5; text-decoration:line-through;" if checked else ""
            st.markdown(f"""<div style="{done_style}">
<span style="font-size:16px;">{rs['icon']}</span>
<b>Step {rs['step']}. {rs['title']}</b>
<span style="color:#DC2626; font-size:12px; font-weight:600;"> ({rs['deadline']})</span><br>
<span style="font-size:13px; color:#475569;">{rs['detail']}</span>
</div>""", unsafe_allow_html=True)

    pct = int(completed_count / len(recovery_steps) * 100)
    st.progress(pct / 100)
    st.caption(f"복구 진행률: {completed_count}/{len(recovery_steps)} ({pct}%)")

    spacer("10px")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 내용증명 초안 생성", use_container_width=True, type="primary"):
            st.switch_page("pages/3_📝_협상_도우미.py")
    with c2:
        if st.button("⚖️ 법률 상담 시작", use_container_width=True):
            st.switch_page("pages/4_⚖️_법률_상담.py")
