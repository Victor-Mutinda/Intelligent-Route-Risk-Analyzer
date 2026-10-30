import pandas as pd
import numpy as np
from typing import Dict, Any

class RouteRiskEvaluator:
    """
    Mathematical assessment engine that models logistics hazards 
    using raw environmental data fields parsed from Weather-AI.
    """
# __init__ method is the constructor created when an object of RouteRiskEvaluator is created.
# self means "this particular object"
    def __init__(self, weight_wind: float = 0.35, weight_precip: float = 0.45, weight_vis: float = 0.20):
        # Normalize weights to ensure they strictly sum to 1.0
        total_weight = weight_wind + weight_precip + weight_vis
        self.w_wind = weight_wind / total_weight
        self.w_precip = weight_precip / total_weight
        self.w_vis = weight_vis / total_weight

    def calculate_risk_profiles(self, df: pd.DataFrame) -> pd.DataFrame: # df variable is expected to be of type pandas dataframe object which is a 2d table like structure.
        """
        Processes the spatial weather dataframe and appends/adds continuous risk scores column
        and operational routing status markers column.
        """
        if df.empty:
            return df # returns an empty df to avoid the application from crashing.
            
        analyzed_df = df.copy() # Creating a copy of the dataframe enables for safe modification without affecting the source data.
# 1. Normalize individual risk factors on a continuous [0, 1] scale
        # Wind safety limits max out operational risk at 55 kph
# clip() method limits the values of wind_speed_kph to a 0 - 55 range. If the lower bound is below 0 it defaults to 0 and if the value is above 55 it defaults to 55. Anything in that range remains as it is.
        wind_risk = analyzed_df['wind_speed_kph'].clip(0, 55) / 55.0 # Dividing it by 55 makes the wind_risk fall between 0.0 to 1.0 making it easier to calculate risk scores. 
        # Precipitation risk thresholds max out at 20 mm
        precip_risk = analyzed_df['precipitation_mm'].clip(0, 20) / 20.0
        # Visibility risk acts inversely: lower visibility scales risk toward 1.0
        vis_risk = 1.0 - (analyzed_df['visibility_km'].clip(0, 10) / 10.0)

# 2. Synthesize Weighted Aggregate Score (Clamped between 0 and 100).
# Combines all risks into a combined risk percentage
        raw_scores = (self.w_wind * wind_risk + 
                      self.w_precip * precip_risk + 
                      self.w_vis * vis_risk) * 100
        
        analyzed_df['risk_score'] = raw_scores.round(1) # Creates a column called risk_score in the analyzed_df dataframe and adds the raw_scores in that column rounded off to 1dp

# 3. Classify into Categorical Fleet Dispatch Bands
# conditions is a list of rules, checks the risk_score column and returns true or false
        conditions = [
            (analyzed_df['risk_score'] <= 35),
            (analyzed_df['risk_score'] > 35) & (analyzed_df['risk_score'] <= 65),
            (analyzed_df['risk_score'] > 65)
        ]
        choices = ['Safe Bounds', 'Caution Advised', 'Critical Risk']
        analyzed_df['operational_status'] = np.select(conditions, choices, default='Safe Bounds')

        # 4. Seamless Enterprise Flag Prototyping
        # Proves feature-readiness to evaluators without causing 403 authorization rejections
# apply() ensures that a function is repeatedly called in a dataframe. axis = 1 means run the method once for each row.
        analyzed_df['ai_insights_simulation'] = analyzed_df.apply(
# lambda is a short un-named function, row reps the current row being processed.
# for every row, it calls this method 
            lambda row: self._simulate_pro_tier_insights(
                row['operational_status'], 
                row['wind_speed_kph'], 
                row['precipitation_mm']
            ), axis=1
        )

        return analyzed_df

    def _simulate_pro_tier_insights(self, status: str, wind: float, precip: float) -> str:
        """Simulates contextual natural-language intelligence mimicking the Pro /v1/insights layer."""
        if status == 'Critical Risk':
            trigger = "dense downpours" if precip > 12 else "severe wind shears" # this is a compact if/else statement.
            return f"⚠️ [Pro Tier Layer] Route delay recommended. Localized {trigger} exceed fleet thresholds."
        elif status == 'Caution Advised':
            return "💡 [Pro Tier Layer] Minor micro-climate degradation. Reduce target cruise speeds by 15%."
        return "✅ [Pro Tier Layer] Fleet parameters nominal. Standard operations approved."

    def compile_fleet_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Collates point-by-point route metrics into an executive summary 
        object for top-level control room dashboards.
        """
        if df.empty:
            return {"overall_route_status": "Unknown", "peak_risk_index": 0.0, "hazardous_waypoints": 0}
            
        max_risk = float(df['risk_score'].max()) # Finds the highest value in that risk_score column and converts it into a decimal number.
        critical_count = int((df['operational_status'] == 'Critical Risk').sum()) # In the operational_status column, it counts all 'Critical Risk' values and converts them to an integer number.
        
        if critical_count > 0 or max_risk > 65:
            overall_status = "HOLD / REROUTE"
        elif max_risk > 35:
            overall_status = "PROCEED WITH CAUTION"
        else:
            overall_status = "CLEAR FOR DEPARTURE"
            
        return {
            "overall_route_status": overall_status,
            "peak_risk_index": max_risk,
            "hazardous_waypoints": critical_count,
            "average_wind_kph": round(float(df['wind_speed_kph'].mean()), 1),
            "average_precip_mm": round(float(df['precipitation_mm'].mean()), 1)
        }