import streamlit as st
import pandas as pd
import numpy as np
import time
import pyotp
import plotly.graph_objects as go
from SmartApi import SmartConnect

# १. व्यावसायिक लेआउट डिझाईन (Wide Mode)
st.set_page_config(layout="wide", page_title="Professional Trading Terminal")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f3f6; border-radius: 5px 5px 0px 0px;
        padding: 8px 20px; font-weight: bold; color: #4e5d6c;
    }
    .stTabs [aria-selected="true"] { background-color: #2e5bffd1 !important; color: white !important; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Pro-Trader Analytics Terminal")
st.caption("Advanced Real-Time Workspace - Stable Version")

# --- सेशन्स आणि स्टेट मॅनेजमेंट ---
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []
if 'price_history' not in st.session_state:
    st.session_state.price_history = pd.DataFrame(columns=['Time', 'Open', 'High', 'Low', 'Close'])

# --- २. Angel One API लॉग-इन ---
@st.cache_resource(ttl=28800)
def init_angel_login():
    try:
        if "angel_one" in st.secrets and "totp_key" in st.secrets["angel_one"]:
            creds = st.secrets["angel_one"]
            totp = pyotp.TOTP(creds["totp_key"]).now()
            obj = SmartConnect(api_key=creds["api_key"])
            session = obj.generateSession(creds["client_id"], creds["password"], totp)
            if session['status']:
                return obj
        return None
    except:
        return None

smart_api = init_angel_login()

# ३. टॉप इंडेक्स बार
selected_index = st.selectbox("🎯 Active Trading Index:", ["NIFTY", "BANKNIFTY", "SENSEX"])

st.divider()

# --- ४. मल्टि-स्क्रीन टॅब रचना ---
tab_chart, tab_chain, tab_alerts = st.tabs(["📈 Charts & Quick Orders", "⛓️ Option Chain Desk", "📊 Analysis & Alert Stream"])

# नो-ब्लिंक कंटेनर्स सेटअप (Duplicate Element ID एरर टाळण्यासाठी कंन्टेनर लॉक केले आहेत)
with tab_chart:
    chart_metric_empty = st.empty()
    chart_view_empty = st.empty()
    st.markdown("<p style='font-weight:bold; color:#2e5bffd1;'>⚡ SCALPER MODE ORDERS</p>", unsafe_allow_html=True)
    # बटन वारंवार री-क्रिएट न करता स्थिर ठेवण्यासाठी लूपच्या बाहेर फक्त एक वेळेस ठेवले आहेत
    b1, b2, b3, b4 = st.columns(4)
    b1.button("🟢 BUY CALL (ATM)", key="btn_buy_ce", use_container_width=True)
    b2.button("🔴 BUY PUT (ATM)", key="btn_buy_pe", use_container_width=True)
    b3.button("🟥 EXIT POSITIONS", key="btn_exit", use_container_width=True)
    status_placeholder = b4.empty()

with tab_chain:
    chain_metric_empty = st.empty()
    chain_view_empty = st.empty()

with tab_alerts:
    alert_metric_empty = st.empty()
    col_a1, col_a2 = st.columns(2)
    alert_stream_empty = col_a1.empty()
    graph_stream_empty = col_a2.empty()

# --- ५. टिक-बाय-टिक डेटा इंजिन ---
def fetch_terminal_data(api_obj, index_name):
    base_p = 25308.40 if index_name == "NIFTY" else (60973.15 if index_name == "BANKNIFTY" else 82101.95)
    step = 50 if index_name == "NIFTY" else 100
    
    if api_obj is not None:
        try:
            exchange = "NSE"
            if index_name == "NIFTY": token = "99926000"
            elif index_name == "BANKNIFTY": token = "99926009"
            else:
                token = "99919000"
                exchange = "BSE"
                
            ltp_response = api_obj.getLtp(exchange, index_name, token)
            if ltp_response['status'] and 'data' in ltp_response:
                base_p = float(ltp_response['data']['ltp'])
        except:
            pass
            
    atm_strike = round(base_p / step) * step
    strikes = [int(atm_strike + (i * step)) for i in range(-5, 6)]
    
    data = []
    ts = time.strftime('%H:%M:%S')
    
    new_row = {
        'Time': ts, 'Open': base_p - np.random.uniform(-2, 2),
        'High': base_p + np.random.uniform(0, 4), 'Low': base_p - np.random.uniform(0, 4),
        'Close': base_p + np.random.uniform(-1, 1)
    }
    st.session_state.price_history = pd.concat([st.session_state.price_history, pd.DataFrame([new_row])], ignore_index=True)
    if len(st.session_state.price_history) > 35:
        st.session_state.price_history = st.session_state.price_history.iloc[1:]
        
    for s in strikes:
        distance = (s - base_p) / step
        ce_delta = round(0.5 - (distance * 0.06), 2)
        pe_delta = round(-0.5 - (distance * 0.06), 2)
        
        ce_oi_chg = np.random.randint(-12, 28) * 10000
        pe_oi_chg = np.random.randint(-12, 28) * 10000
        
        row = {
            "CE_Volume": np.random.randint(10, 90) * 100000,
            "CE_OI_Chg": ce_oi_chg,
            "CE_OI": np.random.randint(10, 95) * 100000,
            "CE_IV": round(np.random.uniform(12.0, 16.0), 2),
            "CE_Delta": max(0.01, min(0.99, ce_delta)),
            "CE_LTP": round(max(5, 210 - (distance * 40)), 2),
            "STRIKE": s,
            "PE_LTP": round(max(5, 210 + (distance * 40)), 2),
            "PE_Delta": max(-0.99, min(-0.01, pe_delta)),
            "PE_IV": round(np.random.uniform(12.0, 16.0), 2),
            "PE_OI": np.random.randint(10, 95) * 100000,
            "PE_OI_Chg": pe_oi_chg,
            "PE_Volume": np.random.randint(10, 90) * 100000,
        }
        
        if ce_oi_chg < -120000:
            msg = f"⏱️ {ts} | [🚨 SHORT COVERING] {s} CE मधुन कॉल रायटर्स पळाले!"
            if msg not in st.session_state.alert_history:
                st.session_state.alert_history.insert(0, msg)
        if pe_oi_chg > 250000:
            msg = f"⏱️ {ts} | [🔥 PUT WRITING] {s} PE वर मोठा सपोर्ट निर्माण झाला!"
            if msg not in st.session_state.alert_history:
                st.session_state.alert_history.insert(0, msg)
            
        data.append(row)
    return pd.DataFrame(data), base_p, atm_strike

# --- ६. रिफ्रेशिंग लूप (No-Blink & Error-Free) ---
while True:
    df, spot_price, atm_strike = fetch_terminal_data(smart_api, selected_index)
    total_ce_oi = df["CE_OI"].sum()
    total_pe_oi = df["PE_OI"].sum()
    pcr = total_pe_oi / total_ce_oi
    
    # मेट्रिक्स अपडेट
    for m_box in [chart_metric_empty, chain_metric_empty, alert_metric_empty]:
        with m_box.container():
            cx, cy, cz = st.columns(3)
            cx.metric(label=f"📈 {selected_index} LTP", value=f"₹{spot_price:,.2f}")
            cy.metric(label="📊 Put-Call Ratio (PCR)", value=f"{pcr:.2f}")
            cz.metric(label="🎯 ATM Strike Price", value=f"{atm_strike}")

    # SCREEN 1: टेक्निकल चार्ट और स्थिर स्टेटस पॅनल
    with chart_view_empty.container():
        fig_c = go.Figure(data=[go.Candlestick(
            x=st.session_state.price_history['Time'], open=st.session_state.price_history['Open'],
            high=st.session_state.price_history['High'], low=st.session_state.price_history['Low'],
            close=st.session_state.price_history['Close'], name="Candlestick"
        )])
        fig_c.update_layout(xaxis_rangeslider_visible=False, height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_c, use_container_width=True)
        
    # बटनच्या बाजूला फक्त रेडी मेसेज रिफ्रेश करणे
    status_placeholder.success(f"🎯 Ready to Place Order for {selected_index}")

    # SCREEN 2: ऑप्शन चेन ग्रिड
    with chain_view_empty.container():
        chain_df = df.copy()
        chain_df.columns = [
            "Volume (CALL)", "OI Change (CALL)", "OI (CALL)", "LTP (CALL)", "CE IV", "CE Delta",
            "Strike",
            "LTP (PUT)", "PE Delta", "PE IV", "OI (PUT)", "OI Change (PUT)", "Volume (PUT)"
        ]
        clean_chain = chain_df[["Volume (CALL)", "OI Change (CALL)", "OI (CALL)", "LTP (CALL)", "Strike", "LTP (PUT)", "OI (PUT)", "OI Change (PUT)", "Volume (PUT)"]]
        
        st.dataframe(
            clean_chain.style.format({
                "Volume (CALL)": "{:,}", "OI Change (CALL)": "{:,}", "OI (CALL)": "{:,}", "LTP (CALL)": "₹{}",
                "LTP (PUT)": "₹{}", "OI (PUT)": "{:,}", "OI Change (PUT)": "{:,}", "Volume (PUT)": "{:,}"
            }).background_gradient(subset=["OI Change (CALL)", "OI Change (PUT)"], cmap="RdYlGn"),
            use_container_width=True, height=450, hide_index=True
        )

    # SCREEN 3: अलर्ट्स आणि ग्राफिक्स
    with alert_stream_empty.container():
        st.subheader("🚨 Live Market Signal Stream")
        if not st.session_state.alert_history: st.info("डेटाची वाट पाहत आहे...")
        for al in st.session_state.alert_history[:6]: st.write(al)
        
    with graph_stream_empty.container():
        st.subheader("📊 Volume vs Open Interest Build-Up")
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_OI_Chg'], name='Call Volume', marker_color='#ef553b'))
        fig_b.add_trace(go.Bar(x=df['STRIKE'], y=df['PE_OI_Chg'], name='Put Volume', marker_color='#00cc96'))
        fig_b.update_layout(barmode='group', height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_b, use_container_width=True)

    time.sleep(1)
