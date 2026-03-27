
import streamlit as st
import time
import os
import html
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
        location = st.text_input(T("label_loc"), placeholder=T("ph_loc"),
                                 value=st.session_state.get("user_location", ""))
        max_time = st.slider(T("label_maxtime"), 10, 60, 30)
    with col2:
        budget = st.number_input(T("label_budget"), min_value=0,
                                 value=st.session_state.get("user_max_deposit", 2000))
        monthly = st.number_input(T("label_monthly"), min_value=0,
                                  value=st.session_state.get("user_max_monthly", 50))

    spacer("20px")
    st.markdown(f"**{T('search_user_info')}**")

    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input(T("label_age"), min_value=19, max_value=60,
                              value=st.session_state.get("user_age", 25))
    with c2:
        # Status: internal keys are always Korean, display labels follow language
        STATUS_KEYS = ["대학생", "직장인", "취업준비생", "창업자"]
        status_labels = T("status_options")
        status_idx = st.selectbox(T("label_status"), range(len(STATUS_KEYS)),
                                  format_func=lambda i: status_labels[i])
        status = STATUS_KEYS[status_idx]
    with c3:
        income = st.number_input("연소득 (만원)" if st.session_state.language == "KO" else "Annual Income (10k KRW)",
                                 min_value=0, value=st.session_state.get("user_income", 0), step=100)

    spacer("20px")

    st.markdown(f"**{T('search_benefit')}**")
    bc1, bc2, bc3 = st.columns(3)
    with bc1: want_public = st.checkbox(T("check_public"), value=True)
    with bc2: want_loan = st.checkbox(T("check_loan"), value=True)
    with bc3: want_support = st.checkbox(T("check_support"))

    spacer("20px")
    submitted = st.form_submit_button(T("btn_run_agent"))

# Agent 호출 (form 밖)
if submitted:
    with st.spinner(T("progress_rag")):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("🔑 OpenAI API Key Missing! Please check the sidebar.")
        else:
            try:
                from src.agents.recommender import RecommenderAgent
                agent = RecommenderAgent(openai_api_key=api_key)

                user_profile = {
                    "age": age,
                    "status": status,
                    "income": income,
                    "assets": budget,
                    "location_preference": location or "신촌",
                    "max_commute": max_time,
                    "max_rent": monthly,
                    "employment_type": st.session_state.get("user_job_type", "unemployed"),
                    "marital_status": st.session_state.get("user_married", "single"),
                }

                query = f"{location or '신촌'} 근처에서 월세 {monthly}만원 이하로 집을 구하고 싶어요. 나이는 {age}세, {status}입니다."
                result = agent.run(query, language=st.session_state.language, user_profile=user_profile)

                st.session_state.search_result = result
                st.session_state.search_performed = True

            except Exception as e:
                st.error("😔 추천을 생성하지 못했어요" if st.session_state.language == "KO" else "😔 Failed to generate recommendations")
                with st.expander("🔧 오류 상세" if st.session_state.language == "KO" else "🔧 Error Details"):
                    st.code(str(e))

# --- Display Results (OUTSIDE form) ---
if st.session_state.get("search_performed") and "search_result" in st.session_state:
    result = st.session_state.search_result

    # 1. Structured Data Rendering (New UI)
    if isinstance(result, dict):
        # (1) Benefits Section
        benefits = result.get("benefits", [])
        st.markdown(f"### 💰 {T('search_benefit')} ({len(benefits)})")
        
        for b in benefits:
            is_base = b.get("is_base", False)
            
            # Style Config
            if is_base:
                badge_bg, badge_text = "#E0F2FE", "#0369A1" # Blue (Stabilized)
                badge_label = "청년필수"
                border_style = "border-left: 4px solid #0EA5E9;"
            else:
                badge_bg, badge_text = "#FEF3C7", "#D97706" # Amber (New/Dynamic)
                badge_label = "AI 추천"
                border_style = "" # Standard
            
            clean_name = b['name'].replace('[기본]', '').replace('[추천]', '').strip()
            
            content = f"""<div style="display:flex; justify-content:space-between; align-items:center;">
<div style="display:flex; align-items:center; gap:8px;">
<span style="background:{badge_bg}; color:{badge_text}; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:800;">{badge_label}</span>
<span style="font-size:16px; font-weight:700; color:#1E293B;">{clean_name}</span>
</div>
<div style="font-size:17px; font-weight:800; color:#2563EB;">{b['amount']}</div>
</div>
<div style="margin-top:8px; display:flex; gap:12px; font-size:13px; color:#64748B;">
<span>🏛️ {b.get('provider', '-')}</span>
<span>📑 {b.get('category', '지원금')}</span>
</div>"""
            card(content, style=border_style)
        
        spacer("20px")

        # (2) Recommendations Section
        recs = result.get("recommendations", [])
        if recs:
            st.markdown(f"### 🏡 {T('result_analyzed')} ({len(recs)})")
            for r in recs:
                risk_color = "#22C55E" if r.get('risk_level') == "안전" else "#F59E0B"
                if r.get('risk_level') == "고위험": risk_color = "#EF4444"
                
                badg_html = ""
                if r.get('_badge'):
                    badg_html = f"<span style='background:#DBEAFE; color:#1E40AF; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:5px; font-weight:bold;'>{r['_badge']}</span>"
                
                rec_content = f"""<div style="display:flex; justify-content:space-between;">
<div>
<div style="font-weight:bold; font-size:16px; margin-bottom:4px;">{badg_html}{r['name']} <span style="font-size:12px; font-weight:normal; color:#888;">({r['type']})</span></div>
<div style="font-size:13px; color:#475569;">📍 {r['location']} <span style="color:#CBD5E1;">|</span> 🚶 통근 {r.get('commute_time','?')}분</div>
<div style="font-size:12px; color:#059669; margin-top:2px;">💡 <b>{r.get('best_loan', '맞춤 대출 분석중')}</b> 추천</div>
</div>
<div style="text-align:right;">
<div style="font-weight:800; font-size:16px; color:#1E293B;">{r['deposit']}/{r['monthly']}</div>
<div style="font-size:12px; color:#64748B;">(실질 {r.get('real_monthly_cost', r['monthly'])}만)</div>
<div style="font-size:12px; font-weight:bold; color:{risk_color}; margin-top:4px;">🛡️ {r['risk_level']}</div>
</div>
</div>"""
                card(rec_content)
                
    # 2. Fallback (Text Mode)
    else:
        st.markdown(result)


    # --- Area Intelligence ---
    st.markdown("### 📍 지역 분석" if st.session_state.language == "KO" else "### 📍 Area Intelligence")
    try:
        import json as _json
        with open("data/housing/regions_guide.json", "r", encoding="utf-8") as _f:
            regions_data = _json.load(_f)

        # 1) 검색 지역의 구 매칭
        search_loc = location or "마포"
        matched_district = None
        seoul_data = regions_data.get("서울", {})
        for district_name, info in seoul_data.items():
            if district_name.replace("구", "") in search_loc or search_loc in district_name:
                matched_district = (district_name, info)
                break

        if matched_district:
            name, info = matched_district
            safety_stars = "⭐" * info["safety_score"] + "☆" * (5 - info["safety_score"])
            area_content = f"""
<h3 style="margin:0 0 12px 0; color:#1E293B;">📍 {name} 가이드</h3>
<p style="color:#475569; margin-bottom:12px;">{info['vibe']}</p>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
<div style="background:#F0F9FF; padding:10px; border-radius:8px;">
<span style="font-size:12px; color:#64748B;">평균 보증금</span><br><b style="color:#0369A1;">{info['avg_deposit']:,}만</b>
</div>
<div style="background:#F0FDF4; padding:10px; border-radius:8px;">
<span style="font-size:12px; color:#64748B;">평균 월세</span><br><b style="color:#166534;">{info['avg_monthly']}만</b>
</div>
</div>
<div style="font-size:13px; color:#334155; line-height:1.8;">
🚇 <b>교통:</b> {info['transport']}<br>
👍 <b>장점:</b> {', '.join(info['pros'])}<br>
👎 <b>단점:</b> {', '.join(info['cons'])}<br>
🎯 <b>추천 대상:</b> {', '.join(info['good_for'])}<br>
🛡️ <b>안전:</b> {safety_stars}<br>
💡 <b>팁:</b> {info['tips']}
</div>"""
            card(area_content)

            # 지역 후기
            try:
                from src.utils.reviews import get_reviews, get_avg_rating, add_review
                stats = get_avg_rating(name)
                if stats["count"] > 0:
                    review_stars = "⭐" * round(stats["avg"]) + "☆" * (5 - round(stats["avg"]))
                    st.caption(f"🗣️ 주민 후기: {review_stars} ({stats['avg']}/5, {stats['count']}건)")
                reviews = get_reviews(name, limit=5)
                if reviews:
                    for rv in reviews:
                        rv_stars = "⭐" * rv["rating"]
                        safe_comment = html.escape(rv.get("comment", ""))
                        safe_status = html.escape(rv.get("status", ""))
                        st.markdown(f"<div style='font-size:13px; color:#334155; padding:4px 0;'>{rv_stars} {safe_comment} <span style='color:#94A3B8; font-size:11px;'>— {safe_status} {rv['date'][:10]}</span></div>", unsafe_allow_html=True)

                with st.expander("✍️ 이 동네 후기 남기기"):
                    rv_rating = st.slider("평점", 1, 5, 4, key="rv_rating")
                    rv_comment = st.text_input("한줄평", placeholder="예: 교통 좋고 밥집 많아요", key="rv_comment")
                    if st.button("후기 등록", key="rv_submit"):
                        if rv_comment:
                            add_review(name, rv_rating, rv_comment, st.session_state.get("user_status", ""))
                            st.success("후기가 등록되었습니다!")
                            st.rerun()
            except Exception:
                pass
        else:
            st.info("해당 지역의 상세 가이드가 준비 중입니다.")

        # 2) 예산 기반 추천 지역
        budget_recs = regions_data.get("budget_recommendations", {})
        user_monthly = monthly if monthly else 50
        if user_monthly <= 30:
            budget_key = "under_30"
        elif user_monthly <= 50:
            budget_key = "30_to_50"
        elif user_monthly <= 70:
            budget_key = "50_to_70"
        else:
            budget_key = "over_70"

        rec = budget_recs.get(budget_key, {})
        if rec:
            districts_str = " · ".join(rec.get("districts", []))
            budget_content = f"""
<div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
<span style="background:#EEF2FF; color:#4F46E5; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:700;">💰 {rec['label']}</span>
<span style="font-size:14px; font-weight:600; color:#1E293B;">예산 맞춤 추천 지역</span>
</div>
<div style="font-size:14px; color:#1E293B; font-weight:600; margin-bottom:6px;">{districts_str}</div>
<div style="font-size:13px; color:#475569;">{rec['tip']}</div>
<div style="font-size:12px; color:#64748B; margin-top:6px;">주거 유형: {', '.join(rec.get('housing_types', []))}</div>"""
            card(budget_content, style="border-left: 4px solid #6366F1;")

    except Exception:
        pass

    spacer("20px")

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
