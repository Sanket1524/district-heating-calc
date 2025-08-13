
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from PIL import Image
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="District Heating Dashboard", layout="wide")

# --- BRANDING ---
st.image("prepay_power_logo.png", width=150)
st.markdown("<h1 style='color:#e6007e;'>🔌 Prepay Power – District Heating Dashboard</h1>", unsafe_allow_html=True)

st.markdown("Easily simulate energy needs & forecast heating outputs by site. Built for **Prepay Power** to support sustainable operations.")

# --- MULTI-SITE CONFIG ---
site_profiles = {
    "Site A - Barnwell (CHP Only)": {
        "area": 22102, "indoor_temp": 20, "outdoor_temp": 5, "u_value": 0.15,
        "system_loss": 0.5, "boiler_eff": 0.85, "chp_installed": True,
        "chp_th": 44.7, "chp_el": 19.965, "chp_gas": 67.9, "chp_hours": 15, "chp_adj": 0.95,
        "hp_installed": False, "hp_th": 0, "hp_hours": 0, "hp_cop": 0
    },
    "Site B - Mixed (CHP + HP)": {
        "area": 20000, "indoor_temp": 20, "outdoor_temp": 5, "u_value": 0.18,
        "system_loss": 0.4, "boiler_eff": 0.88, "chp_installed": True,
        "chp_th": 40, "chp_el": 18, "chp_gas": 62, "chp_hours": 12, "chp_adj": 0.9,
        "hp_installed": True, "hp_th": 50, "hp_hours": 9, "hp_cop": 3.5
    }
}

site = st.selectbox("📍 Select Site", list(site_profiles.keys()))
profile = site_profiles[site]

# --- INPUTS ---
with st.expander("⚙️ Input Parameters", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        area = st.number_input("Area (m²)", value=profile['area'])
        indoor_temp = st.number_input("Indoor Temp (°C)", value=profile['indoor_temp'])
        outdoor_temp = st.number_input("Outdoor Temp (°C)", value=profile['outdoor_temp'])
        u_value = st.number_input("U-Value (W/m²K)", value=profile['u_value'])
        system_loss = st.slider("System Loss (%)", 0, 100, int(profile['system_loss']*100)) / 100
        boiler_eff = st.slider("Boiler Efficiency (%)", 50, 100, int(profile['boiler_eff']*100)) / 100

    with col2:
        chp_enabled = st.checkbox("CHP Installed", value=profile["chp_installed"])
        chp_th = st.number_input("CHP Thermal Output (kW)", value=profile["chp_th"] if chp_enabled else 0)
        chp_el = st.number_input("CHP Electrical Output (kW)", value=profile["chp_el"] if chp_enabled else 0)
        chp_gas = st.number_input("CHP Gas Input (kW)", value=profile["chp_gas"] if chp_enabled else 0)
        chp_hours = st.slider("CHP Hours/Day", 0, 24, value=profile["chp_hours"] if chp_enabled else 0)
        chp_adj = st.slider("CHP Adjustment Factor (%)", 0, 100, value=int(profile["chp_adj"]*100) if chp_enabled else 0) / 100

st.markdown("---")
st.markdown("### 🔋 Heat Pump Settings")
hp_enabled = st.checkbox("Heat Pump Installed", value=profile["hp_installed"])
col1, col2, col3 = st.columns(3)
with col1:
    hp_th = st.number_input("HP Thermal Output (kW)", value=profile["hp_th"] if hp_enabled else 0)
with col2:
    hp_hours = st.slider("HP Hours/Day", 0, 24, value=profile["hp_hours"] if hp_enabled else 0)
with col3:
    hp_cop = st.number_input("HP COP", value=profile["hp_cop"] if hp_enabled else 0)

# --- CALCULATIONS ---
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24) / 1000 * (1 + system_loss)
chp_thermal = chp_th * chp_adj * chp_hours if chp_enabled else 0
chp_gas_input = chp_gas * chp_adj * chp_hours if chp_enabled else 0
hp_thermal = hp_th * hp_hours if hp_enabled else 0
hp_electric = hp_thermal / hp_cop if hp_enabled and hp_cop else 0
boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff if boiler_thermal > 0 else 0

# --- OUTPUT SECTION ---
st.markdown("---")
st.markdown("## 📈 Daily Heat Breakdown")
col1, col2, col3 = st.columns(3)
col1.metric("Total Heat Demand", f"{heat_demand:.0f} kWh/day")
col2.metric("Boiler Heat Output", f"{boiler_thermal:.0f} kWh")
col3.metric("HP Electricity Used", f"{hp_electric:.0f} kWh")

col1, col2, col3 = st.columns(3)
col1.metric("CHP Heat Output", f"{chp_thermal:.0f} kWh")
col2.metric("CHP Gas Input", f"{chp_gas_input:.0f} kWh")
col3.metric("Boiler Gas Input", f"{boiler_gas_input:.0f} kWh")

st.plotly_chart(px.pie(values=[chp_thermal, hp_thermal, boiler_thermal],
                       names=["CHP", "Heat Pump", "Boiler"],
                       title="Heat Supply Distribution"))

# --- FORECASTING ---
monthly_temps = {
    "Jan": 5.0, "Feb": 5.5, "Mar": 7.0, "Apr": 9.0, "May": 11.0, "Jun": 13.5,
    "Jul": 15.0, "Aug": 15.0, "Sep": 13.0, "Oct": 10.0, "Nov": 7.0, "Dec": 5.5
}
days_in_month = {
    "Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
    "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31
}

forecast = []
for m in monthly_temps:
    temp = monthly_temps[m]
    days = days_in_month[m]
    h = (u_value * area * (indoor_temp - temp) * 24) / 1000 * (1 + system_loss)
    h_month = h * days
    chp_m = chp_th * chp_adj * chp_hours * days if chp_enabled else 0
    hp_m = hp_th * hp_hours * days if hp_enabled else 0
    b_m = max(0, h_month - chp_m - hp_m)
    forecast.append({"Month": m, "Demand (kWh)": h_month, "CHP (kWh)": chp_m, "HP (kWh)": hp_m, "Boiler (kWh)": b_m})

df_forecast = pd.DataFrame(forecast).set_index("Month")

st.markdown("## 📅 Monthly Forecast")
st.dataframe(df_forecast.style.format("{:.0f}"))

st.bar_chart(df_forecast)

