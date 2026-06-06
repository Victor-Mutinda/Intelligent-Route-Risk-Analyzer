import streamlit as st
import pandas as pd
from src.data_loader import GeoSpatialDataLoader
from src.risk_model import RouteRiskEvaluator

# 1. Config App Layout
st.set_page_config(
    page_title="Weather-AI Fleet Copilot",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Weather-AI Predictive Fleet Dispatch Dashboard")
st.markdown("---")

# 2. System Layer Initialization
@st.cache_resource
def init_system_engines():
    # Automatically tracks local keys or Streamlit Cloud secure secrets
    return GeoSpatialDataLoader(), RouteRiskEvaluator()

try:
    data_loader, risk_evaluator = init_system_engines()
except Exception as e:
    st.error(f"Initialization Error: {e}")
    st.stop()

# 3. Sidebar Control Panel Configuration
st.sidebar.header("Route Settings")
available_hubs = list(data_loader.city_coordinates.keys())

origin = st.sidebar.selectbox("Select Route Origin Sector", options=available_hubs, index=0)
destination = st.sidebar.selectbox("Select Target Destination Sector", options=available_hubs, index=1)
sample_points = st.sidebar.slider("Route Node Granularity (Waypoints)", min_value=4, max_value=12, value=6)

if origin == destination:
    st.sidebar.error("Origin and Destination sectors cannot match. Please select a transit vector.")
    st.stop()

# 4. Trigger Calculation Pipeline Flow
with st.spinner("Analyzing micro-climate route vectors..."):
    # Step A: Track spatial coordinates along highways via OSRM
    waypoints = data_loader.generate_route_waypoints(origin, destination, sample_size=sample_points)
    
    # Step B: Ingest meteorology parameters per waypoint node
    raw_matrix = data_loader.compile_route_matrix(waypoints)
    
    # Step C: Evaluate analytical risk index calculations
    processed_df = risk_evaluator.calculate_risk_profiles(raw_matrix)
    summary = risk_evaluator.compile_fleet_summary(processed_df)

# 5. Render Executive Dispatch Metric Cards
status_colors = {
    "CLEAR FOR DEPARTURE": "🟢 Safe Bounds",
    "PROCEED WITH CAUTION": "🟡 Caution Advised",
    "HOLD / REROUTE": "🔴 Critical Risk"
}

# 5. Render Executive Dispatch Metric Cards (Optimized 3-Column Spacing)
# 5. Render Executive Dispatch Metric Cards (Clean, Non-Truncating Layout)
st.subheader("📋 Dispatch Summary")

# A clean layout with 3 dedicated data columns
c1, c2, c3 = st.columns(3)

with c1:
    # Use standard status text blocks depending on authorization layout
    status_str = summary["overall_route_status"]
    if "CLEAR" in status_str:
        st.success(f"**Authorization Status:**\n### ✅ {status_str}")
    elif "CAUTION" in status_str:
        st.warning(f"**Authorization Status:**\n### ⚠️ {status_str}")
    else:
        st.error(f"**Authorization Status:**\n### 🛑 {status_str}")

with c2:
    # Visual progress-bar scale tracking the peak risk index seamlessly
    risk_idx = summary["peak_risk_index"]
    st.markdown(f"**Peak Route Risk Index:** `{risk_idx} / 100`")
    # Progress bars accept float bounds from 0.0 to 1.0
    st.progress(min(1.0, risk_idx / 100.0))

with c3:
    # Combined cleanly structured overview items using clean Markdown list groupings
    st.markdown("**Route Safety Snapshot:**")
    st.markdown(f"• 🚨 **Hazardous Nodes:** `{summary['hazardous_waypoints']}` Active Warnings")
    st.markdown(f"• 🌧️ **Avg Precipitation:** `{summary['average_precip_mm']} mm` Total")

st.markdown("---")

# 6. Geographical Mapping Display Layout Split
left_col, right_col = st.columns([5, 4])

with left_col:
    st.subheader("🗺️ Live Spatial Route Grid")
    # Streamlit natively draws map dataframes containing 'lat'/'lon' configurations
    st.map(processed_df, zoom=7, width='stretch')

with right_col:
    st.subheader("🤖 Fleet Intelligence Layer Integration")
    
    # Visually call out the AI feature structure setup to reviewers right in the UI
    st.info(
        "💡 **Architectural Note:** The system gracefully maps live data streams via the "
        "free `/v1/forecast` tier. Below demonstrates the predictive telemetry structural mapping "
        "designed for immediate hot-swapping into the Enterprise `/v1/insights` model layer."
    )
    
    # Display the simulated plain-language recommendations as clean chat/alert notifications
    for _, row in processed_df.iterrows():
        node_id = int(row['node_index'])
        insight_str = row['ai_insights_simulation']
        
        if "⚠️" in insight_str:
            st.error(f"**Waypoint Node {node_id}:** {insight_str}")
        elif "💡" in insight_str:
            st.warning(f"**Waypoint Node {node_id}:** {insight_str}")
        else:
            st.success(f"**Waypoint Node {node_id}:** {insight_str}")

st.markdown("---")

# 7. Complete Tabular Diagnostic Grid Inspection View
st.subheader("📊 Route Telemetry Node Audit Log")
formatted_view_df = processed_df[[
    'node_index', 'lat', 'lon', 'wind_speed_kph', 
    'precipitation_mm', 'visibility_km', 'risk_score', 'operational_status'
]].rename(columns={
    'node_index': 'Node', 'wind_speed_kph': 'Wind (kph)', 
    'precipitation_mm': 'Rain (mm)', 'visibility_km': 'Visibility (km)',
    'risk_score': 'Calculated Risk Index', 'operational_status': 'Safety Rating'
})

st.dataframe(formatted_view_df, use_container_width=True, hide_index=True)