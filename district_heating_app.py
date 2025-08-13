
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="District Heating Calculator", layout="centered")

st.title("🏠 District Heating Energy Calculator")
st.markdown("Use the panel below to enter parameters and estimate daily heating requirements and fuel breakdown.")

# --- Inputs ---
st.header("1. Input Parameters")
col1, col2 = st.columns(2)

with col1:
    area = st.number_input("Area of Complex (m²)", value=22102)
    indoor_temp = st.number_input("Indoor Temperature (°C)", value=20)
    outdoor_temp = st.number_input("Outdoor Temperature (°C)", value=5)
    u_value = st.number_input("U-Value (W/m²K)", value=0.15)
    system_loss = st.slider("System Loss (%)", min_value=0, max_value=100, value=50) / 100
    boiler_eff = st.slider("Boiler Efficiency (%)", min_value=50, max_value=100, value=85) / 100
    elec_price = st.number_input("Electricity Price (€/kWh)", value=0.25)
    gas_emission = st.number_input("CO₂ Emission Factor (kg/kWh)", value=0.233)

with col2:
    chp_enabled = st.selectbox("Is CHP Installed?", ["Yes", "No"])
    chp_th = st.number_input("CHP Thermal Output (kW)", value=44.7)
    chp_el = st.number_input("CHP Electrical Output (kW)", value=19.965)
    chp_gas = st.number_input("CHP Gas Input (kW)", value=67.9)
    chp_hours = st.slider("CHP Hours/Day", 0, 24, value=15)
    chp_adj = st.slider("CHP Adjustment Factor (%)", 0, 100, value=95) / 100

st.subheader("Heat Pump")
hp_enabled = st.selectbox("Is Heat Pump Installed?", ["Yes", "No"])
hp_th = st.number_input("Heat Pump Thermal Output (kW)", value=60)
hp_hours = st.slider("HP Hours/Day", 0, 24, value=9)
hp_cop = st.number_input("HP COP", value=4.0)

# --- Daily Calculations ---
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24) / 1000 * (1 + system_loss)
chp_thermal = chp_th * chp_adj * chp_hours if chp_enabled == "Yes" else 0
chp_electric = chp_el * chp_adj * chp_hours if chp_enabled == "Yes" else 0
chp_gas_input = chp_gas * chp_adj * chp_hours if chp_enabled == "Yes" else 0

hp_thermal = hp_th * hp_hours if hp_enabled == "Yes" else 0
hp_electric = hp_thermal / hp_cop if hp_enabled == "Yes" and hp_cop else 0

boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff if boiler_thermal > 0 else 0

# --- Output ---
st.header("2. Output Summary")
st.metric("Total Heat Demand (kWh/day)", f"{heat_demand:.2f}")

col1, col2, col3 = st.columns(3)
col1.metric("CHP Heat Output", f"{chp_thermal:.2f} kWh")
col2.metric("HP Heat Output", f"{hp_thermal:.2f} kWh")
col3.metric("Boiler Heat Output", f"{boiler_thermal:.2f} kWh")

col1.metric("CHP Gas Input", f"{chp_gas_input:.2f} kWh")
col2.metric("HP Elec Used", f"{hp_electric:.2f} kWh")
col3.metric("Boiler Gas Input", f"{boiler_gas_input:.2f} kWh")

# --- Chart ---
st.header("3. Heat Source Breakdown")
df = pd.DataFrame({
    'Source': ['CHP', 'Heat Pump', 'Boiler'],
    'Energy (kWh)': [chp_thermal, hp_thermal, boiler_thermal]
})
st.bar_chart(df.set_index("Source"))

# --- Forecasting ---
st.header("4. Forecasting: Monthly & Annual Estimates")
monthly_temps = {
    "Jan": 5.0, "Feb": 5.5, "Mar": 7.0, "Apr": 9.0, "May": 11.0, "Jun": 13.5,
    "Jul": 15.0, "Aug": 15.0, "Sep": 13.0, "Oct": 10.0, "Nov": 7.0, "Dec": 5.5
}
days_in_month = {
    "Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
    "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31
}

forecast = []
for month in monthly_temps:
    temp = monthly_temps[month]
    days = days_in_month[month]
    heat = (u_value * area * (indoor_temp - temp) * 24) / 1000 * (1 + system_loss)
    heat_month = heat * days
    chp_th_m = chp_th * chp_adj * chp_hours * days if chp_enabled == "Yes" else 0
    chp_gas_m = chp_gas * chp_adj * chp_hours * days if chp_enabled == "Yes" else 0
    hp_th_m = hp_th * hp_hours * days if hp_enabled == "Yes" else 0
    hp_el_m = hp_th_m / hp_cop if hp_enabled == "Yes" and hp_cop else 0
    boiler_th = max(0, heat_month - chp_th_m - hp_th_m)
    boiler_gas_m = boiler_th / boiler_eff if boiler_th > 0 else 0
    total_gas = boiler_gas_m + chp_gas_m
    co2 = total_gas * gas_emission
    elec_cost = hp_el_m * elec_price

    forecast.append({
        "Month": month,
        "Heating (kWh)": heat_month,
        "CHP Gas (kWh)": chp_gas_m,
        "Boiler Gas (kWh)": boiler_gas_m,
        "HP Electricity (kWh)": hp_el_m,
        "Electricity Cost (€)": elec_cost,
        "CO₂ Emissions (kg)": co2
    })

forecast_df = pd.DataFrame(forecast).set_index("Month")

st.subheader("📅 Monthly Forecast Table")
st.dataframe(forecast_df.style.format("{:.0f}"))

if st.toggle("Show Forecast Charts"):
    st.bar_chart(forecast_df[["Heating (kWh)", "CO₂ Emissions (kg)"]])
    st.line_chart(forecast_df[["Electricity Cost (€)", "HP Electricity (kWh)"]])

if st.download_button("📥 Download Forecast CSV", data=forecast_df.to_csv(), file_name="district_heating_forecast.csv"):
    st.success("CSV download initiated!")

st.success(f"🏁 Annual Heating: {forecast_df['Heating (kWh)'].sum():,.0f} kWh | Annual CO₂: {forecast_df['CO₂ Emissions (kg)'].sum():,.0f} kg | Annual Electricity Cost: €{forecast_df['Electricity Cost (€)'].sum():,.0f}")
streamlit run district_heating_app.py

