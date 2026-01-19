
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.ui import setup_page, draw_sidebar, T, card, badge_html

setup_page("Young & Home")
draw_sidebar()

# =================
# HOME DASHBOARD
# =================

# Welcome Card
welcome_content = f"""
<h2 class="no-margin-top">{T('home_welcome').replace('서강', st.session_state.user_name)}</h2>
<p>{T('home_desc')}</p>
<div class="flex-gap-12 mt-20">
    {badge_html(T('badge_new'), accent=True)}
    {badge_html(T('badge_system'))}
</div>
"""
card(welcome_content)

# Dashboard Grid
col1, col2 = st.columns(2)
with col1:
    discovery_content = f"""
    <div class="stat-circle bg-blue-radial"></div>
    <h3 style="color:#1E293B;">{T('card_discovery')}</h3>
    <p><strong>12</strong> {T('card_discovery_desc')}</p>
    <p class="text-sm-gray">{T('card_discovery_sub')}</p>
    """
    card(discovery_content, height="160px", style="position:relative; overflow:hidden;")

with col2:
    safety_content = f"""
    <div class="stat-circle bg-red-radial"></div>
    <h3 style="color:#1E293B;">{T('card_safety')}</h3>
    <p><strong>1</strong> {T('card_safety_desc')}</p>
    <p class="text-sm-gray">{T('card_safety_sub')}</p>
    """
    card(safety_content, height="160px", style="position:relative; overflow:hidden;")

st.markdown(f"### {T('quick_actions')}")
b_col1, b_col2, b_col3 = st.columns(3)

with b_col1:
    if st.button(T('btn_start_search'), use_container_width=True):
        st.switch_page("pages/1_🔍_스마트_검색.py")
with b_col2:
    if st.button(T('btn_analyze'), use_container_width=True):
        st.switch_page("pages/2_🛡️_안전_진단.py")
with b_col3:
    if st.button(T('btn_calc'), use_container_width=True):
        st.switch_page("pages/5_💰_금융_계산기.py")
