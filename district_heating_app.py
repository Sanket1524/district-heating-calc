
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="District Heating Dashboard", layout="wide")

st.markdown(
    "<h1 style='color:#e6007e;'>🔥 Prepay Power – District Heating Energy Dashboard</h1>",
    unsafe_allow_html=True
)

# --- Sidebar Site Selection ---
st.sidebar.header("🏢 Select Site")
sites = {
    "Barnwell": {
        "area": 22102, "indoor_temp": 20, "outdoor_temp": 5, "u_value": 0.15, "system_loss": 0.5,
        "chp_enabled": True, "chp_th": 44.7, "chp_el": 19.965, "chp_gas": 67.9, "chp_hours": 15, "chp_adj": 0.95,
        "hp_enabled": True, "hp_th": 60, "hp_hours": 9, "hp_cop": 4.0,
        "boiler_eff": 0.85, "gas_emission": 0.233
    },
    "Site B": {
        "area": 18000, "indoor_temp": 21, "outdoor_temp": 6, "u_value": 0.18, "system_loss": 0.45,
        "chp_enabled": False, "chp_th": 0, "chp_el": 0, "chp_gas": 0, "chp_hours": 0, "chp_adj": 0,
        "hp_enabled": True, "hp_th": 70, "hp_hours": 8, "hp_cop": 3.8,
        "boiler_eff": 0.87, "gas_emission": 0.233
    }
}

selected_site = st.sidebar.selectbox("Choose a site:", list(sites.keys()))
params = sites[selected_site]

# --- Calculations ---
heat_demand = (params['u_value'] * params['area'] * (params['indoor_temp'] - params['outdoor_temp']) * 24) / 1000 * (1 + params['system_loss'])

chp_thermal = params['chp_th'] * params['chp_adj'] * params['chp_hours'] if params['chp_enabled'] else 0
chp_electric = params['chp_el'] * params['chp_adj'] * params['chp_hours'] if params['chp_enabled'] else 0
chp_gas_input = params['chp_gas'] * params['chp_adj'] * params['chp_hours'] if params['chp_enabled'] else 0

hp_thermal = params['hp_th'] * params['hp_hours'] if params['hp_enabled'] else 0
hp_electric = hp_thermal / params['hp_cop'] if params['hp_enabled'] and params['hp_cop'] else 0

boiler_thermal = max(0, heat_demand - chp_thermal - hp_thermal)
boiler_gas_input = boiler_thermal / params['boiler_eff'] if params['boiler_eff'] else 0

total_gas = chp_gas_input + boiler_gas_input
co2_emissions = total_gas * params['gas_emission']

# --- Layout ---
st.subheader("📊 Daily Energy Breakdown")

output_data = pd.DataFrame({
    "Source": ["CHP", "Heat Pump", "Boiler"],
    "Thermal Output (kWh/day)": [chp_thermal, hp_thermal, boiler_thermal]
})

fig = px.bar(output_data, x="Source", y="Thermal Output (kWh/day)",
             color="Source", text_auto=True,
             color_discrete_map={"CHP": "#fcbf49", "Heat Pump": "#81b29a", "Boiler": "#e07a5f"})
fig.update_layout(title="Daily Thermal Energy Output by Source",
                  title_font_size=18, height=400, margin=dict(t=50, b=30))

st.plotly_chart(fig, use_container_width=True)

# --- Summary ---
st.subheader("Summary")
st.markdown(f"""
• Total Heat Demand: {heat_demand:.0f} kWh/day  
• CHP Electricity: {chp_electric:.0f} kWh/day  
• Total Gas Used: {total_gas:.0f} kWh/day  
• Estimated CO₂ Emissions: {co2_emissions:.0f} kg/day
""")
