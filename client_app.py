"""
client_app.py
--------------
Customer-facing portal for the HEFI system.
Features:
1. Login with Household ID
2. Data Update Wizard
3. Personal HEFI Dashboard
4. AI Support Chatbot
"""

import streamlit as st
import sqlite3
import pandas as pd
import os
import time
from fairness_index import run_pipeline, upsert_households, recalculate_with_context, DB_PATH
from chatbot_logic import get_chatbot_response

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Citizen HEFI Portal", page_icon="🏠", layout="wide")

# Custom Premium Styling
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background: linear-gradient(45deg, #238636, #2ea043); color: white; border: none; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    .user-card { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; }
    .hefi-badge { font-size: 2.5em; font-weight: bold; color: #58a6ff; text-align: center; }
    .chat-bubble { background-color: #21262d; padding: 12px; border-radius: 10px; margin: 5px 0; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# ─── Session State ───────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ─── Helper Functions ────────────────────────────────────────────────────────
def get_user_data(hid):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM households WHERE household_id = '{hid}'", conn)
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

# ─── Login Screen ────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.title("🏠 Citizen Energy Portal")
    st.markdown("Please log in with your Registered Household ID to view your Fairness Index (HEFI).")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            hid_input = st.text_input("Enter Household ID (e.g., HH_001)", placeholder="HH_XXX")
            if st.button("Access Dashboard"):
                user = get_user_data(hid_input)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = hid_input
                    st.rerun()
                else:
                    st.error("Household ID not found. Please contact your local utility office.")
    st.stop()

# ─── Authenticated Dashboard ─────────────────────────────────────────────────
user_data = get_user_data(st.session_state.user_id)

# Sidebar Navigation
with st.sidebar:
    st.title(f"Welcome, {st.session_state.user_id}")
    st.markdown("---")
    menu = st.radio("Navigation", ["📈 My HEFI Status", "📝 Update My Details", "💬 Support Chat"])
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ─── TAB: Dashboard ──────────────────────────────────────────────────────────
if menu == "📈 My HEFI Status":
    st.title("📈 Your Household Energy Fairness Status")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='user-card'><p style='text-align:center;'>Current HEFI Score</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='hefi-badge'>{user_data['hefi_score']}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='user-card'><p style='text-align:center;'>Tax/Tariff Tier</p>", unsafe_allow_html=True)
        color = "#238636" if user_data['tariff_tier'] == "Subsidized" else "#d29922" if user_data['tariff_tier'] == "Standard" else "#f85149"
        st.markdown(f"<div class='hefi-badge' style='font-size:1.8em; color:{color};'>{user_data['tariff_tier']}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='user-card'><p style='text-align:center;'>Last Meter Reading</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='hefi-badge' style='font-size:1.8em;'>{user_data['monthly_electricity_consumption_kwh']} <span style='font-size:0.5em;'>kWh</span></div></div>", unsafe_allow_html=True)

    st.markdown("### 📊 Fairness Breakdown")
    # Small bar chart for components
    components = {
        "Income Vuln": user_data['income_vulnerability'],
        "Household Size": user_data['household_size_factor'],
        "Dependency": user_data['energy_dependency'],
        "Anomaly": user_data['consumption_anomaly']
    }
    st.bar_chart(pd.Series(components))
    st.info("💡 **Tip**: A higher score means you are categorized as more vulnerable, qualifying you for higher subsidies.")

# ─── TAB: Update Details ─────────────────────────────────────────────────────
elif menu == "📝 Update My Details":
    st.title("📝 Self-Report Dashboard")
    st.markdown("Has your household situation changed? Update your details below to ensure a fair tariff calculation.")
    
    with st.form("update_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            new_size = st.number_input("Household Size", value=int(user_data['household_size']), min_value=1)
            new_income = st.number_input("Monthly Income (₹)", value=int(user_data['household_income']), min_value=0)
        with col_b:
            new_appliances = st.number_input("Appliance Count", value=int(user_data['appliance_count']), min_value=1)
            new_renewable = st.selectbox("Renewable Access", ["Yes", "No"], index=0 if user_data['renewable_energy_access']=="Yes" else 1)
        
        submitted = st.form_submit_button("Securely Update My Details")
        if submitted:
            # 1. Show processing state
            with st.spinner("Synchronizing with HEFI Registry..."):
                updated_record = user_data.copy()
                updated_record.update({
                    "household_size": new_size,
                    "household_income": new_income,
                    "appliance_count": new_appliances,
                    "renewable_energy_access": new_renewable
                })
                
                # 2. Contextual recalculation
                df_updated = recalculate_with_context(pd.DataFrame([updated_record]))
                upsert_households(df_updated)
                time.sleep(1.5)
                # Set a flag to show success outside the form
                st.session_state.update_success = True
                st.rerun()

    if st.session_state.get("update_success"):
        st.toast("Registry Synchronized!", icon="✅")
        st.success("**Update Complete.** Your HEFI score has been automatically refreshed based on the new data.")
        if st.button("View My Updated HEFI Status"):
            st.session_state.update_success = False
            st.rerun()

# ─── TAB: Support Chat ───────────────────────────────────────────────────────
elif menu == "💬 Support Chat":
    st.title("💬 HEFI Assistant")
    st.markdown("Ask our AI assistant about your score, subsidies, or energy fairness issues.")
    
    # Display Chat
    for msg in st.session_state.chat_history:
        st.markdown(f"<div class='chat-bubble'><b>{'You' if msg['role']=='user' else 'Bot'}:</b> {msg['text']}</div>", unsafe_allow_html=True)
    
    # Input
    user_q = st.chat_input("How can I lower my electricity bill?")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "text": user_q})
        response = get_chatbot_response(user_q, user_data)
        st.session_state.chat_history.append({"role": "bot", "text": response})
        st.rerun()
