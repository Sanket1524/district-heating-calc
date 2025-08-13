
import streamlit as st
import pandas as pd

st.set_page_config(page_title="District Heating Calculator", layout="wide")
st.title("🔥 Prepay Power: District Heating Forecast")

# Sidebar Inputs
st.sidebar.header("🛠 Input Parameters")
area = st.sidebar.number_input("Area (m²)", value=22102)
indoor_temp = st.sidebar.number_input("Indoor Temp (°C)", value=20)
outdoor_temp = st.sidebar.number_input("Outdoor Temp (°C)", value=5)
u_value = st.sidebar.number_input("U-Value (W/m²K)", value=0.15)
system_loss = st.sidebar.slider("System Loss (%)", 0, 100, value=50) / 100
boiler_eff = st.sidebar.slider("Boiler Efficiency (%)", 0, 100, value=85) / 100
co2_emission = st.sidebar.number_input("CO₂ Emission Factor (kg/kWh)", value=0.23)
elec_price = st.sidebar.number_input("Electricity Price (€/kWh)", value=0.25)

# Heat Pump Inputs
st.sidebar.subheader("♨️ Heat Pump")
hp_enabled = st.sidebar.selectbox("HP Installed?", ["Yes", "No"])
hp_th = st.sidebar.number_input("HP Thermal Output (kW)", value=60 if hp_enabled == "Yes" else 0)
hp_hours = st.sidebar.slider("HP Hours/Day", 0, 24, value=9 if hp_enabled == "Yes" else 0)
hp_cop = st.sidebar.number_input("HP COP", value=4.0 if hp_enabled == "Yes" else 1.0)

# CHP Inputs
st.sidebar.subheader("⚙️ CHP")
chp_enabled = st.sidebar.selectbox("CHP Installed?", ["Yes", "No"])
chp_th = st.sidebar.number_input("CHP Thermal Output (kW)", value=44.7 if chp_enabled == "Yes" else 0)
chp_el = st.sidebar.number_input("CHP Elec Output (kW)", value=19.965 if chp_enabled == "Yes" else 0)
chp_gas = st.sidebar.number_input("CHP Gas Input (kW)", value=67.9 if chp_enabled == "Yes" else 0)
chp_hours = st.sidebar.slider("CHP Hours/Day", 0, 24, value=15 if chp_enabled == "Yes" else 0)
chp_adj = st.sidebar.slider("CHP Adj. Factor (%)", 0, 100, value=95 if chp_enabled == "Yes" else 0) / 100

# Calculations
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24) / 1000 * (1 + system_loss)
hp_thermal = hp_th * hp_hours if hp_enabled == "Yes" else 0
hp_elec = hp_thermal / hp_cop if hp_enabled == "Yes" and hp_cop != 0 else 0
chp_thermal = chp_th * chp_hours * chp_adj if chp_enabled == "Yes" else 0
chp_electric = chp_el * chp_hours * chp_adj if chp_enabled == "Yes" else 0
chp_gas_input = chp_gas * chp_hours * chp_adj if chp_enabled == "Yes" else 0

boiler_thermal = max(0, heat_demand - hp_thermal - chp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff if boiler_eff != 0 else 0

if boiler_eff == 0 and boiler_thermal > 0:
    st.warning("⚠️ Boiler efficiency is set to 0%. Set a realistic value to avoid incorrect results.")

# Outputs
st.subheader("📊 Output Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Heat Demand", f"{heat_demand:.2f} kWh/day")
col2.metric("CHP Thermal", f"{chp_thermal:.2f} kWh")
col3.metric("Heat Pump Thermal", f"{hp_thermal:.2f} kWh")

col1, col2, col3 = st.columns(3)
col1.metric("Boiler Thermal", f"{boiler_thermal:.2f} kWh")
col2.metric("Boiler Gas Input", f"{boiler_gas_input:.2f} kWh")
col3.metric("CHP Gas Input", f"{chp_gas_input:.2f} kWh")
