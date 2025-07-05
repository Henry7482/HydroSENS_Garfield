import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
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
        # figure & axes 
        fig, ax = plt.subplots(figsize=(16.06, 7.68), dpi=96,
                            facecolor='white')   # white canvas
        ax.set_facecolor('white')                   # white plot area

        # data line
        stats_df[field].plot(
            ax=ax,
            marker='o',
            markersize=8,
            linewidth=4,
            color='#33c3ff'                         # keep bright‐blue line
        )

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
