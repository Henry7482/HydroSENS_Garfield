import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Avoid matplotlib in Docker: savefig() hangs on linux/amd64 emulated images.
WIDTH, HEIGHT = 1542, 737
DATA_COLOR = "#33c3ff"
TREND_COLOR = "#cc3333"
GRID_COLOR = "#000000"
BG_COLOR = "#ffffff"

units = {
    "ndvi": "NDVI [-]",
    "temperature": "Temperature [°C]",
    "precipitation": "Precipitation [mm]",
    "curve_number": "Curve Number",
    "soil_fraction": "Soil Fraction",
    "vegetation_fraction": "Vegetation Fraction",
}

ID_TO_FIELD = {
    "ndvi": "ndvi",
    "temperature": "temperature",
    "precipitation": "precipitation",
    "curve_number": "curve-number",
    "soil_fraction": "soil-fraction",
    "vegetation_fraction": "vegetation-fraction",
}


def _load_font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _plot_bounds():
    return {
        "left": 140,
        "right": WIDTH - 50,
        "top": 70,
        "bottom": HEIGHT - 120,
    }


def _scale_x(index: int, count: int, left: int, right: int) -> float:
    if count <= 1:
        return (left + right) / 2
    return left + index * (right - left) / (count - 1)


def _scale_y(value: float, y_min: float, y_max: float, top: int, bottom: int) -> float:
    if y_max == y_min:
        return (top + bottom) / 2
    return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)


def _draw_chart(
    dates,
    values,
    ylabel: str,
    output_path: Path,
    *,
    bar_chart: bool = False,
):
    bounds = _plot_bounds()
    left, right = bounds["left"], bounds["right"]
    top, bottom = bounds["top"], bounds["bottom"]

    values = np.asarray(values, dtype=float)
    y_min = 0.0 if bar_chart else float(np.min(values))
    y_max = float(np.max(values))
    if bar_chart:
        y_max = max(1.0, y_max * 1.2)
    elif y_max == y_min:
        y_min -= 0.5
        y_max += 0.5
    else:
        padding = (y_max - y_min) * 0.08
        y_min -= padding
        y_max += padding

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    title_font = _load_font(28)
    tick_font = _load_font(22)
    legend_font = _load_font(20)

    # Horizontal grid + y tick labels
    for i in range(6):
        t = i / 5
        y_val = y_min + t * (y_max - y_min)
        y_px = _scale_y(y_val, y_min, y_max, top, bottom)
        draw.line([(left, y_px), (right, y_px)], fill=GRID_COLOR, width=1)
        draw.text((20, y_px - 10), f"{y_val:.2f}", fill="black", font=tick_font)

    count = len(values)
    points = []
    for i, value in enumerate(values):
        x_px = _scale_x(i, count, left, right)
        y_px = _scale_y(value, y_min, y_max, top, bottom)
        points.append((x_px, y_px))

    if bar_chart:
        bar_width = max(12, (right - left) / max(count, 1) * 0.55)
        for (x_px, y_px), value in zip(points, values):
            draw.rectangle(
                [
                    x_px - bar_width / 2,
                    y_px,
                    x_px + bar_width / 2,
                    bottom,
                ],
                fill=DATA_COLOR,
            )
    else:
        if len(points) > 1:
            draw.line(points, fill=DATA_COLOR, width=4)
        for x_px, y_px in points:
            r = 8
            draw.ellipse(
                [x_px - r, y_px - r, x_px + r, y_px + r],
                fill=DATA_COLOR,
                outline=DATA_COLOR,
            )

    if count > 1:
        x_numeric = np.array(
            [(pd.Timestamp(d) - pd.Timestamp(dates[0])).days for d in dates],
            dtype=float,
        )
        slope, intercept = np.polyfit(x_numeric, values, 1)
        trend_points = [
            (
                _scale_x(0, count, left, right),
                _scale_y(intercept, y_min, y_max, top, bottom),
            ),
            (
                _scale_x(count - 1, count, left, right),
                _scale_y(
                    slope * x_numeric[-1] + intercept,
                    y_min,
                    y_max,
                    top,
                    bottom,
                ),
            ),
        ]
        draw.line(trend_points, fill=TREND_COLOR, width=2)
        draw.text(
            (left, 20),
            f"Trend (slope: {slope:.4f})",
            fill=TREND_COLOR,
            font=legend_font,
        )

    # X labels
    for i, date in enumerate(dates):
        x_px = _scale_x(i, count, left, right)
        label = pd.Timestamp(date).strftime("%Y-%m-%d")
        draw.text((x_px - 45, bottom + 12), label, fill="black", font=tick_font)

    draw.text((20, top - 45), ylabel, fill="black", font=title_font)
    draw.line([(left, top), (left, bottom), (right, bottom)], fill="black", width=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG")


def generate_graphs(metrics_data, report_data, graph_output_dir="data/assets/graphs"):
    """
    Generate time series graphs from metrics_data and save them as PNGs.
    For each metric in report_data["metrics"], attach the corresponding graph path under 'graph_image_path'.
    """
    if not report_data:
        print("[generate_graphs] report_data is empty; skipping.")
        return report_data

    graph_output_dir = Path(graph_output_dir)
    graph_output_dir.mkdir(parents=True, exist_ok=True)
    # LaTeX copies data/assets -> temp/assets; paths must be assets/graphs/<id>.png
    latex_graph_path = Path("assets/graphs")

    stats_df = pd.DataFrame.from_dict(metrics_data["outputs"], orient="index")
    stats_df.index = pd.to_datetime(stats_df.index)

    for metric in report_data.get("metrics", []):
        metric_id = metric.get("id")
        field = ID_TO_FIELD.get(metric_id)
        if not field or field not in stats_df.columns:
            print(f"[generate_graphs] Skipping unknown or missing field '{metric_id}'")
            continue

        metric_data = stats_df[field].dropna()
        if len(metric_data) <= 1:
            print(
                f"[generate_graphs] Skipping '{metric_id}' - need at least 2 data points, got {len(metric_data)}"
            )
            continue

        filename = f"{metric_id}.png"
        graph_path = graph_output_dir / filename
        print(f"[generate_graphs] Writing {graph_path}")

        _draw_chart(
            metric_data.index.to_pydatetime(),
            metric_data.values,
            units.get(metric_id, metric_id),
            graph_path,
            bar_chart=(metric_id == "precipitation"),
        )

        metric["graph_image_path"] = str(latex_graph_path / filename)

    return report_data
