---
Title: Intelligent Route Risk Analyzer
sdk: streamlit
app_file: app.py
app_port: 8501
tags:
- streamlit
pinned: false
short_description: Intelligent model that gives insight on users on transit.
sdk_version: 1.58.0
---

Intelligent Route Risk Analyzer

This is an intelligent predictive geospatial Route Risk analyzer dashboard built for 
long-haul operations across major commercial transit corridors across the continent. 
This application interfaces with the live Weather-AI Engine, models highway waypoints 
using the Open Source Routing Machine (OSRM), 
and runs a localized weighted hazard assessment matrix to compute continuous point-to-point risk profiles for people(Drivers) in Transit.

Live Hosted Application on Hugging Face Spaces: [https://huggingface.co/spaces/VictorMutinda/Intelligent_Route_Risk_Analyzer]

System Architecture & Methodology

The application follows a decoupled three-tier software design pattern:
  1.Geospatial Processing Layer (src/data_loader.py)
This Translates physical logistics sectors (e.g., Nairobi to Mombasa) into absolute geographic waypoint polylines.

  2.Predictive Analytics Layer (src/risk_model.py)
It Normalizes distinct weather factors. The factors have used are windspeed, precipitation and visibility index.
It computes continuous risk indices via a weighted combination matrix, and simulates contextual intelligence layers.

  3.Presentation & Dashboard Layer (app.py)
An interactive web application presenting real-time maps, visual progress tracking scales, and clear fleet status alerts.
The status alerts are:
      1. 'CLEAR FOR DEPARTURE'
      2. 'PROCEED WITH CAUTION'
      3. 'HOLD / REROUTE'

        ARCHITECHTURE / Data Flow

        [---User Input ---] // These are the Start and Destination Location. For this demo. We have Mombasa, Nairobi, Nakuru AND Kisumu
                |
        [---GeoCoding & Route Engine ---] // Fetches path co-ordinates(Latitude & Longitude).
                |
        [---Weather Data Ingestion ---] // Queries Weather-AI API per waypoint and fetches weather info for that waypoint
                |
        [---ML Risk Scoring Engine---] // Evaluates anomalies & hazardous alerts on the weather extracted from each waypoint. And provides meaningful info 
                |
        [---Interactive Frontend UI---] // Displays a dynamic route map with 6 marked waypoints along the route. Each waypoint has a safety rating.

How To Run And Test Locally

1. Clone the Code Base
   Run the following:
   . git clone https://huggingface.co/spaces/VictorMutinda/Intelligent_Route_Risk_Analyzer
   . cd Intelligent_Route_Risk_Analyzer
2. Configure Your Virtual Environment
   Run the following:
    . pip install -r requirements.txt
3. Setup Your API key
    1. At the root of the project create a folder called ".streamlit"
    2. In the folder create a file called "secrets.toml"
    3. In side the file add your api key as this
        WEATHER_AI_KEY = "paste your weather-ai.co API Key here"

4. Execute the Local Automated Test Pipeline
   Run the following:
    . streamlit run test_pipeline.py
5. Launch the Dashboard Interface
   Run the following:
    . streamlit run app.py
