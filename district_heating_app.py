
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(page_title="Prepay Power: District Heating Forecast", layout="wide")
st.markdown("<h1 style='color:#e6007e'>💡 Prepay Power: District Heating Forecast</h1>", unsafe_allow_html=True)

# --- Site Profiles ---
sites = {
    "Barnwell": {
        "area": 22102,
        "u_value": 0.15,
        "indoor_temp": 20,
        "outdoor_temp": 5,
        "system_loss": 0.50,
        "boiler_eff": 0.85,
        "co2_factor": 0.23,
        "elec_price": 0.25,
        "chp_installed": "Yes",
        "chp_th": 44.7,
        "chp_el": 19.965,
        "chp_gas": 67.9,
        "chp_hours": 15,
        "chp_adj": 0.95,
        "hp_installed": "Yes",
        "hp_th": 60,
        "hp_hours": 9,
        "hp_cop": 4
    },
    "Custom": {}
}

# --- Select Site ---
site = st.selectbox("Select Site", list(sites.keys()))
defaults = sites.get(site, {})

# --- Input Columns ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🔧 Input Parameters")
    area = st.number_input("Area (m²)", value=defaults.get("area", 0))
    indoor_temp = st.number_input("Indoor Temp (°C)", value=defaults.get("indoor_temp", 20))
    outdoor_temp = st.number_input("Outdoor Temp (°C)", value=defaults.get("outdoor_temp", 5))
    u_value = st.number_input("U-Value (W/m²K)", value=defaults.get("u_value", 0.15))
    system_loss = st.slider("System Loss (%)", 0, 100, int(defaults.get("system_loss", 0.5) * 100)) / 100
    boiler_eff = st.slider("Boiler Efficiency (%)", 1, 100, int(defaults.get("boiler_eff", 85))) / 100
    co2_factor = st.number_input("CO₂ Emission Factor (kg/kWh)", value=defaults.get("co2_factor", 0.23))
    elec_price = st.number_input("Electricity Price (€/kWh)", value=defaults.get("elec_price", 0.25))

with col2:
    st.subheader("⚙️ System Configuration")
    chp_on = st.radio("CHP Installed?", ["Yes", "No"], index=0 if defaults.get("chp_installed") == "Yes" else 1)
    chp_th = st.number_input("CHP Thermal Output (kW)", value=defaults.get("chp_th", 0), disabled=chp_on == "No")
    chp_el = st.number_input("CHP Elec Output (kW)", value=defaults.get("chp_el", 0), disabled=chp_on == "No")
    chp_gas = st.number_input("CHP Gas Input (kW)", value=defaults.get("chp_gas", 0), disabled=chp_on == "No")
    chp_hours = st.slider("CHP Hours/Day", 0, 24, value=defaults.get("chp_hours", 0), disabled=chp_on == "No")
    chp_adj = st.slider("CHP Adjustment (%)", 0, 100, int(defaults.get("chp_adj", 0.95) * 100), disabled=chp_on == "No") / 100
    hp_on = st.radio("Heat Pump Installed?", ["Yes", "No"], index=0 if defaults.get("hp_installed") == "Yes" else 1)
    hp_th = st.number_input("HP Thermal Output (kW)", value=defaults.get("hp_th", 0), disabled=hp_on == "No")
    hp_hours = st.slider("HP Hours/Day", 0, 24, value=defaults.get("hp_hours", 0), disabled=hp_on == "No")
    hp_cop = st.number_input("HP COP", value=defaults.get("hp_cop", 0), disabled=hp_on == "No")

# --- Core Calculations ---
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24 / 1000) * (1 + system_loss)
chp_thermal = chp_th * chp_adj * chp_hours if chp_on == "Yes" else 0
chp_electric = chp_el * chp_adj * chp_hours if chp_on == "Yes" else 0
chp_gas_input = chp_gas * chp_adj * chp_hours if chp_on == "Yes" else 0
hp_thermal = hp_th * hp_hours if hp_on == "Yes" else 0
hp_electric = hp_thermal / hp_cop if hp_on == "Yes" and hp_cop > 0 else 0
boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff if boiler_eff > 0 else 0

# --- Monthly Forecast ---
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
    heat = (u_value * area * (indoor_temp - temp) * 24 / 1000) * (1 + system_loss) * days
    chp_m = chp_th * chp_adj * chp_hours * days if chp_on == "Yes" else 0
    hp_m = hp_th * hp_hours * days if hp_on == "Yes" else 0
    hp_el = hp_m / hp_cop if hp_on == "Yes" and hp_cop > 0 else 0
    boiler = max(0, heat - chp_m - hp_m)
    gas = (boiler / boiler_eff if boiler_eff > 0 else 0) + (chp_gas * chp_adj * chp_hours * days if chp_on == "Yes" else 0)
    co2 = gas * co2_factor

    forecast.append({
        "Month": m, "Heating (kWh)": heat, "CHP (kWh)": chp_m, "HP (kWh)": hp_m,
        "Boiler (kWh)": boiler, "HP Elec (kWh)": hp_el, "CO₂ Emissions (kg)": co2
    })

df = pd.DataFrame(forecast).set_index("Month")
st.subheader("📆 Monthly Forecast")
st.dataframe(df.style.format("{:.0f}"))

# --- Forecast Line Chart with All Outputs ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df["Heating (kWh)"], mode='lines+markers',
                         name='Heating', line=dict(color='#e6007e', width=3)))
fig.add_trace(go.Scatter(x=df.index, y=df["CHP (kWh)"], mode='lines+markers',
                         name='CHP Output', line=dict(color='orange', dash='dot')))
fig.add_trace(go.Scatter(x=df.index, y=df["HP (kWh)"], mode='lines+markers',
                         name='HP Output', line=dict(color='green', dash='dash')))
fig.add_trace(go.Scatter(x=df.index, y=df["Boiler (kWh)"], mode='lines+markers',
                         name='Boiler Output', line=dict(color='purple')))
fig.update_layout(title="Monthly Energy Output by Source",
                  xaxis_title="Month", yaxis_title="Energy (kWh)",
                  legend_title="Energy Source", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)
