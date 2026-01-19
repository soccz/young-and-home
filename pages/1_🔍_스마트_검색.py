
import streamlit as st
import time
import os
import pandas as pd
from src.utils.ui import setup_page, draw_sidebar, T, load_housing_data, card, spacer

setup_page("Smart Search")
draw_sidebar()

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
    
    spacer("20px")
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
    
    spacer("20px")
    
    st.markdown(f"**{T('search_benefit')}**")
    bc1, bc2, bc3 = st.columns(3)
    with bc1: st.checkbox(T("check_public"), value=True)
    with bc2: st.checkbox(T("check_loan"), value=True)
    with bc3: st.checkbox(T("check_support"))

    spacer("20px")
    submitted = st.form_submit_button(T("btn_run_agent"))
    
    if submitted:
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            progress_content = f"""
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#3C8CE7;">{T('progress_rag')}</span>
                <span>45%</span>
            </div>
            """
            card(progress_content)
            time.sleep(0.5)
        
        progress_placeholder.empty()
        
        # 실제 Agent 호출
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
             st.error("🔑 OpenAI API Key Missing! Please check the sidebar.")
        else:
            try:
                from src.agents.recommender import RecommenderAgent
                agent = RecommenderAgent(openai_api_key=api_key)
            
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
                
                # Save to session state
                st.session_state.search_result = result
                st.session_state.search_performed = True
                
            except Exception as e:
                st.error("😔 추천을 생성하지 못했어요" if st.session_state.language == "KO" else "😔 Failed to generate recommendations")
                st.info("API 키를 확인하거나 잠시 후 다시 시도해주세요!" if st.session_state.language == "KO" else "Check API key or try again later!")
                with st.expander("🔧 오류 상세" if st.session_state.language == "KO" else "🔧 Error Details"):
                    st.code(str(e))

    # --- Display Results ---
    if st.session_state.get("search_performed"):
        st.markdown(f"### {T('result_analyzed')}")
        if "search_result" in st.session_state:
            st.markdown(st.session_state.search_result)

        # --- Map View ---
        st.markdown(f"### {T('map_view')}")
        try:
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
