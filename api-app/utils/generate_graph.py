import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import os

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

        fig, ax = plt.subplots(figsize=(8, 4))
        stats_df[field].plot(ax=ax, marker='o', title=metric["title"])
        ax.set_xlabel("Date")
        ax.set_ylabel(metric["title"])
        ax.grid(True)
        fig.tight_layout()

        filename = f"{metric_id}.png"
        graph_path = graph_output_dir / filename
        out_graph_path = graph_dir / filename
        fig.savefig(graph_path)
        plt.close(fig)

        metric["graph_image_path"] = str(out_graph_path)
    return report_data
