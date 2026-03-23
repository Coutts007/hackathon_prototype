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
from fairness_index import init_db, run_pipeline, upsert_households, recalculate_with_context, DB_PATH
from chatbot_logic import get_chatbot_response

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Citizen HEFI Portal", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# Theme selector
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Theme toggle (visible at top, not hidden in sidebar)
col_theme1, col_theme2 = st.columns([8, 2])
with col_theme2:
    selected_theme = st.radio(
        "Theme",
        ["🌙 Dark", "☀️ Light"],
        index=0 if st.session_state.theme == "dark" else 1,
        horizontal=True,
        key="theme_mode_select",
    )
    st.session_state.theme = "dark" if "🌙" in selected_theme else "light"

# Apply theme CSS

def _get_theme_values(mode: str):
    if mode == "dark":
        return {
            "app_bg": "#0f1419",
            "text": "#e0e6ed",
            "panel": "#1a1f28",
            "border": "#2d3748",
            "card": "#1a1f28",
            "card_shadow": "rgba(0,0,0,0.6)",
            "nav_bg": "linear-gradient(135deg, #1a3a5c 0%, #0f2744 100%)",
            "nav_text": "white",
            "nav_shadow": "rgba(0,0,0,0.5)",
            "muted": "#8b94a5",
            "link": "#4da6ff",
            "input_bg": "#16202b",
            "input_text": "#e0e6ed",
            "input_border": "#2d3748",
            "button_start": "#00d4ff",
            "button_end": "#0099cc",
            "button_text": "#0f1419",
            "hero_sub": "#a8b3c1",
            "footer": "#6b7684",
            "accent": "#00d4ff",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "secondary_bg": "#242d39",
        }
    return {
        "app_bg": "#f5f7fa",
        "text": "#1a202c",
        "panel": "#ffffff",
        "border": "#e2e8f0",
        "card": "#ffffff",
        "card_shadow": "rgba(0,0,0,0.08)",
        "nav_bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "nav_text": "white",
        "nav_shadow": "rgba(102, 126, 234, 0.3)",
        "muted": "#6b7280",
        "link": "#667eea",
        "input_bg": "#f9fafb",
        "input_text": "#1a202c",
        "input_border": "#e5e7eb",
        "button_start": "#667eea",
        "button_end": "#764ba2",
        "button_text": "white",
        "hero_sub": "#4b5563",
        "footer": "#9ca3af",
        "accent": "#667eea",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "secondary_bg": "#f3f4f6",
    }

_theme = _get_theme_values(st.session_state.theme)

st.markdown(f"""
    <style>
    /* Global */
    * {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }}
    
    /* Layout */
    .stApp {{ background: {_theme['app_bg']}; color: {_theme['text']}; }}
    .stContainer {{ max-width: 100%; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background: {_theme['secondary_bg']}; }}
    
    /* Headers */
    h1, h2, h3 {{ color: {_theme['text']}; font-weight: 700; letter-spacing: -0.5px; }}
    h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.875rem; margin-bottom: 1rem; }}
    h3 {{ font-size: 1.375rem; margin-bottom: 0.75rem; }}
    
    /* Cards */
    .info-card {{ 
        background: {_theme['card']}; 
        border-radius: 16px; 
        padding: 24px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 20px {_theme['card_shadow']}; 
        border: 1px solid {_theme['border']};
        transition: all 0.3s ease;
    }}
    .info-card:hover {{
        box-shadow: 0 8px 32px {_theme['card_shadow']};
        transform: translateY(-2px);
    }}
    .info-card h3 {{ margin-top: 0; color: {_theme['accent']}; margin-bottom: 1rem; }}
    .info-card p {{ margin: 10px 0; color: {_theme['muted']}; line-height: 1.6; }}
    
    /* Feature Grid */
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }}
    .feature-card {{
        background: linear-gradient(135deg, {_theme['button_start']}, {_theme['button_end']});
        border: none;
        color: {_theme['button_text']};
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    .feature-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.3);
    }}
    .feature-card strong {{
        display: block;
        font-size: 1.1rem;
        margin-bottom: 10px;
        opacity: 0.95;
    }}
    .feature-card p {{
        margin: 0;
        line-height: 1.5;
    }}
    
    /* Step Badge */
    .step-badge {{
        display: inline-block;
        background: linear-gradient(135deg, {_theme['accent']}22, {_theme['accent']}11);
        color: {_theme['accent']};
        border: 1.5px solid {_theme['accent']}44;
        border-radius: 999px;
        padding: 8px 16px;
        font-weight: 700;
        margin-right: 12px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }}
    .step-badge:hover {{
        background: {_theme['accent']}33;
        transform: scale(1.05);
    }}
    
    /* Forms */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>div>div:first-child {{
        background-color: {_theme['input_bg']} !important;
        color: {_theme['input_text']} !important;
        border: 1.5px solid {_theme['input_border']} !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
    }}
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {{
        border-color: {_theme['accent']} !important;
        box-shadow: 0 0 0 3px {_theme['accent']}22 !important;
    }}
    
    /* Buttons */
    .stButton>button {{
        width: 100%;
        border-radius: 10px;
        height: 3.2em;
        background: linear-gradient(135deg, {_theme['button_start']}, {_theme['button_end']});
        color: {_theme['button_text']};
        border: none;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}
    .stButton>button:active {{
        transform: translateY(0px);
    }}
    
    /* Text */
    .hero-title {{
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 1rem 0;
        background: linear-gradient(135deg, {_theme['accent']}, {_theme['button_end']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hero-sub {{
        color: {_theme['hero_sub']};
        margin-top: 12px;
        margin-bottom: 24px;
        font-size: 1.1rem;
        line-height: 1.6;
    }}
    
    /* Metric Cards */
    .user-card {{
        background-color: {_theme['card']};
        padding: 24px;
        border-radius: 16px;
        border: 1.5px solid {_theme['border']};
        margin-bottom: 20px;
        box-shadow: 0 4px 16px {_theme['card_shadow']};
        transition: all 0.3s ease;
        text-align: center;
    }}
    .user-card:hover {{
        box-shadow: 0 8px 24px {_theme['card_shadow']};
        transform: translateY(-4px);
    }}
    .user-card p {{
        margin: 0 0 16px 0;
        font-size: 0.95rem;
        color: {_theme['muted']};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .hefi-badge {{
        font-size: 2.4em;
        font-weight: 800;
        color: {_theme['accent']};
        margin: 0;
        letter-spacing: -1px;
    }}
    
    /* Chat */
    .chat-bubble {{
        background-color: {_theme['secondary_bg']};
        padding: 14px 18px;
        border-radius: 14px;
        margin: 8px 0;
        border-left: 4px solid {_theme['accent']};
        animation: slideIn 0.3s ease;
    }}
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateX(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateX(0);
        }}
    }}
    
    /* Footer */
    .footer {{
        color: {_theme['footer']};
        font-size: 0.9rem;
        text-align: center;
        padding-top: 20px;
        margin-top: 40px;
        border-top: 1px solid {_theme['border']};
    }}
    
    /* Alerts & Notifications */
    .stAlert {{
        border-radius: 12px !important;
        border: 1.5px solid !important;
    }}
    [data-testid="stAlert"] {{
        background-color: {_theme['secondary_bg']} !important;
        border-radius: 12px !important;
    }}
    
    /* Expandable sections */
    .streamlit-expanderHeader {{
        background-color: {_theme['secondary_bg']} !important;
        border-radius: 12px !important;
        border: 1px solid {_theme['border']} !important;
        transition: all 0.3s ease !important;
    }}
    .streamlit-expanderHeader:hover {{
        background-color: {_theme['card']} !important;
    }}
    
    /* Tabs */
    [data-testid="stTabs"] [aria-selected="true"] {{
        border-bottom: 3px solid {_theme['accent']} !important;
        color: {_theme['accent']} !important;
    }}
    
    /* Responsive */
    @media (max-width: 940px) {{
        .hero-title {{ font-size: 2rem; }}
        h1 {{ font-size: 1.8rem; }}
        .feature-grid {{ grid-template-columns: 1fr; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# Setup navigation state defaults
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "login_mode" not in st.session_state:
    st.session_state.login_mode = False

# ─── Session State ───────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Ensure the registry exists so users can register and data is persisted
init_db()

# ─── Helper Functions ────────────────────────────────────────────────────────
def get_user_data(hid):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM households WHERE household_id = ?", conn, params=(hid,))
    finally:
        conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

# ─── Landing / Login / Registration ──────────────────────────────────────────
if not st.session_state.authenticated:
    if "view" not in st.session_state:
        st.session_state.view = "landing"

    # Hero Section
    st.markdown("""
        <div style='margin: -40px -40px 30px -40px; padding: 50px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 0 0 20px 20px;' class='hero-section'>
            <h1 style='margin: 0 0 15px 0; font-size: 3.2rem; font-weight: 800; color: white;'>⚡ Citizen Energy Portal</h1>
            <p style='margin: 0; font-size: 1.2rem; line-height: 1.6; opacity: 0.95;'>Your gateway to fair energy tariffs, personalized HEFI insights, and practical savings advice.</p>
        </div>
    """, unsafe_allow_html=True)

    # Info Cards in 3 columns
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
            <div class='info-card'>
                <h3>🎯 Why HEFI Matters</h3>
                <p>HEFI ensures electricity pricing is fair by matching tariff support to those who need it most. Your household's unique situation matters.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("""
            <div class='info-card'>
                <h3>📊 How It Works</h3>
                <p><strong>Collect</strong> your household info • <strong>Calculate</strong> your fairness score • <strong>Unlock</strong> subsidies & support</p>
            </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown("""
            <div class='info-card'>
                <h3>✨ Benefits</h3>
                <p>Quick access, transparent scoring, personalized support, and AI-powered guidance—all at your fingertips.</p>
            </div>
        """, unsafe_allow_html=True)

    # Feature Cards
    st.markdown("<h2 style='margin-top: 40px; margin-bottom: 20px;'>✨ Key Features</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='feature-grid'>"
        "<div class='feature-card'>"
        "<strong>⚡ Instant HEFI Score</strong>"
        "<p>Get your household energy fairness index instantly with clear analysis and recommendations.</p>"
        "</div>"
        "<div class='feature-card'>"
        "<strong>📋 Smart Updates</strong>"
        "<p>Keep your profile current for fair calculations. Our system recalculates automatically.</p>"
        "</div>"
        "<div class='feature-card'>"
        "<strong>🤖 AI Assistant</strong>"
        "<p>Chat with HEFI anytime for personalized tips, energy-saving strategies, and tariff guidance.</p>"
        "</div>"
        "</div>"
    , unsafe_allow_html=True)

    col_info, col_actions = st.columns([2.5, 1.5])
    
    with col_info:
        st.markdown("""
            <div class='info-card'>
                <h3>🚀 Ready to Get Started?</h3>
                <p style='font-size: 1.05rem; line-height: 1.7;'>Join thousands of households accessing fair energy tariffs. Register now or log in if you're already a member. It takes less than 2 minutes.</p>
            </div>
        """, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        if st.session_state.view == "landing":
            if st.session_state.login_mode:
                st.info("🔒 Login mode active: enter your Household ID to access your dashboard.")
            
            st.markdown("<h3 style='margin-top: 0;'>🔐 Access Your Dashboard</h3>", unsafe_allow_html=True)
            hid_input = st.text_input("🆔 Household ID", placeholder="e.g., HH_001 or HH_12345", key="login_hid")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Login", key="login_btn", use_container_width=True):
                    if not hid_input.strip():
                        st.error("⚠️ Please enter your Household ID")
                    else:
                        user = get_user_data(hid_input)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = hid_input
                            st.session_state.view = "dashboard"
                            st.rerun()
                        else:
                            st.error("❌ Household ID not found. Please register or contact your local utility office.")
            
            with col_btn2:
                if st.button("📝 New Account", key="goto_register", use_container_width=True):
                    st.session_state.view = "register"
                    st.session_state.login_mode = False
                    st.rerun()

        elif st.session_state.view == "register":
            st.markdown("<h3 style='margin-top: 0;'>📋 Register Your Household</h3>", unsafe_allow_html=True)
            st.markdown("**Complete the form below** — it takes just 2 minutes. We'll calculate a fair tariff tier for your household.")
            
            with st.form("register_form", clear_on_submit=False):
                hid = st.text_input("🆔 Create Household ID", placeholder="e.g., HH_001", help="Must be unique")
                
                st.markdown("**📊 Your Household Details**", unsafe_allow_html=True)
                col_a, col_b = st.columns(2)
                with col_a:
                    consumption = st.number_input("⚡ Monthly Electricity (kWh)", min_value=0.0, value=120.0, step=10.0)
                    income = st.number_input("💰 Monthly Income (₹)", min_value=0, value=10000, step=1000)
                    size = st.number_input("👥 Household Size (members)", min_value=1, value=4, step=1)
                with col_b:
                    location = st.selectbox("📍 Location", ["Urban", "Rural"])
                    appliances = st.number_input("🔌 Appliance Count", min_value=0, value=5, step=1)
                    renewable = st.selectbox("♻️ Renewable Energy Access", ["Yes", "No"])
                
                st.markdown("**⚡ Energy Usage Pattern**", unsafe_allow_html=True)
                dependency = st.slider("Electricity Dependency Score", 0, 10, 5, help="0 = Low, 10 = Very High")

                col_register, col_back = st.columns(2)
                with col_register:
                    register = st.form_submit_button("✨ Register & Calculate", use_container_width=True)
                with col_back:
                    back = st.form_submit_button("← Back", use_container_width=True)
                
                if back:
                    st.session_state.view = "landing"
                    st.rerun()
                
                if register:
                    hid = hid.strip()
                    if not hid:
                        st.error("❌ Please enter a valid Household ID.")
                    else:
                        existing = get_user_data(hid)
                        if existing:
                            st.error("⚠️ Household ID already registered. Please log in instead.")
                        else:
                            new_record = {
                                "household_id": hid,
                                "monthly_electricity_consumption_kwh": float(consumption),
                                "household_income": int(income),
                                "household_size": int(size),
                                "urban_or_rural": location,
                                "appliance_count": int(appliances),
                                "renewable_energy_access": renewable,
                                "electricity_dependency_score": float(dependency),
                            }
                            with st.spinner("⏳ Processing your registration and calculating HEFI..."):
                                df_new = recalculate_with_context(pd.DataFrame([new_record]))
                                upsert_households(df_new)
                                time.sleep(1)

                            hefi_score = df_new.iloc[0]['hefi_score']
                            tariff_tier = df_new.iloc[0]['tariff_tier']
                            
                            st.success(f"✅ **Registration Successful!**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Your HEFI Score", f"{hefi_score:.1f}", help="Higher = More eligible for subsidies")
                            with col2:
                                st.metric("Tariff Tier", tariff_tier)
                            
                            st.info("🎉 You can now access your dashboard. Click below to continue.")
                            if st.button("🚀 Go to Dashboard", use_container_width=True):
                                st.session_state.authenticated = True
                                st.session_state.user_id = hid
                                st.session_state.view = "dashboard"
                                st.rerun()

        else:
            st.session_state.view = "landing"

    st.stop()

# ─── Authenticated Dashboard ─────────────────────────────────────────────────
user_data = get_user_data(st.session_state.user_id)

# Sidebar Navigation
with st.sidebar:
    st.markdown(f"# 👤 {st.session_state.user_id}")
    st.markdown("---")
    
    menu = st.radio(
        "📍 Navigation",
        ["📈 My HEFI Status", "📝 Update My Details", "💬 Support Chat"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"""
        <div style='padding: 15px; background: rgba(0,212,255,0.1); border-radius: 10px; border: 1px solid rgba(0,212,255,0.3); margin-top: 20px;'>
        <p style='margin: 0; font-size: 0.9rem; color: #8b94a5;'><strong>💡 Tip:</strong> A higher HEFI score means more eligibility for subsidies and energy support.</p>
        </div>
    """, unsafe_allow_html=True)

# ─── TAB: Dashboard ──────────────────────────────────────────────────────────
if menu == "📈 My HEFI Status":
    st.markdown("# 📈 Your Household Energy Fairness Status")
    st.markdown("---")
    
    # Top Metrics
    c1, c2, c3 = st.columns(3, gap="medium")
    
    with c1:
        st.markdown("<div class='user-card'><p>Current HEFI Score</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='hefi-badge'>{user_data['hefi_score']:.1f}</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b94a5; font-size: 0.9rem;'>Range: 0-100</p>", unsafe_allow_html=True)
    
    with c2:
        st.markdown("<div class='user-card'><p>Your Tariff Tier</p>", unsafe_allow_html=True)
        
        tier = user_data['tariff_tier']
        if tier == "Subsidized":
            color = "#10b981"
            icon = "🟢"
        elif tier == "Standard":
            color = "#f59e0b"
            icon = "🟡"
        else:
            color = "#ef4444"
            icon = "🔴"
        
        st.markdown(f"<div class='hefi-badge' style='color: {color}; font-size: 1.8em;'>{icon}<br>{tier}</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b94a5; font-size: 0.9rem;'>Subsidy Eligibility</p>", unsafe_allow_html=True)
    
    with c3:
        st.markdown("<div class='user-card'><p>Monthly Consumption</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='hefi-badge' style='font-size: 1.8em;'>{user_data['monthly_electricity_consumption_kwh']:.0f}<span style='font-size: 0.5em;'>kWh</span></div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b94a5; font-size: 0.9rem;'>Last Reading</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Score Breakdown
    st.markdown("### 📊 Your Fairness Score Breakdown")
    
    breakdown_col1, breakdown_col2 = st.columns(2)
    
    with breakdown_col1:
        components = {
            "Income Vulnerability": user_data['income_vulnerability'],
            "Household Size": user_data['household_size_factor'],
            "Dependency Score": user_data['energy_dependency'],
            "Consumption Anomaly": user_data['consumption_anomaly']
        }
        st.bar_chart(pd.Series(components))
    
    with breakdown_col2:
        st.markdown("""
            <div class='info-card'>
                <h3>📌 What This Means</h3>
                <p><strong>Income Vulnerability:</strong> Lower income = Higher priority for subsidies</p>
                <p><strong>Household Size:</strong> Larger families get more support</p>
                <p><strong>Dependency Score:</strong> Measures reliance on electricity for essential services</p>
                <p><strong>Consumption Anomaly:</strong> Unusual usage patterns (high/low) are flagged</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # What-if Simulator
    with st.expander("🔮 **What-If Simulator: See How Changes Affect Your HEFI**", expanded=False):
        st.markdown("Try adjusting your household parameters to see how your HEFI score and tariff tier might change. **Note:** Changes are simulated only — your actual data remains unchanged until you use the Update tab.")
        
        sim_col_a, sim_col_b = st.columns(2)
        with sim_col_a:
            sim_consumption = st.number_input(
                "⚡ Simulated Monthly Consumption (kWh)",
                value=float(user_data['monthly_electricity_consumption_kwh']),
                min_value=0.0,
                step=10.0,
                key="sim_consumption",
            )
            sim_income = st.number_input(
                "💰 Simulated Monthly Income (₹)",
                value=int(user_data['household_income']),
                min_value=0,
                step=1000,
                key="sim_income",
            )
        with sim_col_b:
            sim_size = st.number_input(
                "👥 Simulated Household Size",
                value=int(user_data['household_size']),
                min_value=1,
                step=1,
                key="sim_size",
            )
            sim_renewable = st.selectbox(
                "♻️ Simulated Renewable Access",
                ["Yes", "No"],
                index=0 if user_data['renewable_energy_access'] == "Yes" else 1,
                key="sim_renewable",
            )

        if st.button("🚀 Run Simulation", use_container_width=True):
            trial = user_data.copy()
            trial.update({
                "monthly_electricity_consumption_kwh": float(sim_consumption),
                "household_income": int(sim_income),
                "household_size": int(sim_size),
                "renewable_energy_access": sim_renewable,
            })
            sim_df = run_pipeline(pd.DataFrame([trial]), retrain=False)
            sim_row = sim_df.iloc[0]
            
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            with sim_col1:
                st.metric(
                    "Simulated HEFI",
                    f"{sim_row['hefi_score']:.1f}",
                    delta=f"{sim_row['hefi_score'] - user_data['hefi_score']:+.1f}",
                )
            with sim_col2:
                st.metric("Current HEFI", f"{user_data['hefi_score']:.1f}")
            with sim_col3:
                st.info(f"**Projected Tier:** {sim_row['tariff_tier']}")

# ─── TAB: Update Details ─────────────────────────────────────────────────────
elif menu == "📝 Update My Details":
    st.markdown("# 📝 Self-Report Dashboard")
    st.markdown("---")
    st.markdown("**Has your household situation changed?** Keep your profile current to ensure fair tariff calculations. We'll automatically recalculate your HEFI score based on your updates.")
    
    with st.form("update_form"):
        st.markdown("### 👥 Household Information")
        col_a, col_b = st.columns(2)
        with col_a:
            new_size = st.number_input("👥 Household Size", value=int(user_data['household_size']), min_value=1)
            new_income = st.number_input("💰 Monthly Income (₹)", value=int(user_data['household_income']), min_value=0, step=500)
        with col_b:
            new_appliances = st.number_input("🔌 Appliance Count", value=int(user_data['appliance_count']), min_value=0)
            new_renewable = st.selectbox("♻️ Renewable Energy Access", ["Yes", "No"], index=0 if user_data['renewable_energy_access']=="Yes" else 1)
        
        st.markdown("---")
        col_submit, col_space, col_cancel = st.columns([1.2, 1, 1])
        
        with col_submit:
            submitted = st.form_submit_button("✅ Securely Update My Details", use_container_width=True)
        
        if submitted:
            with st.spinner("⏳ Synchronizing with HEFI Registry..."):
                updated_record = user_data.copy()
                updated_record.update({
                    "household_size": new_size,
                    "household_income": new_income,
                    "appliance_count": new_appliances,
                    "renewable_energy_access": new_renewable
                })
                
                df_updated = recalculate_with_context(pd.DataFrame([updated_record]))
                upsert_households(df_updated)
                time.sleep(1.5)
                st.session_state.update_success = True
                st.rerun()

    if st.session_state.get("update_success"):
        st.success("✅ **Registry Synchronized!**")
        st.markdown(f"""
            <div class='info-card'>
                <h3>📊 Your Updated HEFI Score</h3>
                <p style='text-align: center; font-size: 2.4rem; font-weight: 800; color: #00d4ff; margin: 0;'>{user_data['hefi_score']:.1f}</p>
                <p style='text-align: center; margin-top: 10px;'>Your tariff tier: <strong>{user_data['tariff_tier']}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.session_state.update_success = False
            st.rerun()
    
    st.markdown("---")
    st.info("💡 Your HEFI score is recalculated automatically whenever you make updates. Changes take effect immediately.")

# ─── TAB: Support Chat ───────────────────────────────────────────────────────
elif menu == "💬 Support Chat":
    st.markdown("# 💬 HEFI AI Assistant")
    st.markdown("---")
    st.markdown("**Ask me anything about your HEFI score, tariff tier, energy-saving strategies, or subsidy eligibility.** I'm powered by AI trained on the entire HEFI system. 🤖")
    
    # Quick suggestion buttons
    st.markdown("### 💡 Quick Questions")
    quick_questions = [
        "What is HEFI and how does it work?",
        "How can I improve my HEFI score?",
        "What are the tariff tiers?",
        "How can I save money on my electricity bill?",
        "What subsidies am I eligible for?",
        "What's my current score and why?",
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(question, key=f"quick_q_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "text": question})
                with st.spinner("🤔 Thinking..."):
                    import time
                    time.sleep(0.5)  # Simulate processing
                    response = get_chatbot_response(question, user_data)
                st.session_state.chat_history.append({"role": "bot", "text": response})
                st.rerun()
    
    st.markdown("---")
    
    # Chat Display with Auto-scroll
    if st.session_state.chat_history:
        st.markdown("### 📜 Conversation")
        chat_container = st.container()
        
        with chat_container:
            for idx, msg in enumerate(st.session_state.chat_history):
                if msg['role'] == "user":
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #667eea, #764ba2); 
                                    color: white; padding: 14px 18px; border-radius: 14px; 
                                    margin: 10px 0; text-align: right; max-width: 80%; 
                                    margin-left: 20%; animation: slideIn 0.3s ease;'>
                            <b>👤 You:</b> {msg['text']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class='chat-bubble'>
                            <b>🤖 Assistant:</b><br>{msg['text']}
                        </div>
                    """, unsafe_allow_html=True)
        
        # Clear history button
        col_clear, col_space = st.columns([1, 4])
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    else:
        st.info("👋 **No messages yet.** Ask a quick question above or type one below!")
    
    st.markdown("---")
    
    # Chat Input Section
    st.markdown("### 💬 Your Question")
    col_input, col_send = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "Ask anything about HEFI:",
            placeholder="e.g., How can I lower my bill? What is my HEFI score?",
            label_visibility="collapsed",
            key="chat_input"
        )
    
    with col_send:
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        send_button = st.button("📤 Send", use_container_width=True, key="send_chat")
    
    # Process user input (only once per message)
    if send_button and user_input and user_input.strip():
        # Initialize tracking for processed messages
        if "last_processed_message" not in st.session_state:
            st.session_state.last_processed_message = None
        
        # Only process if this is a new message (not a duplicate)
        if st.session_state.last_processed_message != user_input:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "text": user_input})
            
            # Generate bot response in real-time
            with st.spinner("⏳ Generating response..."):
                import time
                time.sleep(0.3)  # Small delay for natural feel
                response = get_chatbot_response(user_input, user_data)
            
            # Add bot response to history
            st.session_state.chat_history.append({"role": "bot", "text": response})
            
            # Mark this message as processed
            st.session_state.last_processed_message = user_input
            
            # Clear input and rerun
            st.rerun()
    
    # Help section
    st.markdown("---")
    with st.expander("❓ **How to Get the Best Responses**"):
        st.markdown("""
        **💡 Tips for Better Answers:**
        
        1. **Be Specific**: Instead of "Help me", try "What is my HEFI score based on₹20k income and 5 family members?"
        2. **Ask Follow-ups**: Don't hesitate to ask "Why is my score low?" or "How can I improve it?"
        3. **Share Context**: Mention if you recently had a baby, job change, or installed solar
        4. **Ask for Examples**: Request "Can you give me examples of high and low HEFI scores?"
        
        **Topic Examples:**
        - **Score Questions**: "What affects my HEFI score?", "Why am I in Standard tier?"
        - **Savings Tips**: "How can I lower my electricity bill?", "What's the best way to save energy?"
        - **Tier Info**: "What does Subsidized mean?", "Can I move to a better tier?"
        - **Account Issues**: "How do I appeal my score?", "When do I see bill changes?"
        
        **🎯 Remember:** I have full access to your household data, so personalized questions get the best responses!
        """)
    
    st.markdown("""
    <div style='margin-top: 30px; padding: 15px; background: rgba(0,212,255,0.05); 
                border-left: 4px solid #00d4ff; border-radius: 10px;'>
        <p style='margin: 0; font-size: 0.9rem; color: #8b94a5;'>
        <strong>⚡ Note:</strong> This AI assistant is trained on the HEFI system and your personal data. 
        For account issues, billing disputes, or to appeal your score, contact your utility's customer support.
        </p>
    </div>
    """, unsafe_allow_html=True)
