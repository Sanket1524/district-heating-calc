
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(page_title="Prepay Power: District Heating Forecast", layout="wide")
st.markdown("### 🔌 Prepay Power: District Heating Forecast", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("🔧 Input Parameters")
    site = st.selectbox("Select Site", ["Barnwell", "Custom"])
    area = st.number_input("Area (m²)", value=22102 if site == "Barnwell" else 0)
    indoor_temp = st.number_input("Indoor Temp (°C)", value=20)
    outdoor_temp = st.number_input("Outdoor Temp (°C)", value=5)
    u_value = st.number_input("U-Value (W/m²K)", value=0.15)
    system_loss = st.slider("System Loss (%)", 0, 100, 50) / 100
    boiler_eff = st.slider("Boiler Efficiency (%)", 1, 100, 85) / 100
    co2_factor = st.number_input("CO₂ Emission Factor (kg/kWh)", value=0.23)
    elec_price = st.number_input("Electricity Price (€/kWh)", value=0.25)

    st.subheader("CHP Configuration")
    chp_on = st.checkbox("CHP Installed?", value=True)
    chp_th = st.number_input("CHP Thermal Output (kW)", value=44.7, disabled=not chp_on)
    chp_el = st.number_input("CHP Elec Output (kW)", value=19.965, disabled=not chp_on)
    chp_gas = st.number_input("CHP Gas Input (kW)", value=67.9, disabled=not chp_on)
    chp_hours = st.slider("CHP Hours/Day", 0, 24, 15, disabled=not chp_on)
    chp_adj = st.slider("CHP Adjustment (%)", 0, 100, 95, disabled=not chp_on) / 100

    st.subheader("Heat Pump Configuration")
    hp_on = st.checkbox("Heat Pump Installed?", value=True)
    hp_th = st.number_input("HP Thermal Output (kW)", value=60, disabled=not hp_on)
    hp_hours = st.slider("HP Hours/Day", 0, 24, 9, disabled=not hp_on)
    hp_cop = st.number_input("HP COP", value=4.0, disabled=not hp_on)

# --- Core Calculations ---
heat_demand = (u_value * area * (indoor_temp - outdoor_temp) * 24 / 1000) * (1 + system_loss)
chp_thermal = chp_th * chp_adj * chp_hours if chp_on else 0
chp_gas_input = chp_gas * chp_adj * chp_hours if chp_on else 0
hp_thermal = hp_th * hp_hours if hp_on else 0
hp_electric = hp_thermal / hp_cop if hp_on and hp_cop > 0 else 0
boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / boiler_eff if boiler_eff > 0 else 0

# --- Output Panel ---
st.header("📊 Output Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Heat Demand", f"{heat_demand:.2f} kWh/day")
col2.metric("CHP Thermal", f"{chp_thermal:.2f} kWh")
col3.metric("HP Thermal", f"{hp_thermal:.2f} kWh")
col1.metric("Boiler Thermal", f"{boiler_thermal:.2f} kWh")
col2.metric("CHP Gas Input", f"{chp_gas_input:.2f} kWh")
col3.metric("Boiler Gas Input", f"{boiler_gas_input:.2f} kWh")

# --- Monthly Forecast Table ---
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
    chp_m = chp_th * chp_adj * chp_hours * days if chp_on else 0
    hp_m = hp_th * hp_hours * days if hp_on else 0
    hp_el = hp_m / hp_cop if hp_on and hp_cop > 0 else 0
    boiler = max(0, heat - chp_m - hp_m)
    gas = (boiler / boiler_eff if boiler_eff > 0 else 0) + (chp_gas * chp_adj * chp_hours * days if chp_on else 0)
    co2 = gas * co2_factor
    forecast.append({
        "Month": m, "Heating (kWh)": heat, "CHP (kWh)": chp_m, "HP (kWh)": hp_m,
        "Boiler (kWh)": boiler, "HP Elec (kWh)": hp_el, "CO₂ Emissions (kg)": co2
    })

df = pd.DataFrame(forecast).set_index("Month")
st.subheader("📆 Monthly Forecast Table")
st.dataframe(df.style.format("{:.0f}"))

# --- Dynamic Line Chart with Shaded Bands ---
st.subheader("📈 Forecast Trends")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df["Heating (kWh)"], mode='lines+markers', name='Heating', line=dict(color='#e6007e', width=3)))
fig.add_trace(go.Scatter(x=df.index, y=df["CHP (kWh)"], mode='lines', name='CHP Output', line=dict(dash='dot')))
fig.add_trace(go.Scatter(x=df.index, y=df["HP (kWh)"], mode='lines', name='HP Output', line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=df.index, y=df["Boiler (kWh)"], mode='lines', name='Boiler Output'))

fig.update_layout(height=450, template='plotly_white', legend_title_text='Energy Source', margin=dict(l=20, r=20, t=30, b=20))
st.plotly_chart(fig, use_container_width=True)
