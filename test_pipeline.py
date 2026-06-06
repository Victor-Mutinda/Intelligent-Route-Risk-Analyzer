# test_pipeline.py
import streamlit as st
from src.data_loader import GeoSpatialDataLoader
from src.risk_model import RouteRiskEvaluator

def test_full_pipeline():
    print("🚀 Running Full Integrated Pipeline Test...\n")
    
    # Init modules
    loader = GeoSpatialDataLoader()
    evaluator = RouteRiskEvaluator()
    
    # Generate route segments
    waypoints = loader.generate_route_waypoints("nairobi", "kisumu", sample_size=6)
    
    # Fetch Weather
    raw_matrix = loader.compile_route_matrix(waypoints)
    
    # Run Analytics Risk Calculations
    processed_df = evaluator.calculate_risk_profiles(raw_matrix)
    summary = evaluator.compile_fleet_summary(processed_df)
    
    print("📊 --- INTEGRATED ANALYTICS FRAME ---")
    print(processed_df[['node_index', 'wind_speed_kph', 'risk_score', 'operational_status']])
    
    print("\n📦 --- CONTROL ROOM EXECUTIVE SUMMARY ---")
    for key, val in summary.items():
        print(f"🔹 {key.replace('_', ' ').title()}: {val}")

if __name__ == "__main__":
    test_full_pipeline()