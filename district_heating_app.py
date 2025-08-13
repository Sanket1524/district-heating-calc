
import streamlit as st
import pandas as pd

# --- Branding ---
st.set_page_config(page_title="Prepay Power - District Heating Dashboard", layout="wide")
st.markdown("<h1 style='color:#e6007e;'>💡 Prepay Power: District Heating Forecast</h1>", unsafe_allow_html=True)

# --- Site Selection ---
sites = {
    "Barnwell": {
        "Area": 22102,
        "Indoor Temp": 20,
        "Outdoor Temp": 5,
        "U-Value": 0.15,
        "System Loss": 0.5,
        "CHP": {"Installed": True, "Thermal": 44.7, "Electric": 19.965, "Gas": 67.9, "Hours": 15, "Adj": 0.95},
        "HP": {"Installed": True, "Thermal": 60, "Hours": 9, "COP": 4.0},
        "Boiler Efficiency": 0.85,
        "Gas Emission": 0.233,
        "Elec Price": 0.25
    },
    "Custom": {}
}

site_choice = st.selectbox("Select Site", list(sites.keys()))
params = sites.get(site_choice, {})

# --- Input Panel ---
st.sidebar.header("🔧 Input Parameters")
area = st.sidebar.number_input("Area (m²)", value=params.get("Area", 20000))
indoor_temp = st.sidebar.number_input("Indoor Temp (°C)", value=params.get("Indoor Temp", 20))
outdoor_temp = st.sidebar.number_input("Outdoor Temp (°C)", value=params.get("Outdoor Temp", 5))
u_value = st.sidebar.number_input("U-Value (W/m²K)", value=params.get("U-Value", 0.15))
system_loss = st.sidebar.slider("System Loss (%)", 0, 100, int(params.get("System Loss", 0.5)*100)) / 100

boiler_eff = st.sidebar.slider("Boiler Efficiency (%)", 50, 100, int(params.get("Boiler Efficiency", 85))) / 100
gas_emission = st.sidebar.number_input("CO₂ Emission Factor (kg/kWh)", value=params.get("Gas Emission", 0.233))
elec_price = st.sidebar.number_input("Electricity Price (€/kWh)", value=params.get("Elec Price", 0.25))

# CHP Section
st.sidebar.subheader("⚙️ CHP")
chp_installed = st.sidebar.checkbox("CHP Installed", value=params.get("CHP", {}).get("Installed", False))
chp_th = st.sidebar.number_input("CHP Thermal Output (kW)", value=params.get("CHP", {}).get("Thermal", 0.0)) if chp_installed else 0
chp_el = st.sidebar.number_input("CHP Electrical Output (kW)", value=params.get("CHP", {}).get("Electric", 0.0)) if chp_installed else 0
chp_gas = st.sidebar.number_input("CHP Gas Input (kW)", value=params.get("CHP", {}).get("Gas", 0.0)) if chp_installed else 0
chp_hours = st.sidebar.slider("CHP Hours/Day", 0, 24, value=params.get("CHP", {}).get("Hours", 0)) if chp_installed else 0
chp_adj = st.sidebar.slider("CHP Adj. Factor (%)", 0, 100, value=int(params.get("CHP", {}).get("Adj", 1.0)*100)) / 100 if chp_installed else 0

# Heat Pump Section
st.sidebar.subheader("⚙️ Heat Pump")
hp_installed = st.sidebar.checkbox("Heat Pump Installed", value=params.get("HP", {}).get("Installed", False))
hp_th = st.sidebar.number_input("Heat Pump Thermal Output (kW)", value=params.get("HP", {}).get("Thermal", 0.0)) if hp_installed else 0
hp_hours = st.sidebar.slider("HP Hours/Day", 0, 24, value=params.get("HP", {}).get("Hours", 0)) if hp_installed else 0
hp_cop = st.sidebar.number_input("HP COP", value=params.get("HP", {}).get("COP", 0.0)) if hp_installed else 0.1

# --- Calculations ---
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24) / 1000 * (1 + system_loss)
chp_thermal = chp_th * chp_adj * chp_hours
chp_electric = chp_el * chp_adj * chp_hours
chp_gas_input = chp_gas * chp_adj * chp_hours

hp_thermal = hp_th * hp_hours
hp_electric = hp_thermal / hp_cop

boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff

total_cost = hp_electric * elec_price
total_emissions = (boiler_gas_input + chp_gas_input) * gas_emission

# --- Dashboard View ---
st.subheader("📊 Output Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Heat Demand", f"{heat_demand:.1f} kWh")
col2.metric("Boiler Gas Input", f"{boiler_gas_input:.1f} kWh")
col3.metric("Total CO₂ Emission", f"{total_emissions:.1f} kg")

col4, col5, col6 = st.columns(3)
col4.metric("CHP Thermal Output", f"{chp_thermal:.1f} kWh")
col5.metric("HP Thermal Output", f"{hp_thermal:.1f} kWh")
col6.metric("Electricity Used by HP", f"{hp_electric:.1f} kWh")

# --- Forecast Table ---
st.markdown("---")
st.subheader("📅 Monthly Forecasting (Temp-based)")
monthly_temps = {
    "Jan": 5, "Feb": 5.5, "Mar": 7, "Apr": 9, "May": 11,
    "Jun": 13.5, "Jul": 15, "Aug": 15, "Sep": 13, "Oct": 10, "Nov": 7, "Dec": 5.5
}
days_in_month = {"Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
                 "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}

forecast = []
for m, temp in monthly_temps.items():
    days = days_in_month[m]
    hd = (u_value * area * (indoor_temp - temp) * 24) / 1000 * (1 + system_loss)
    heat_month = hd * days
    chp_th_m = chp_th * chp_adj * chp_hours * days if chp_installed else 0
    chp_gas_m = chp_gas * chp_adj * chp_hours * days if chp_installed else 0
    hp_th_m = hp_th * hp_hours * days if hp_installed else 0
    hp_el_m = hp_th_m / hp_cop if hp_installed else 0
    boiler_th = max(0, heat_month - chp_th_m - hp_th_m)
    boiler_gas_m = boiler_th / boiler_eff if boiler_th > 0 else 0
    co2 = (boiler_gas_m + chp_gas_m) * gas_emission

    forecast.append({
        "Month": m,
        "Heating (kWh)": heat_month,
        "Boiler Gas (kWh)": boiler_gas_m,
        "CHP Gas (kWh)": chp_gas_m,
        "HP Electricity (kWh)": hp_el_m,
        "CO₂ Emissions (kg)": co2
    })

df = pd.DataFrame(forecast).set_index("Month")
st.dataframe(df.style.format("{:.0f}"))

# --- Optional Summary ---
st.markdown("---")
st.subheader("📌 Annual Summary")
st.write(f"🔺 Annual Heating Demand: **{df['Heating (kWh)'].sum():,.0f} kWh**")
st.write(f"♻️ Total CO₂ Emissions: **{df['CO₂ Emissions (kg)'].sum():,.0f} kg**")
