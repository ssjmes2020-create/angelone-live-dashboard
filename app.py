import streamlit as st
import pandas as pd
import numpy as np
import pyotp
import time
from SmartApi import SmartConnect

# डॅशबोर्डची स्क्रीन रुंद (Wide) करणे
st.set_page_config(layout="wide", page_title="Live Option Chain Dashboard")

st.title("📊 Live Option Chain & Greeks Dashboard")
st.caption("Powered by Angel One SmartAPI V2 & Streamlit Cloud")

# --- सेशन्स आणि स्टेट मॅनेजमेंट ---
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []

# --- १. टॉप बार: ड्रॉपडाऊन आणि मुख्य इंडिकेटर्स ---
col_top1, col_top2, col_top3 = st.columns()

with col_top1:
    selected_index = st.selectbox("🎯 इंडेक्स निवडा (Select Index):", ["NIFTY", "BANKNIFTY", "SENSEX"])

# --- २. डॅशबोर्डसाठी डमी डेटा जनरेटर (जोपर्यंत API कनेक्ट होत नाही) ---
def generate_live_data(index_name):
    base_price = 24500 if index_name == "NIFTY" else (52000 if index_name == "BANKNIFTY" else 80000)
    strikes = [base_price + (i * (50 if index_name == "NIFTY" else 100)) for i in range(-7, 8)]
    
    data = []
    for s in strikes:
        distance = (s - base_price) / (50 if index_name == "NIFTY" else 100)
        ce_delta = round(0.5 - (distance * 0.05), 2)
        pe_delta = round(-0.5 - (distance * 0.05), 2)
        
        row = {
            "CE_OI": np.random.randint(10, 50) * 100000,
            "CE_OI_Chg": np.random.randint(-5, 15) * 50000,
            "CE_Vol": np.random.randint(50, 500) * 1000,
            "CE_Delta": max(0.01, min(0.99, ce_delta)),
            "CE_Gamma": 0.02,
            "CE_Theta": -12.5,
            "CE_Vega": 18.2,
            "CE_LTP": round(max(5, 150 - (distance * 35)), 2),
            "STRIKE": s,
            "PE_LTP": round(max(5, 150 + (distance * 35)), 2),
            "PE_Vega": 18.2,
            "PE_Theta": -11.8,
            "PE_Gamma": 0.02,
            "PE_Delta": max(-0.99, min(-0.01, pe_delta)),
            "PE_Vol": np.random.randint(50, 500) * 1000,
            "PE_OI_Chg": np.random.randint(-5, 15) * 50000,
            "PE_OI": np.random.randint(10, 50) * 100000,
        }
        data.append(row)
    return pd.DataFrame(data), base_price

df, spot_price = generate_live_data(selected_index)

total_ce_oi = df["CE_OI"].sum()
total_pe_oi = df["PE_OI"].sum()
pcr = total_pe_oi / total_ce_oi

with col_top2:
    st.metric(label=f"📈 {selected_index} Spot Price", value=f"₹{spot_price}")
with col_top3:
    st.metric(label="📊 Overall PCR (Put-Call Ratio)", value=f"{pcr:.2f}", 
              delta="Bullish Trend" if pcr > 1.2 else ("Bearish Trend" if pcr < 0.7 else "Neutral/Sideways"))

st.divider()

# --- ३. मुख्य लेआउट: अलर्ट्स विंडो आणि ऑप्शन चेन मॅट्रिक्स ---
col_alerts, col_matrix = st.columns()

with col_alerts:
    st.subheader("🚨 Live Smart Alerts")
    if st.button("🔄 सिम्युलेट अलर्ट (Test Alert)"):
        timestamp = time.strftime('%H:%M:%S')
        random_row = df.sample(1).iloc[0]
        if np.random.choice([True, False]):
            st.session_state.alert_history.insert(0, f"⏱️ {timestamp} - [🚨 SHORT COVERING] {selected_index} {int(random_row['STRIKE'])} CE मधून वेगाने OI कमी होत आहे! (तेजीचे संकेत)")
        else:
            st.session_state.alert_history.insert(0, f"⏱️ {timestamp} - [🚨 OPERATOR ENTRY] {selected_index} {int(random_row['STRIKE'])} PE वर मोठा व्हॉल्यूम स्पाईक! (मजबूत सपोर्ट)")
    
    for alert in st.session_state.alert_history[:5]:
        st.info(alert)

with col_matrix:
    st.subheader(f"📊 Option Chain Matrix ({selected_index})")
    
    display_df = df[[
        "CE_OI", "CE_OI_Chg", "CE_Vol", "CE_Delta", "CE_Gamma", "CE_Theta", "CE_Vega", "CE_LTP",
        "STRIKE",
        "PE_LTP", "PE_Vega", "PE_Theta", "PE_Gamma", "PE_Delta", "PE_Vol", "PE_OI_Chg", "PE_OI"
    ]]
    
    st.dataframe(
        display_df.style.format({
            "CE_OI": "{:,}", "CE_OI_Chg": "{:,}", "CE_Vol": "{:,}", "CE_LTP": "₹{}",
            "PE_OI": "{:,}", "PE_OI_Chg": "{:,}", "PE_Vol": "{:,}", "PE_LTP": "₹{}",
            "STRIKE": "{}"
        }),
        use_container_width=True,
        height=500
    )

# --- ४. ऑटो-रिफ्रेश मॅकेनिझम ---
time.sleep(1)
st.rerun()
