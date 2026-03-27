
import streamlit as st
import os
import html as _html
from src.utils.ui import setup_page, draw_sidebar, T, card

setup_page("Negotiator")
draw_sidebar()

st.markdown(f"## {T('neg_title')}")
st.markdown(f"<p>{T('neg_desc')}</p>", unsafe_allow_html=True)

TOPIC_KEYS = ["보증보험 가입 요청", "특약 조항 추가", "수리 요청", "계약 조건 변경", "보증금 반환 촉구"]
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OpenAI API Key is missing. Please enter it in the sidebar.")
    else:
        with st.spinner("Generating..."):
            try:
                from src.agents.negotiator import NegotiatorAgent
                agent = NegotiatorAgent(openai_api_key=api_key)

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
                elif issue == "보증금 반환 촉구":
                    message = agent.generate_message(
                        sender_name=sender_name,
                        recipient="임대인" if st.session_state.language=="KO" else "Landlord",
                        negotiation_type="보증금 반환 최고 (내용증명)",
                        situation=analysis_context or "임대차계약 종료 후 보증금 미반환 상태. 주택임대차보호법 제3조의2에 따라 반환을 요구합니다.",
                        desired_outcome="본 최고장 수령일로부터 14일 이내 보증금 전액 반환. 불이행 시 법적 조치(지급명령 신청, 임차권등기명령) 예정."
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
                draft_content = f"""<div style="display:flex; align-items:center; margin-bottom:12px;">
<span class="material-icons" style="color:#6366F1; margin-right:8px;">description</span>
<h3 style="margin:0; color:#1E293B;">Draft Message</h3>
</div>
<p style="color:#334155 !important; font-family: 'Pretendard', sans-serif; white-space: pre-wrap; line-height: 1.8;">{_html.escape(message)}</p>
<div style="margin-top:16px; padding:12px; background:#F8FAFC; border-radius:8px; font-size:12px; color:#64748B;">
💡 <b>Tip:</b> 위 내용을 복사해서 문자나 카카오톡으로 보내세요.
</div>"""
                card(draft_content)

                st.code(message, language=None)

            except Exception as e:
                st.error(f"Error: {str(e)}")
