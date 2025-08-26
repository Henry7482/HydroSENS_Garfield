import {
  Leaf,
  Sprout,
  Droplet,
  CloudRain,
  Thermometer,
  Gauge,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Mock gauge definitions used in RegionDashboard & ChartCard
// ---------------------------------------------------------------------------
export interface GaugeMeta {
  label: string;
  value: number;
  min: number;
  max: number;
  description: string;
  icon: JSX.Element;
  color: string;
  unit?: string;
  chartType: "line" | "bar";
}

export const gauges: GaugeMeta[] = [
  {
    label: "NDVI",
    value: 0.5,
    min: 0,
    max: 1,
    description: "Moderately Healthy Vegetation",
    icon: <Leaf className="w-4 h-4" />,
    color: "#8b5cf6", // violet‑500
    chartType: "line",
  },
  {
    label: "Vegetation Fraction",
    value: 0.1,
    min: 0,
    max: 1,
    description: "Very Sparse Vegetation",
    icon: <Sprout className="w-4 h-4" />,
    color: "#4ade80", // green‑400
    chartType: "line",
  },
  {
    label: "Soil Fraction",
    value: 0.4,
    min: 0,
    max: 1,
    description: "Very Sparse Vegetation",
    icon: <Droplet className="w-4 h-4" />,
    color: "#60a5fa", // blue‑400
    chartType: "line",
  },
  {
    label: "Precipitation",
    value: 44,
    min: 0,
    max: 100,
    description: "Moderate Precipitation",
    icon: <CloudRain className="w-4 h-4" />,
    color: "#facc15", // yellow‑400
    unit: "mm",
    chartType: "bar",
  },
  {
    label: "Temperature",
    value: 26.5,
    min: -35,
    max: 80,
    description: "Mild Temperature",
    icon: <Thermometer className="w-4 h-4" />,
    color: "#fb923c", // orange‑400
    unit: "°C",
    chartType: "line",
  },
  {
    label: "Curve Number",
    value: 55,
    min: 0,
    max: 100,
    description: "Low Runoff Curve Number",
    icon: <Gauge className="w-4 h-4" />,
    color: "#f472b6", // pink‑400
    chartType: "line"
  }
];

// ---------------------------------------------------------------------------
// Mock time‑series data for the charts
// ---------------------------------------------------------------------------
const dates = [
  "20/04/2024",
  "22/04/2024",
  "24/04/2024",
  "26/04/2024",
  "28/04/2024",
  "30/04/2024",
];

const buildSeries = (values: number[]) =>
  dates.map((date, i) => ({ date, value: values[i] }));

export const chartData: Record<string, { date: string; value: number }[]> = {
  NDVI: buildSeries([60, 70, 78, 85, 75, 38]),
  "Vegetation Fraction": buildSeries([10, 20, 12, 30, 18, 27]),
  "Soil Fraction": buildSeries([50, 40, 60, 35, 20, 55]),
  Precipitation: buildSeries([10, 5, 2, 15, 8, 25]),
  Temperature: buildSeries([22, 24, 26, 28, 27, 26]),
  "Curve Number": buildSeries([45, 50, 55, 60, 53, 55]),
};
