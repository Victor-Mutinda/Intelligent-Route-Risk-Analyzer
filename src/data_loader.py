import requests
import numpy as np
import pandas as pd
import time
from typing import List, Dict, Any
import streamlit as st

class GeoSpatialDataLoader: 
    # Colon is used to signal that everything indented below belongs to that class.
    """
    Handles geographical calculations, route sampling via OpenStreetMap (OSRM),
    and secure communication layers with the Weather-AI developer endpoints.
    """
    # This is a constructor method runs automatically when you create an object.
    # self is included as part of the arguments since its used to specify the instance of the class.
    # Allowing for modification and access for an objects attribute data
    def __init__(self, base_url: str = "https://weather-ai.co"):  
        if "WEATHER_AI_KEY" in st.secrets:      
            self.api_key =  st.secrets["WEATHER_AI_KEY"]
        else:
            raise KeyError( # KeyError is an exception thats raised when a dictionary key doesnt exist in a collection
# Streamlit automatically parses the secrets.toml file and converts its into a Dictionary.
# Therefore to access content in the .toml file, you use key-value functionalities/logic. If key isnt found thats why you handle the error with a KeyError exception.                
                "Critical Error: API key is not being retrieved"
            )
        self.base_url = base_url.rstrip('/')
# Reliable geocoding coordinate reference fallback for the MVP testing
# city_coordinates is a dictionary that contains keys which store names of counties and values which store the coordinates-lat&long of those county key
        self.city_coordinates = {
# outer dictionary has cities as the keys that are mapped to
# nested dictionary as the value. The nested dict has lat and long keys.
            "nairobi": {"lat": -1.2921, "lon": 36.8219},
            "mombasa": {"lat": -4.0435, "lon": 39.6682},
            "nakuru": {"lat": -0.3031, "lon": 36.0800},
            "kisumu": {"lat": -0.0917, "lon": 34.7680}
        }
# This method takes arguments and returns a list of dictionaries with String Keys and any data type values.
# The sample_size variable has a default 8 value meaning the sample_size argument is optional.
# You can pass whatever int value you want in the sample_size but the default is always 8.
    def generate_route_waypoints(self, start_city: str, end_city: str, sample_size: int = 8) -> List[Dict[str, Any]]:
        """
        Queries the Open Source Routing Machine (OSRM) to capture polyline data
        and performs downsampling to select equidistant operational nodes.
        Fixes the malformed API route path syntax.
        """
        start_norm = start_city.strip().lower() # This is done since city_coordinates dictionary the key elements are the cities and are in lowercase and no whitespaces.
        end_norm = end_city.strip().lower()
# if..not in.. statement checks the start_norm(city) if its a key available in the city_coordinates dictionary.
        if start_norm not in self.city_coordinates or end_norm not in self.city_coordinates:
            raise ValueError(f"Coordinates missing for selected sectors. Registered: {list(self.city_coordinates.keys())}")
# By using the key elements i.e star &end_norm we can get the value elements in the city_coordinates dictionary
# value = dict[key]
        start_coords = self.city_coordinates[start_norm]
        end_coords = self.city_coordinates[end_norm]
        
        # OSRM expects: /route/v1/driving/lon,lat;lon,lat?options
        # Removed trailing slash after 'driving' to fix the malformed string parsing error
        osrm_url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{start_coords['lon']},{start_coords['lat']};{end_coords['lon']},{end_coords['lat']}"
            f"?overview=full&geometries=geojson"
# ? shows the start of the query parameters,which are used to send additional requests to the API.
#overview=full requests the full detailed route geometry.
#geometries=geojson specifies that the path returned by API should be a GeoJSON object
        )
# The headers below defines a dict that set a User-agent header(key) which identifies your app to the API.
# The rest of the string is - Mozilla(is used to show that this request comes from a standard web browser)
# WeatherAiCopit identifies the name of the app and after the semicolon CandidateAssessment is used to identify the context of use for the request.
        headers = {
            "User-Agent": "Mozilla/5.0 (WeatherAICopilotLogisticsApp/1.0; CandidateAssessment)"
        }
        
        try:
# this below sends a HTTP GET request
            response = requests.get(osrm_url, headers=headers, timeout=5)
# Raise_for_status method raises an exception(http exception error) if a request fails.
            response.raise_for_status()
# If request is successful, the JSON response is converted to DICTIONARY by the json() method
            data = response.json()
# Checks if routes key is in the data dict.            
            if 'routes' not in data or not data['routes']:
                raise KeyError("No valid driving route variations returned by the routing cluster.")
# In the data dictionary, in the routes key, the first list item is a dict with geometry as key with a nested dictionary which contains coordinates as a key with a list of coordinates along that route as the value elements.
            all_coordinates = data['routes'][0]['geometry']['coordinates']
            
# Execute deterministic downsampling along the coordinate polyline length
# linspace is used to evenly separate values over a specified interval
            indices = np.linspace(0, len(all_coordinates) - 1, sample_size, dtype=int)

            sampled_points = [all_coordinates[i] for i in indices]
            
            return [
                {
                    "node_index": idx + 1,
                    "lon": pt[0],
                    "lat": pt[1]
                }
# for loop, uses idx to store the count/index which starts at 0. pt is an array/list variable used to hold the coordinates.
# enumerate is used to retrieves an element from a list and its corresponding index position
                for idx, pt in enumerate(sampled_points)
            ]
# exception below catches any errors such as network,corrupted JSON etc logs them and ensure app handles them gracefully   
        except Exception as e:
            print(f"[WARN] OSRM engine unreachable or rejected parsing ({e}). Dropping to linear fallback.")
            return self._generate_fallback_linear_points(start_coords, end_coords, sample_size)
# presence of two underscores __ before a method name signifys its a private method. Access is restricted to be used by the class only.
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
# params dict holds the query parameters the API needs for a certain request
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "ai": "false"
            #"key": self.api_key
        }

        # FIX: Re-routing authentication token from query string into standard headers

        headers = {
# uniquely identifies your request. Authorization header(key) has different security methods. In this case we're using Bearer method.
# 'Bearer' keyword is helps the receiving server understand the type of security making it easy to decode that request. 
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "WeatherAICopilotLogisticsApp/1.0" # uniquely identifies the client/application to the API host
        }

        try:
# An actual API call to fetch real-time data.
# request.get() sends a http get request to the specified API
            response = requests.get(target_endpoint, params=params, headers=headers, timeout=5)
# raises a http exception error if the reqeust fails
            response.raise_for_status()
# the JSON response is converted to a python dictionary
            payload = response.json()

# in the payload dict, using the get()method and passing the 'daily' key element inorder to return the values associated with the daily key
# if the daily key doesnt exist or has no values, it defaults to an empty list.
            daily_list = payload.get("daily", []) 
# get method returns the values paired to that key in the way they were stored in that dict. 
#In this case the values were stored as a list structure.

            if daily_list and isinstance(daily_list, list):
# First the 'if daily_list' evaluates if the variable has elements or empty. 'isinstance' checks if the 'daily_list' is a list.
                # Target the primary day array block element
                target_day = daily_list[0] # Reason for using the first element/dictionary in that list is because we want to access the immediate days' weather forecast data(today).
                
# Extracts and converts the wind and precip values to floats from their respective keys in the dict. If the keys are empty or non-existent the values default to 15 or 0.0 respectively.
                wind = float(target_day.get("wind_max", 15.0))
                precip = float(target_day.get("precipitation_sum", 0.0))
                
# Dynamic Visibility Modeling: This formula uses only Precipitation to calculate visibility. The formula is not ideal because there are other factors that affect visibility such as fog,mist,smoke 
# The formula below sets the minimum value as 3. Anything below 3 will be returned as 3.
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
        #except Exception as e:
         #   print(f"[WARN] Error fetching metrics for grid [{lat}, {lon}]: {e}")
          #  return {"wind_speed_kph": 0.0, "precipitation_mm": 0.0, "visibility_km": 10.0, "lightning_risk": "Low"}

        except Exception as e:
            # Check if the error is a 429 rate-limit to log a clean, professional status alert instead of a messy traceback
            if "429" in str(e):
                print(f"[API Rate-Shield] Node [{lat}, {lon}]: Core Sandbox Token rate-limited for today. Activating dynamic local fallback simulation.")
            else:
                print(f"[WARN] Ingestion anomaly for node [{lat}, {lon}]: {e}")
                
            # Keep your reliable fallback metrics intact to preserve dashboard operations
            import numpy as np
            return {
                "wind_speed_kph": round(float(np.random.uniform(12.0, 30.0)), 1),
                "precipitation_mm": round(float(np.random.uniform(0.0, 4.0)), 1),
                "visibility_km": round(float(np.random.uniform(7.0, 10.0)), 1)
            }
        
    def _resolve_waypoint_name(self, start_city: str, end_city: str, current_idx: int, total_nodes: int) -> str:
        """
        Dynamically estimates realistic highway station and town checkpoint names 
        along Kenya's primary transit vectors based on route progression.
        """
        start_norm = start_city.strip().lower()
        end_norm = end_city.strip().lower()
        
        corridors = {
            # key is a tuple. A tuple is ordered and immutable collection of elements. Values are lists of strings
            ("nairobi", "mombasa"): ["Nairobi Hub", "Athi River Checkpoint", "Sultan Hamud", "Makindu Station", "Mtito Andei", "Manyani Gate", "Voi Transit Point", "Maungu Corridor", "Mariakani Toll", "Mombasa Terminal"],
            ("mombasa", "nairobi"): ["Mombasa Terminal", "Mariakani Toll", "Maungu Corridor", "Voi Transit Point", "Manyani Gate", "Mtito Andei", "Makindu Station", "Sultan Hamud", "Athi River Checkpoint", "Nairobi Hub"],
            ("nairobi", "nakuru"): ["Nairobi Hub", "Limuru Escarpment", "Uplands Station", "Naivasha Flat", "Gilgil Weighbridge", "Nakuru Hub"],
            ("nakuru", "nairobi"): ["Nakuru Hub", "Gilgil Weighbridge", "Naivasha Flat", "Uplands Station", "Limuru Escarpment", "Nairobi Hub"],
            ("nairobi", "kisumu"): ["Nairobi Hub", "Limuru Escarpment", "Naivasha Junction", "Nakuru Hub", "Njoro Turnoff", "Molo Forest", "Kericho Tea Belt", "Awasi Bypass", "Kisumu Terminal"],
            ("kisumu", "nairobi"): ["Kisumu Terminal", "Awasi Bypass", "Kericho Tea Belt", "Molo Forest", "Njoro Turnoff", "Nakuru Hub", "Naivasha Junction", "Limuru Escarpment", "Nairobi Hub"],
            ("nakuru", "mombasa"): ["Nakuru Hub", "Gilgil", "Naivasha", "Limuru", "Nairobi Transit", "Sultan Hamud", "Mtito Andei", "Voi Checkpoint", "Mariakani", "Mombasa Terminal"],
            ("mombasa", "nakuru"): ["Mombasa Terminal", "Mariakani", "Voi Checkpoint", "Mtito Andei", "Sultan Hamud", "Nairobi Transit", "Limuru", "Naivasha", "Gilgil", "Nakuru Hub"],
            ("kisumu", "mombasa"): ["Kisumu Terminal", "Kericho", "Nakuru Hub", "Naivasha", "Nairobi Bypass", "Sultan Hamud", "Mtito Andei", "Voi Checkpoint", "Mariakani", "Mombasa Terminal"],
            ("mombasa", "kisumu"): ["Mombasa Terminal", "Mariakani", "Voi Checkpoint", "Mtito Andei", "Sultan Hamud", "Nairobi Bypass", "Naivasha", "Nakuru Hub", "Kericho", "Kisumu Terminal"]
        }
# pair is a tuple that stores the normalized start and end city names        
        pair = (start_norm, end_norm)
# if statement is checking if the key(elements in pair) is in the dict 
        if pair in corridors:
            landmarks = corridors[pair] # Retrieves all values(list of way points along that route) mapped to the key in a dict
# Based on the route selected and the total nodes selected. linspace will divide the whole route evenly based on the total waypoints passed and returns the index position for the selected waypoints/nodes
            target_idx = int(np.linspace(0, len(landmarks) - 1, total_nodes)[current_idx])

            return landmarks[target_idx] # based on the chosen waypoints, the waypoints are retrieved based on their index position
            
        if current_idx == 0:
            return f"{start_city.title()} Hub"
        elif current_idx == total_nodes - 1:
            return f"{end_city.title()} Terminal"
        else:
            return f"Sector Checkpoint Corridor {current_idx + 1}"

    def compile_route_matrix(self, waypoints: List[Dict[str, Any]], start_city: str = "nairobi", end_city: str = "mombasa") -> pd.DataFrame:
        """
        Iterates over generated waypoints and compiles their weather matrices.
        Includes a rate-limiting delay and dynamic name-resolution parameters.
        """
        route_data = [] # initialized empty list.
        total_nodes = len(waypoints)
        
        for idx, wp in enumerate(waypoints): # enumerate is used to retrieve an element tog with its index position in a list. 
            time.sleep(0.5) # pauses the execution of the loop for half a second before next iteration begins
            
            metrics = self.fetch_weather_metrics(wp['lat'], wp['lon']) # fetch_weather_metrics() method returns a dict storing weather data for each waypoint in every iteration
            
            # Resolve the specific highway location name string natively
            location_name = self._resolve_waypoint_name(start_city, end_city, idx, total_nodes)
            
            node_record = {
                "node_index": wp['node_index'],
                "location_name": location_name, # Injects the clean landmark name text
                "lat": wp['lat'],
                "lon": wp['lon'],
                **metrics # unpacks the metrics dict merging all its key-value elements to this dict
            }
            route_data.append(node_record) # In every iteration, a node_record which is a dict will be added to the route_data list.
# route_data will contain a list of dictionary for each waypoint(node_record).
            
        return pd.DataFrame(route_data) # Converts the route_data list to a pandas dataframe.