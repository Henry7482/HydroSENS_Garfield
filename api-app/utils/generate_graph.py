import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
import os

units = {
    "ndvi": "NDVI [-]",
    "temperature": "Temperature [°C]",
    "precipitation": "Precipitation [mm]",
    "curve_number": "Curve Number",
    "soil_fraction": "Soil Fraction",
    "vegetation_fraction": "Vegetation Fraction"
}

def generate_graphs(metrics_data, report_data, graph_output_dir="data/assets/graphs"):
    """
    Generate time series graphs from metrics_data and save them as PNGs.
    For each metric in report_data["metrics"], attach the corresponding graph path under 'graph_image_path'.
    """
    graph_output_dir = Path(graph_output_dir)
    graph_output_dir.mkdir(parents=True, exist_ok=True)
    graph_dir = Path("assets/graphs")

    # Convert metrics_data to DataFrame
    stats_df = pd.DataFrame.from_dict(metrics_data["outputs"], orient="index")
    stats_df.index = pd.to_datetime(stats_df.index)

    # Map metric IDs to graphable field names (if different)
    id_to_field = {
        "ndvi": "ndvi",
        "temperature": "temperature",
        "precipitation": "precipitation",
        "curve_number": "curve-number",
        "soil_fraction": "soil-fraction",
        "vegetation_fraction": "vegetation-fraction"
    }

    for metric in report_data.get("metrics", []):
        metric_id = metric.get("id")
        field = id_to_field.get(metric_id)
        if not field or field not in stats_df.columns:
            print(f"Skipping graph for unknown or missing field '{metric_id}'")
            continue
        
        # Get the data for this metric
        metric_data = stats_df[field].dropna()
        
        # Skip if there's only one data point or no data
        if len(metric_data) <= 1:
            print(f"Skipping linear regression for '{metric_id}' - insufficient data points")
            
        # figure & axes 
        fig, ax = plt.subplots(figsize=(16.06, 7.68), dpi=96,
                            facecolor='white')   # white canvas
        ax.set_facecolor('white')                   # white plot area

        if metric_id == "precipitation":
            ax.set_ylim(bottom=0)
        # data line
        metric_data.plot(
            ax=ax,
            marker='o',
            markersize=8,
            linewidth=4,
            color='#33c3ff'                         # keep bright‐blue line
        )

        # Add linear regression line if we have more than 1 data point
        if len(metric_data) > 1:
            # Convert datetime index to numerical values (days since first date)
            x_datetime = metric_data.index
            x_numeric = (x_datetime - x_datetime[0]).days.values
            y_values = metric_data.values
            
            # Calculate linear regression using the actual time intervals
            slope, intercept = np.polyfit(x_numeric, y_values, 1)
            
            # Generate regression line points using the same time intervals
            regression_line = slope * x_numeric + intercept
            
            # Plot regression line using the datetime index for proper x-axis alignment
            ax.plot(x_datetime, regression_line, 
                   linestyle='--', 
                   linewidth=2, 
                   color='red', 
                   alpha=0.6,
                   label=f'Trend (slope: {slope:.4f})')
            
            # Add legend to show the trend line (positioned above the plot area, left-aligned)
            ax.legend(fontsize=20, bbox_to_anchor=(0, 1.02), loc='lower left')

        # grid: solid black, horizontal only 
        ax.yaxis.grid(True, color='black', linewidth=0.6)   # horizontal lines
        ax.xaxis.grid(False)                                # no vertical lines

        # tidy labels & formatting 
        ax.set_ylabel(units.get(metric_id), fontsize=28)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45, ha='right', fontsize=24)
        plt.yticks(fontsize=24)

        # Optional: hide the top/right spines for a cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fig.tight_layout()

        # save 
        filename = f"{metric_id}.png"
        graph_path = graph_output_dir / filename
        out_graph_path = graph_dir / filename
        fig.savefig(graph_path)           # no transparency → true white background
        plt.close(fig)

        metric["graph_image_path"] = str(out_graph_path)
    return report_data