
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Prepay Power - District Heating Dashboard", layout="wide")

# Logo and Header
st.image("https://www.prepaypower.ie/sites/default/files/prepay-power-logo_0_0.png", width=160)
st.markdown("## 💡 Prepay Power | District Heating Energy Dashboard")

# Define site options
sites = {
    "Barnwell (CHP only)": {
        "area": 22102, "u": 0.15, "indoor": 20, "outdoor": 5, "loss": 0.5,
        "chp": True, "chp_th": 44.7, "chp_el": 19.965, "chp_gas": 67.9, "chp_hr": 15, "chp_adj": 0.95,
        "hp": False, "hp_th": 0, "hp_hr": 0, "cop": 0
    },
    "Sample Site (HP + CHP)": {
        "area": 25000, "u": 0.17, "indoor": 21, "outdoor": 6, "loss": 0.4,
        "chp": True, "chp_th": 35, "chp_el": 15, "chp_gas": 60, "chp_hr": 12, "chp_adj": 0.90,
        "hp": True, "hp_th": 50, "hp_hr": 8, "cop": 3.5
    },
}

site_name = st.selectbox("🏙️ Select Site", list(sites.keys()))
params = sites[site_name]

# Inputs (with real-time update)
with st.expander("🔧 Configuration", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        area = st.number_input("Area (m²)", value=params["area"])
        indoor = st.number_input("Indoor Temp (°C)", value=params["indoor"])
        outdoor = st.number_input("Outdoor Temp (°C)", value=params["outdoor"])
        u = st.number_input("U-value (W/m²K)", value=params["u"])
        loss = st.slider("System Loss (%)", 0, 100, int(params["loss"] * 100)) / 100
        boiler_eff = st.slider("Boiler Efficiency (%)", 50, 100, 85) / 100
    with col2:
        chp_on = st.checkbox("CHP Installed", value=params["chp"])
        hp_on = st.checkbox("Heat Pump Installed", value=params["hp"])
        chp_th = st.number_input("CHP Thermal Output (kW)", value=params["chp_th"] if chp_on else 0)
        chp_el = st.number_input("CHP Electrical Output (kW)", value=params["chp_el"] if chp_on else 0)
        chp_gas = st.number_input("CHP Gas Input (kW)", value=params["chp_gas"] if chp_on else 0)
        chp_hr = st.slider("CHP Hours/day", 0, 24, params["chp_hr"] if chp_on else 0)
        chp_adj = st.slider("CHP Adjustment Factor (%)", 0, 100, int(params["chp_adj"] * 100 if chp_on else 0)) / 100
        hp_th = st.number_input("HP Thermal Output (kW)", value=params["hp_th"] if hp_on else 0)
        hp_hr = st.slider("HP Hours/day", 0, 24, params["hp_hr"] if hp_on else 0)
        cop = st.number_input("Heat Pump COP", value=params["cop"] if hp_on else 0.01)

# Calculations
heat_demand = u * area * (indoor - outdoor) * 24 / 1000 * (1 + loss)
chp_thermal = chp_th * chp_hr * chp_adj if chp_on else 0
hp_thermal = hp_th * hp_hr if hp_on else 0
boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas = boiler_thermal / boiler_eff if boiler_thermal > 0 else 0

# Output Summary
st.markdown("### 📊 Daily Heat Demand Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Heat Demand (kWh/day)", f"{heat_demand:.2f}")
col2.metric("Boiler Thermal Output", f"{boiler_thermal:.2f} kWh")
col3.metric("Boiler Gas Input", f"{boiler_gas:.2f} kWh")

# Breakdown Chart
st.markdown("### 🔍 Heat Source Breakdown")
source_data = pd.DataFrame({
    "Source": ["CHP", "Heat Pump", "Boiler"],
    "Thermal Output (kWh)": [chp_thermal, hp_thermal, boiler_thermal]
})
st.plotly_chart(px.pie(source_data, names="Source", values="Thermal Output (kWh)", title="Heat Source Share"), use_container_width=True)

# Monthly Forecast
temps = {"Jan":5.0, "Feb":5.5, "Mar":7.0, "Apr":9.0, "May":11.0, "Jun":13.5,
         "Jul":15.0, "Aug":15.0, "Sep":13.0, "Oct":10.0, "Nov":7.0, "Dec":5.5}
days = {"Jan":31, "Feb":28, "Mar":31, "Apr":30, "May":31, "Jun":30,
        "Jul":31, "Aug":31, "Sep":30, "Oct":31, "Nov":30, "Dec":31}
monthly = []
for m in temps:
    h = u * area * (indoor - temps[m]) * 24 / 1000 * (1 + loss)
    th = h * days[m]
    chp = chp_th * chp_hr * chp_adj * days[m] if chp_on else 0
    hp = hp_th * hp_hr * days[m] if hp_on else 0
    blr = max(0, th - chp - hp)
    monthly.append({"Month": m, "Heat Demand": th, "CHP": chp, "HP": hp, "Boiler": blr})

df = pd.DataFrame(monthly)
st.markdown("### 📅 Monthly Forecast")
st.dataframe(df.set_index("Month").style.format("{:.0f}"))

st.plotly_chart(px.bar(df, x="Month", y=["CHP", "HP", "Boiler"], title="Monthly Heat by Source", barmode="stack"), use_container_width=True)
