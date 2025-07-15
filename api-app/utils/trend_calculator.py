import pandas as pd
import numpy as np

def calculate_trends(metrics_data):
    """
    Calculate trends for each metric using linear regression.
    Returns a dictionary with metric trends in the format expected by the report.
    """
    # Convert metrics_data to DataFrame
    stats_df = pd.DataFrame.from_dict(metrics_data["outputs"], orient="index")
    stats_df.index = pd.to_datetime(stats_df.index)
    
    # Map metric IDs to field names (matching generate_graph.py)
    id_to_field = {
        "ndvi": "ndvi",
        "temperature": "temperature", 
        "precipitation": "precipitation",
        "curve_number": "curve-number",
        "soil_fraction": "soil-fraction",
        "vegetation_fraction": "vegetation-fraction"
    }
    
    trends = {}
    
    for metric_id, field in id_to_field.items():
        if field not in stats_df.columns:
            continue
            
        # Get the data for this metric
        metric_data = stats_df[field].dropna()
        
        # Skip if there's only one data point or no data
        if len(metric_data) <= 1:
            trends[metric_id] = {
                "percent": 0.0,
                "uptrend": True
            }
            continue
            
        # Convert datetime index to numerical values (days since first date)
        x_datetime = metric_data.index
        x_numeric = (x_datetime - x_datetime[0]).days.values
        y_values = metric_data.values
        
        # Calculate linear regression using the actual time intervals
        slope, intercept = np.polyfit(x_numeric, y_values, 1)
        
        # Calculate percentage change from regression line's start to end value
        start_value = intercept  # Value at first time point (x=0)
        end_value = slope * x_numeric[-1] + intercept  # Value at last time point
        
        # For fraction/proportion metrics (0-1 range), use percentage point change
        # For other metrics, use traditional percentage change
        fraction_metrics = ["ndvi", "soil-fraction", "vegetation-fraction"]
        
        if field in fraction_metrics:
            # Use percentage point change (multiply by 100 to convert to percentage points)
            percentage_change = (end_value - start_value) * 100
        else:
            # Use traditional percentage change for other metrics
            if start_value != 0:
                percentage_change = ((end_value - start_value) / abs(start_value)) * 100
            else:
                # Handle case where start_value is 0
                percentage_change = 0.0 if end_value == 0 else (100.0 if end_value > 0 else -100.0)
        
        trends[metric_id] = {
            "percent": round(abs(percentage_change), 2),
            "uptrend": percentage_change >= 0
        }
    
    return trends