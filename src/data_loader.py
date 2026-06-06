import requests
import numpy as np
import pandas as pd
import time
from typing import List, Dict, Any
import streamlit as st

class GeoSpatialDataLoader:
    """
    Handles geographical calculations, route sampling via OpenStreetMap (OSRM),
    and secure communication layers with the Weather-AI developer endpoints.
    """
    def __init__(self, api_key: str = "wai_ef09dc.4393e8b27a6ea0c165140aa335714518bd85c08fd0ae39b7", base_url: str = "https://weather-ai.co"):
        #self.api_key = st.secrets.get("WEATHER_AI_KEY", api_key)
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        # Reliable geocoding coordinate reference fallback for the MVP testing
        self.city_coordinates = {
            "nairobi": {"lat": -1.2921, "lon": 36.8219},
            "mombasa": {"lat": -4.0435, "lon": 39.6682},
            "nakuru": {"lat": -0.3031, "lon": 36.0800},
            "kisumu": {"lat": -0.0917, "lon": 34.7680}
        }

    def generate_route_waypoints(self, start_city: str, end_city: str, sample_size: int = 8) -> List[Dict[str, Any]]:
        """
        Queries the Open Source Routing Machine (OSRM) to capture polyline data
        and performs downsampling to select equidistant operational nodes.
        Fixes the malformed API route path syntax.
        """
        start_norm = start_city.strip().lower()
        end_norm = end_city.strip().lower()
        
        if start_norm not in self.city_coordinates or end_norm not in self.city_coordinates:
            raise ValueError(f"Coordinates missing for selected sectors. Registered: {list(self.city_coordinates.keys())}")
            
        start_coords = self.city_coordinates[start_norm]
        end_coords = self.city_coordinates[end_norm]
        
        # OSRM expects: /route/v1/driving/lon,lat;lon,lat?options
        # Removed trailing slash after 'driving' to fix the malformed string parsing error
        osrm_url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{start_coords['lon']},{start_coords['lat']};{end_coords['lon']},{end_coords['lat']}"
            f"?overview=full&geometries=geojson"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (WeatherAICopilotLogisticsApp/1.0; CandidateAssessment)"
        }
        
        try:
            response = requests.get(osrm_url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' not in data or not data['routes']:
                raise KeyError("No valid driving route variations returned by the routing cluster.")
                
            all_coordinates = data['routes'][0]['geometry']['coordinates']
            
            # Execute deterministic downsampling along the coordinate polyline length
            indices = np.linspace(0, len(all_coordinates) - 1, sample_size, dtype=int)
            sampled_points = [all_coordinates[i] for i in indices]
            
            return [
                {
                    "node_index": idx + 1,
                    "lon": pt[0],
                    "lat": pt[1]
                }
                for idx, pt in enumerate(sampled_points)
            ]
            
        except Exception as e:
            print(f"[WARN] OSRM engine unreachable or rejected parsing ({e}). Dropping to linear fallback.")
            return self._generate_fallback_linear_points(start_coords, end_coords, sample_size)

    def _generate_fallback_linear_points(self, start: dict, end: dict, samples: int) -> List[Dict[str, Any]]:
        """Fallback interpolation mechanism if OSRM endpoint is timed out."""
        lats = np.linspace(start['lat'], end['lat'], samples)
        lons = np.linspace(start['lon'], end['lon'], samples)
        return [{"node_index": i + 1, "lon": lons[i], "lat": lats[i]} for i in range(samples)]

    def fetch_weather_metrics(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Performs network ingestion against Weather-AI endpoints for explicit spatial nodes.
        Features graceful error catchers and mirrors standard corporate API payload standards.
        """
        # Formulate your targeting endpoint based on documentation layout
        # (e.g., target endpoint might be /v1/forecast or /v2/standard)
        target_endpoint = f"{self.base_url}/v1/forecast" 

        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric"
            #"key": self.api_key
        }

        # FIX: Re-routing authentication token from query string into standard headers

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "WeatherAICopilotLogisticsApp/1.0"
        }
        
        try:
     # In a production environment, this would be the actual API call to fetch real-time data
            response = requests.get(target_endpoint, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            payload = response.json()

            # print(f"DEBUG PAYLOAD FOR NODE: {payload}")
            daily_list = payload.get("daily", [])

            if daily_list and isinstance(daily_list, list):
                # Target the primary day array block element
                target_day = daily_list[0]
                
                # Extracting keys found in your terminal logs printout
                wind = float(target_day.get("wind_max", 15.0))
                precip = float(target_day.get("precipitation_sum", 0.0))
                
                # Dynamic Visibility Modeling: 
                # If precipitation_sum is high, safety visibility falls from 10km down to 3km
                vis = max(3.0, round(10.0 - (precip * 0.5), 1))
            else:
                # Fallback parameters if the daily block layout structural shape differs
                wind, precip, vis = 15.0, 0.0, 10.0
                
            return {
                "wind_speed_kph": wind,
                "precipitation_mm": precip,
                "visibility_km": vis
            }
           # return {
           #     "wind_speed_kph": payload.get("wind_speed", payload.get("wind", 15.0)),
            #    "precipitation_mm": payload.get("precipitation", payload.get("rain", 0.0)),
             #   "visibility_km": payload.get("visibility", 10.0)
            #}
            # Defensive programmatic mock payload mapping real-world variables
            #return {
             #   "wind_speed_kph": round(float(np.random.uniform(12, 58)), 2),
              #  "precipitation_mm": round(float(np.random.uniform(0, 18)), 2),
               # "visibility_km": round(float(np.random.uniform(2, 12)), 2),
                #"lightning_risk": np.random.choice(["Low", "Moderate", "High"])
            #}
        except Exception as e:
            print(f"[WARN] Error fetching metrics for grid [{lat}, {lon}]: {e}")
            return {"wind_speed_kph": 0.0, "precipitation_mm": 0.0, "visibility_km": 10.0, "lightning_risk": "Low"}

    def compile_route_matrix(self, waypoints: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Iterates over generated waypoints and compiles their weather matrices.
        Includes a rate-limiting delay to prevent 429 server blocks.
        """
        route_data = []
        for wp in waypoints:
            # 💡 FIX: Introduce a 0.5-second structural breathing room between endpoint requests
            time.sleep(0.5) 
            
            metrics = self.fetch_weather_metrics(wp['lat'], wp['lon'])
            node_record = {
                "node_index": wp['node_index'],
                "lat": wp['lat'],
                "lon": wp['lon'],
                **metrics
            }
            route_data.append(node_record)
            
        return pd.DataFrame(route_data)