import streamlit as st
import pandas as pd

st.set_page_config(page_title="Aviation Tools", layout="centered")
st.title("🛫 Aviation Calculator Suite")

# Tabs
tab1, tab2 = st.tabs(["Pressure Altitude Calculator", "Takeoff Performance Calculator"])

# ---------------------------
# Tab 1: Pressure Altitude
# ---------------------------
with tab1:
    st.header("🛬 Pressure Altitude Calculator")

    @st.cache_data
    def load_airport_data():
        return pd.read_csv("airports.csv")

    airport_data = load_airport_data()

    def get_airport_info(icao_code):
        result = airport_data[airport_data['ident'] == icao_code.upper()]
        if not result.empty:
            elevation = result.iloc[0]['elevation_ft']
            name = result.iloc[0]['name']
            if pd.notna(elevation):
                return float(elevation), name
        return None, None

    def calculate_pressure_altitude(elevation_ft, qnh_hpa):
        return elevation_ft + (1013.25 - qnh_hpa) * 30

    icao = st.text_input("Enter ICAO Code (e.g., EDDF, KJFK)").upper()
    qnh = st.number_input("Enter QNH (hPa)", min_value=800.0, max_value=1100.0, value=1013.25, step=0.01)

    if icao and qnh:
        elevation, name = get_airport_info(icao)
        if elevation is not None:
            pressure_alt = calculate_pressure_altitude(elevation, qnh)
            st.success(f"Airport: {name} ({icao})")
            st.write(f"Elevation: {elevation:.1f} ft")
            st.write(f"Pressure Altitude: {pressure_alt:.1f} ft")
        else:
            st.error("ICAO code not found or missing elevation.")

# ---------------------------
# Tab 2: Takeoff Performance
# ---------------------------
with tab2:
    st.header("🛫 Takeoff Performance Calculator")

    files = {
        '1157': 'takeoff_1157kg_clean.csv',
        '1134': 'takeoff_1134kg_clean.csv',
        '1111': 'takeoff_1111kg_clean.csv'
    }

    def load_all_data():
        data = {}
        for weight, file in files.items():
            df = pd.read_csv(file, encoding='utf-8')
            df.rename(columns={'Pressure Altitude [ft]': 'Pressure Altitude (ft)'}, inplace=True)
            df['Pressure Altitude (ft)'] = pd.to_numeric(df['Pressure Altitude (ft)'], errors='coerce')
            data[int(weight)] = df
        return data

    def find_bounds(values, target):
        values = sorted(values)
        lower = max([v for v in values if v <= target], default=min(values))
        upper = min([v for v in values if v >= target], default=max(values))
        return lower, upper

    def interpolate(value1, value2, point1, point2, target_point):
        if point1 == point2:
            return value1
        return value1 + (value2 - value1) * (target_point - point1) / (point2 - point1)

    def apply_conditions(row, wind, slope, surface):
        row = row.copy()
        row['Distance (m)'] += wind + slope + surface
        return row

    data = load_all_data()
    weight_options = sorted(data.keys(), reverse=True)

    weight = st.selectbox("Select Takeoff Weight (kg)", weight_options)
    pa_input = st.number_input("Enter Pressure Altitude (ft)", min_value=0, max_value=10000, value=0, step=100)

    wind_corr = st.number_input("Wind Correction (m)", value=0)
    slope_corr = st.number_input("Slope Correction (m)", value=0)
    surface_corr = st.number_input("Surface Correction (m)", value=0)

    if weight and pa_input is not None:
        df = data[weight]
        pa_values = df['Pressure Altitude (ft)'].dropna().unique()
        lower, upper = find_bounds(pa_values, pa_input)
        row_low = df[df['Pressure Altitude (ft)'] == lower].iloc[0]
        row_up = df[df['Pressure Altitude (ft)'] == upper].iloc[0]

        dist_low = apply_conditions(row_low, wind_corr, slope_corr, surface_corr)['Distance (m)']
        dist_up = apply_conditions(row_up, wind_corr, slope_corr, surface_corr)['Distance (m)']
        final_dist = interpolate(dist_low, dist_up, lower, upper, pa_input)

        st.write(f"Interpolated Takeoff Distance: **{final_dist:.1f} m**")
