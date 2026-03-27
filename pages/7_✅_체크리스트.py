
import streamlit as st
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.utils.ui import setup_page, draw_sidebar, T, card, spacer, load_checklists_data

setup_page("Checklist")
draw_sidebar()

st.markdown("## ✅ 처음 집 구할 때 필수 체크리스트" if st.session_state.language == "KO" else "## ✅ First-Time Housing Checklist")
st.markdown("<p>집 보기 → 계약 → 입주까지, 놓치면 안 되는 것들을 한 곳에 모았습니다.</p>" if st.session_state.language == "KO" else "<p>Everything you need from viewing to moving in.</p>", unsafe_allow_html=True)

checklists = load_checklists_data()
if not checklists:
    st.error("체크리스트 데이터를 불러올 수 없습니다.")
    st.stop()

# Initialize checked state
if "checklist_state" not in st.session_state:
    st.session_state.checklist_state = {}

# Tabs for each phase
tab_viewing, tab_contract, tab_movein = st.tabs([
    f"🔍 {checklists['viewing']['title']}",
    f"✍️ {checklists['contract']['title']}",
    f"🏠 {checklists['movein']['title']}"
])

def render_checklist(tab, phase_key, phase_data):
    with tab:
        st.caption(phase_data["desc"])
        spacer("10px")

        total_items = 0
        checked_items = 0

        for cat in phase_data["categories"]:
            st.markdown(f"#### {cat['name']}")

            for item in cat["items"]:
                total_items += 1
                check_key = f"{phase_key}_{cat['name']}_{item['check'][:20]}"

                col1, col2 = st.columns([0.05, 0.95])
                with col1:
                    is_checked = st.checkbox(
                        "check",
                        key=check_key,
                        value=st.session_state.checklist_state.get(check_key, False),
                        label_visibility="collapsed"
                    )
                    st.session_state.checklist_state[check_key] = is_checked
                    if is_checked:
                        checked_items += 1

                with col2:
                    text_style = "text-decoration:line-through; color:#94A3B8;" if is_checked else "color:#1E293B;"
                    st.markdown(
                        f"<div style='{text_style} font-size:14px; font-weight:500;'>{item['check']}</div>"
                        f"<div style='font-size:12px; color:#64748B; margin-bottom:8px;'>💡 {item['why']}</div>",
                        unsafe_allow_html=True
                    )

            spacer("8px")

        # Progress
        pct = int(checked_items / total_items * 100) if total_items > 0 else 0
        color = "#22C55E" if pct == 100 else "#F59E0B" if pct > 50 else "#6366F1"

        progress_content = f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:14px; font-weight:600; color:#1E293B;">진행률</span>
<span style="font-size:20px; font-weight:800; color:{color};">{pct}%</span>
</div>
<div style="background:#E2E8F0; border-radius:99px; height:8px; margin-top:8px;">
<div style="background:{color}; border-radius:99px; height:8px; width:{pct}%;"></div>
</div>
<div style="font-size:12px; color:#64748B; margin-top:4px;">{checked_items}/{total_items} 항목 완료</div>"""
        card(progress_content)

render_checklist(tab_viewing, "viewing", checklists["viewing"])
render_checklist(tab_contract, "contract", checklists["contract"])
render_checklist(tab_movein, "movein", checklists["movein"])

# Reset button
spacer("20px")
if st.button("🔄 체크리스트 초기화", use_container_width=True):
    st.session_state.checklist_state = {}
    st.rerun()

# === 방문 전 질문 생성기 ===
spacer("20px")
st.markdown("### 🗣️ 집주인/중개사에게 물어볼 질문")
st.caption("매물 정보를 입력하면 꼭 물어봐야 할 질문을 자동으로 만들어드려요.")

with st.expander("질문 생성하기", expanded=False):
    q_deposit = st.number_input("보증금 (만원)", min_value=0, value=st.session_state.get("user_max_deposit", 2000), step=1000, key="q_dep")
    q_type = st.selectbox("주거 유형", ["전세", "월세", "반전세"], key="q_type")

    if st.button("💡 맞춤 질문 생성", use_container_width=True, key="q_gen"):
        questions = [
            f"1. 등기부등본상 근저당이 있나요? 있다면 채권최고액이 얼마인가요?",
            f"2. 전세보증보험(HUG) 가입에 동의하시나요?",
            f"3. 잔금일에 전입신고와 확정일자를 바로 받을 수 있나요?",
            f"4. 관리비가 얼마이고, 포함 항목은 무엇인가요? (수도/전기/가스/인터넷)",
            f"5. 계약 기간 중 근저당 추가 설정이나 소유권 이전 계획이 있나요?",
        ]
        if q_type == "전세":
            questions.append(f"6. 보증금 {q_deposit:,}만원 전액 반환에 문제가 없으시겠죠? 계약서에 반환 기한을 명시해도 될까요?")
            questions.append("7. 이 건물의 다른 세입자가 있나요? 있다면 총 보증금 합계가 시세 대비 어느 정도인가요?")
        elif q_type == "월세":
            questions.append("6. 월세 연체 시 위약금 기준이 어떻게 되나요?")
            questions.append("7. 계약 중도 해지 시 조건이 어떻게 되나요?")
        questions.append("8. 입주 전 수리/정비가 필요한 곳이 있나요? 시설물 현황표를 작성해도 될까요?")

        for q in questions:
            st.markdown(f"- {q}")

        st.caption("💡 이 질문들을 스크린샷 찍어서 방문 시 참고하세요!")
