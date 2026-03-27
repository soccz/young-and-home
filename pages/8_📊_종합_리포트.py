
import streamlit as st
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.utils.ui import setup_page, draw_sidebar, T, card, spacer, load_housing_data, load_regions_data

setup_page("Report")
draw_sidebar()

st.markdown("## 📊 원클릭 종합 리포트")
st.caption("매물 하나를 선택하면 안전 진단 + 대출 시뮬레이션 + 생활비 분석을 한 번에 보여드립니다.")

houses = load_housing_data()
regions = load_regions_data()

if not houses:
    st.warning("매물 데이터를 불러올 수 없습니다.")
    st.stop()

# === Step 1: 매물 선택 ===
safe_houses = [h for h in houses if h.get("risk_level") != "고위험"]
if not safe_houses:
    safe_houses = houses[:5] if houses else []

if not safe_houses:
    st.warning("분석 가능한 매물이 없습니다.")
    st.stop()

house_names = [f"{h['name']} ({h['deposit']}/{h['monthly']}만)" for h in safe_houses]
selected_idx = st.selectbox("📍 분석할 매물 선택", range(len(house_names)),
                             format_func=lambda i: house_names[i])
house = safe_houses[selected_idx]

if st.button("⚡ 이 집 종합 분석하기", use_container_width=True, type="primary"):
    st.session_state.report_house = house
    st.session_state.report_ready = True

if not st.session_state.get("report_ready"):
    st.info("매물을 선택하고 '종합 분석하기'를 눌러주세요.")
    st.stop()

house = st.session_state.report_house

# === Header Card ===
risk_color = {"안전": "#22C55E", "보통": "#F59E0B", "주의": "#F59E0B", "고위험": "#EF4444"}.get(house.get("risk_level", "보통"), "#64748B")
header_content = f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<h2 style="margin:0; color:#1E293B;">{house['name']}</h2>
<div style="font-size:14px; color:#64748B; margin-top:4px;">📍 {house['location']} | {house.get('address', '')} | 🚶 통근 {house.get('commute_time', '?')}분</div>
<div style="margin-top:8px; display:flex; gap:8px;">
<span style="background:#EEF2FF; color:#4F46E5; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:700;">{house['type']}</span>
<span style="background:{risk_color}22; color:{risk_color}; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:700;">🛡️ {house.get('risk_level', '미정')}</span>
</div>
</div>
<div style="text-align:right;">
<div style="font-size:28px; font-weight:900; color:#1E293B;">보증금 {house['deposit']:,}만</div>
<div style="font-size:20px; font-weight:700; color:#6366F1;">월세 {house['monthly']:,}만</div>
</div>
</div>"""
card(header_content)

# === Section 1: 안전 진단 ===
st.markdown("### 🛡️ 1. 안전 진단")

from src.ocr.parser import RiskAnalyzer
analyzer = RiskAnalyzer()

# 주소에서 구 추출하여 시세 추정
address = house.get("address", "")
try:
    area_sqm = float(house.get("area", "59.5").split("㎡")[0]) if "㎡" in str(house.get("area", "")) else 59.5
except Exception:
    area_sqm = 59.5

estimated_value = analyzer._estimate_market_value(address, area_sqm)
deposit_won = house["deposit"] * 10000

# 간이 깡통전세 비율 (근저당 정보 없으므로 보증금/시세만)
ratio = (deposit_won / estimated_value * 100) if estimated_value > 0 else 0

if ratio <= 60:
    safety_emoji, safety_color, safety_verdict = "✅", "#22C55E", "안전"
    safety_msg = "보증금이 시세 대비 안전한 수준입니다."
elif ratio <= 80:
    safety_emoji, safety_color, safety_verdict = "⚠️", "#F59E0B", "주의"
    safety_msg = "보증금 비율이 다소 높습니다. 전세보증보험 가입을 권장합니다."
else:
    safety_emoji, safety_color, safety_verdict = "🚨", "#EF4444", "위험"
    safety_msg = "보증금이 시세에 비해 매우 높습니다. 등기부 정밀 확인이 필요합니다."

safety_content = f"""
<div style="display:flex; align-items:center; gap:20px;">
<div style="text-align:center; min-width:120px;">
<div style="font-size:36px; font-weight:900; color:{safety_color};">{ratio:.0f}%</div>
<div style="font-size:12px; color:#64748B;">보증금/시세</div>
<div style="font-size:16px; font-weight:700; color:{safety_color};">{safety_emoji} {safety_verdict}</div>
</div>
<div style="flex:1;">
<div style="font-size:14px; color:#334155; line-height:1.8;">
• 추정 시세: <b>{estimated_value//10000:,}만원</b> (구별 평균 기준)<br>
• 보증금: <b>{house['deposit']:,}만원</b><br>
• {safety_msg}<br>
• 🏠 정확한 시세는 <a href="https://land.naver.com" target="_blank">네이버 부동산</a>에서 확인하세요
</div>
</div>
</div>"""
card(safety_content, style=f"border-left: 4px solid {safety_color};")

# === Section 2: 대출 시뮬레이션 ===
st.markdown("### 💰 2. 대출 시뮬레이션")

from src.agents.finance_agent import FinancialSimulator
sim = FinancialSimulator()

sim_profile = {
    "income_yearly": st.session_state.get("user_income", 0),
    "total_assets": st.session_state.get("user_assets", 2000),
    "employment_type": st.session_state.get("user_job_type", "unemployed"),
    "age": st.session_state.get("user_age", 25),
    "marital_status": st.session_state.get("user_married", "single")
}

sim_result = sim.simulate(sim_profile, house)
rec = sim_result["recommendation"]
res = sim_result["result"]

loan_content = f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
<div>
<div style="font-size:16px; font-weight:700; color:#1E293B;">🏦 {rec['loan_product']}</div>
<div style="font-size:13px; color:#64748B; margin-top:4px;">금리 {rec['loan_rate']} | 대출 {rec['loan_amount']:,}만원</div>
</div>
<div style="text-align:right;">
<div style="font-size:12px; color:#64748B;">실질 월 부담</div>
<div style="font-size:28px; font-weight:900; color:#6366F1;">{res['real_monthly_cost']:,}만원</div>
</div>
</div>
<div style="background:#F8FAFC; padding:12px; border-radius:8px; font-size:13px; color:#334155; line-height:1.8;">
• 월세: {house['monthly']}만 + 대출이자: {rec['interest_monthly']}만 - 월세지원: {rec['subsidy_monthly']}만<br>
• 본인 부담금 (보증금 - 대출): <b>{res['required_own_money']:,}만원</b><br>
• {res['summary']}
</div>"""
card(loan_content, style="border-left: 4px solid #6366F1;")

# === Section 3: 생활비 분석 ===
st.markdown("### 🏠 3. 생활비 분석")

monthly_income = st.session_state.get("user_income", 0) // 12 if st.session_state.get("user_income", 0) > 0 else 0
total_housing = res["real_monthly_cost"] + 8  # 관리비 추정
est_living = 30 + 5 + 5 + 5 + 10  # 식비+교통+통신+공과금+기타
total_expense = total_housing + est_living
remaining = monthly_income - total_expense

if monthly_income > 0:
    housing_ratio = total_housing / monthly_income * 100
    if remaining >= 10:
        life_emoji, life_color, life_verdict = "✅", "#22C55E", "생활 가능"
    elif remaining >= 0:
        life_emoji, life_color, life_verdict = "⚠️", "#F59E0B", "빠듯함"
    else:
        life_emoji, life_color, life_verdict = "🚨", "#EF4444", "생활 어려움"

    living_content = f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="font-size:14px; color:#334155; line-height:1.8;">
• 월 소득: <b>{monthly_income:,}만원</b><br>
• 주거비 (실질월세+관리비): <b>{total_housing:,}만원</b> ({housing_ratio:.0f}%)<br>
• 생활비 (식비·교통·통신 등): <b>{est_living}만원</b> (추정)<br>
• 총 지출: <b>{total_expense:,}만원</b>
</div>
</div>
<div style="text-align:center; min-width:120px;">
<div style="font-size:32px; font-weight:900; color:{life_color};">{remaining:+,}만</div>
<div style="font-size:14px; font-weight:700; color:{life_color};">{life_emoji} {life_verdict}</div>
</div>
</div>"""
    card(living_content, style=f"border-left: 4px solid {life_color};")

    if housing_ratio > 30:
        st.warning(f"⚠️ 주거비 비율 {housing_ratio:.0f}% — 소득의 30% 이하가 권장됩니다.")
else:
    st.info("💡 프로필에서 소득 정보를 입력하면 생활비 분석이 가능합니다.")
    if st.button("👤 프로필 설정하기"):
        st.switch_page("pages/2_👤_내_프로필.py")

# === Section 4: 지역 가이드 ===
st.markdown("### 📍 4. 지역 가이드")
seoul = regions.get("서울", {})
matched = None
for district, info in seoul.items():
    if district.replace("구", "") in address:
        matched = (district, info)
        break

if matched:
    name, info = matched
    stars = "⭐" * info["safety_score"] + "☆" * (5 - info["safety_score"])
    area_content = f"""
<div style="font-size:16px; font-weight:700; color:#1E293B; margin-bottom:8px;">📍 {name}</div>
<div style="font-size:14px; color:#475569; margin-bottom:12px;">{info['vibe']}</div>
<div style="font-size:13px; color:#334155; line-height:1.8;">
🚇 {info['transport']}<br>
👍 {', '.join(info['pros'])}<br>
👎 {', '.join(info['cons'])}<br>
🛡️ 안전: {stars}<br>
💡 {info['tips']}
</div>"""
    card(area_content)

# === Section 5: 다음 단계 ===
spacer("20px")
st.markdown("### ▶ 다음 단계")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🛡️ 등기부 정밀 분석", use_container_width=True):
        st.switch_page("pages/2_🛡️_안전_진단.py")
with c2:
    if st.button("✅ 집보기 체크리스트", use_container_width=True):
        st.switch_page("pages/7_✅_체크리스트.py")
with c3:
    if st.button("📝 협상 메시지 작성", use_container_width=True):
        st.switch_page("pages/3_📝_협상_도우미.py")

# === 매물 비교 장바구니 ===
spacer("10px")
if "saved_listings" not in st.session_state:
    st.session_state.saved_listings = []

if st.button(f"💾 이 매물 저장하기 (현재 {len(st.session_state.saved_listings)}개 저장됨)", use_container_width=True):
    if house["id"] not in [h["id"] for h in st.session_state.saved_listings]:
        st.session_state.saved_listings.append({
            **house,
            "real_monthly": res["real_monthly_cost"],
            "best_loan": rec["loan_product"],
            "safety_ratio": f"{ratio:.0f}%"
        })
        st.success(f"✅ '{house['name']}' 저장 완료!")
    else:
        st.info("이미 저장된 매물입니다.")

# === 저장된 매물 비교 테이블 ===
if len(st.session_state.saved_listings) >= 2:
    spacer("20px")
    st.markdown("### 🔄 저장 매물 비교")
    import pandas as pd
    compare_data = []
    for h in st.session_state.saved_listings:
        compare_data.append({
            "매물": h["name"],
            "보증금(만)": h["deposit"],
            "월세(만)": h["monthly"],
            "실질월세(만)": h.get("real_monthly", h["monthly"]),
            "통근(분)": h.get("commute_time", "?"),
            "안전": h.get("risk_level", "?"),
            "보증금/시세": h.get("safety_ratio", "?"),
            "추천대출": h.get("best_loan", "-")
        })
    df = pd.DataFrame(compare_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("🗑️ 비교 목록 초기화"):
        st.session_state.saved_listings = []
        st.rerun()
