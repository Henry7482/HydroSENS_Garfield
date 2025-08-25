// src/components/GaugeCard.tsx
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CircularProgressbarWithChildren,
  buildStyles,
} from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import { Leaf } from "lucide-react";

/**
 * GaugeCard
 * ---------------------------------
 * A reusable gauge-style KPI card that matches the Pillar dashboard design.
 *
 * Props:
 *  - label        (string)  : The metric name, e.g. "NDVI".
 *  - value        (number)  : Current reading (rounded to 2 decimals).
 *  - min          (number)  : Minimum value for the gauge (default: 0).
 *  - max          (number)  : Maximum value for the gauge (default: 1).
 *  - description  (string)  : Qualitative description based on the value (e.g. "Low NDVI").
 *  - icon         (ReactNode): Metric icon (defaults to <Leaf />).
 *  - color        (string)  : Primary HEX color for the gauge path & accent.
 */
export interface GaugeCardProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  description: string;
  icon?: React.ReactNode;
  color?: string;
  className?: string;
}

export const GaugeCard: React.FC<GaugeCardProps> = ({
  label,
  value,
  min = 0,
  max = 1,
  description,
  icon,
  color = "#6b21a8",
  className
}) => {
  // Calculate percentage for the gauge
  const percent = ((value - min) / (max - min)) * 100;
  const backgroundTint = `${color}10`; // ~6% opacity
  const trailTint = `${color}29`;      // ~16% opacity

  // Format the numeric display to 2 decimals
  const displayValue = value.toFixed(2);

  return (
    <Card
      className={`rounded-2xl border-0 shadow-sm ${className ?? ""}`}
      style={{ background: backgroundTint }}
    >
      {/* Header */}
      <CardHeader className="p-4 pb-0">
        <div className="flex items-center gap-2">
          <span
            className="w-7 h-7 flex items-center justify-center rounded-full"
            style={{ background: trailTint }}
          >
            {icon ?? <Leaf className="w-4 h-4" style={{ color }} />}
          </span>
          <CardTitle className="text-lg font-semibold" style={{ color }}>
            {label}
          </CardTitle>
        </div>
      </CardHeader>

      {/* Body */}
      <CardContent className="flex flex-col items-center p-4 pt-2 gap-1">
        <div className="relative w-28">
          <CircularProgressbarWithChildren
            value={percent}
            minValue={0}
            maxValue={100}
            circleRatio={0.5}
            styles={buildStyles({
              rotation: 0.75,
              strokeLinecap: "round",
              pathColor: color,
              trailColor: trailTint,
              textColor: "#0f172a"
            })}
          >
            <span className="text-lg font-semibold text-slate-900">
              {displayValue}
            </span>
          </CircularProgressbarWithChildren>

          {/* Min / Max */}
          <span className="absolute left-0 bottom-3 text-sm leading-none text-slate-700 select-none">
            {min}
          </span>
          <span className="absolute right-0 bottom-3 text-sm leading-none text-slate-700 select-none">
            {max}
          </span>
        </div>

        {/* Qualitative description */}
        <p className="pt-1 text-base font-medium text-center text-slate-800">
          {description}
        </p>
      </CardContent>
    </Card>
  );
};