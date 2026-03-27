
import streamlit as st
import os
from src.utils.ui import setup_page, draw_sidebar, T, divider

setup_page("Legal Help")
draw_sidebar()

st.markdown(f"## {T('menu_legal')}")
st.markdown("<p>AI Legal Advisor based on Housing Lease Protection Act</p>", unsafe_allow_html=True)

if "legal_messages" not in st.session_state:
    st.session_state.legal_messages = [
        {"role": "assistant", "content": "안녕하세요. 주택임대차보호법 관련 궁금한 점을 물어보세요." if st.session_state.language=="KO" else "Hello. Ask me anything about the Housing Lease Protection Act."}
    ]

# Chat container styling


# FAQ buttons
st.caption("💡 자주 묻는 질문" if st.session_state.language=="KO" else "💡 FAQ")

faq_row1_c1, faq_row1_c2, faq_row1_c3 = st.columns(3)
with faq_row1_c1:
    if st.button("🏠 보증금 돌려받기", use_container_width=True, key="faq1"):
        st.session_state.legal_prompt = "계약 만료 후 보증금을 못 받고 있어요. 어떻게 해야 하나요?"
with faq_row1_c2:
    if st.button("📈 월세 인상 한도", use_container_width=True, key="faq2"):
        st.session_state.legal_prompt = "집주인이 월세를 10% 올려달라고 하는데 법적으로 가능한가요?"
with faq_row1_c3:
    if st.button("🔧 수리비 부담", use_container_width=True, key="faq3"):
        st.session_state.legal_prompt = "보일러가 고장 났는데 수리비는 누가 내야 하나요?"

faq_row2_c1, faq_row2_c2, faq_row2_c3 = st.columns(3)
with faq_row2_c1:
    if st.button("📋 전입신고 방법", use_container_width=True, key="faq4"):
        st.session_state.legal_prompt = "전입신고를 어떻게 하나요? 확정일자는 뭐고 왜 받아야 하나요? 안 받으면 어떻게 되나요?"
with faq_row2_c2:
    if st.button("🛡️ 보증보험 가입", use_container_width=True, key="faq5"):
        st.session_state.legal_prompt = "전세보증보험(HUG)이 뭔가요? 가입 조건과 방법, 비용을 알려주세요. 집주인 동의가 필요한가요?"
with faq_row2_c3:
    if st.button("⚠️ 깡통전세 대처", use_container_width=True, key="faq6"):
        st.session_state.legal_prompt = "깡통전세란 뭔가요? 이미 계약한 집이 깡통전세인 것 같은데 어떻게 해야 하나요? 법적으로 보호받을 수 있는 방법은?"

divider("16px 0")

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
        
        # Check API Key first
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            message_placeholder.warning("⚠️ OpenAI API Key가 필요합니다. 왼쪽 사이드바에서 키를 입력해주세요." if st.session_state.language=="KO" else "⚠️ OpenAI API Key missing. Please enter it in the sidebar.")
        else:
            message_placeholder.markdown("Searching Legal Database..." if st.session_state.language=="EN" else "법령 데이터 검색 중...")
            try:
                from src.agents.legal import LegalAdvisorAgent
                # 세션에 에이전트 캐시 (법령/판례 파일 재로드 방지)
                if "legal_agent" not in st.session_state or st.session_state.get("_legal_api_key") != api_key:
                    st.session_state.legal_agent = LegalAdvisorAgent(openai_api_key=api_key)
                    st.session_state._legal_api_key = api_key
                agent = st.session_state.legal_agent
                response = agent.consult(prompt, language=st.session_state.language)
                
                message_placeholder.markdown(response)
                st.session_state.legal_messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")
