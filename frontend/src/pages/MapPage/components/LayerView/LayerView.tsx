// components/LayerView/LayerView.tsx
import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { AppDispatch, RootState } from "@/redux/store";
import { setSelectedDate, setSelectedLayer } from "@/redux/layerActions";
import { Card, CardContent } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import { Layers, Calendar, Image } from "lucide-react";
import { COLOR_PALETTES } from "@/constants";

// Define value ranges for each layer
const LAYER_RANGES = {
    vegetation: { min: 0, max: 100, unit: "%" },
    impervious: { min: 0, max: 100, unit: "%" },
    CCN_final: { min: 0, max: 100, unit: "" },
    Runoff: { min: 0, max: null, unit: "" }, // max from data
    NDVI: { min: -1, max: 1, unit: "" },
    Vegetation_Health: { min: null, max: null, unit: "" }, // both from data
    soil: { min: 0, max: 100, unit: "%" },
};

// Define user-friendly display names for each layer
const LAYER_DISPLAY_NAMES = {
    vegetation: "Vegetation Fraction",
    impervious: "Impervious",
    CCN_final: "Curve Number",
    Runoff: "Runoff",
    NDVI: "NDVI",
    Vegetation_Health: "Vegetation Health",
    soil: "Soil Fraction",
    TCI: "True Color",
};

// Helper function to get display name for a layer
const getLayerDisplayName = (layerName: string): string => {
    const baseName = layerName.replace(".tif", "");
    return (
        LAYER_DISPLAY_NAMES[baseName as keyof typeof LAYER_DISPLAY_NAMES] ||
        baseName
    );
};

// Helper function to interpolate between multiple colors in a palette
const interpolateColorArray = (
    colors: number[][],
    factor: number
): number[] => {
    factor = Math.max(0, Math.min(1, factor));

    if (colors.length === 1) {
        return [...colors[0]];
    }

    if (factor === 0) {
        return [...colors[0]];
    }

    if (factor === 1) {
        return [...colors[colors.length - 1]];
    }

    const segmentCount = colors.length - 1;
    const segmentSize = 1 / segmentCount;
    const segmentIndex = Math.floor(factor / segmentSize);
    const segmentFactor = (factor - segmentIndex * segmentSize) / segmentSize;

    const startIndex = Math.min(segmentIndex, segmentCount - 1);
    const endIndex = Math.min(startIndex + 1, colors.length - 1);

    const startColor = colors[startIndex];
    const endColor = colors[endIndex];

    return [
        Math.round(
            startColor[0] + (endColor[0] - startColor[0]) * segmentFactor
        ),
        Math.round(
            startColor[1] + (endColor[1] - startColor[1]) * segmentFactor
        ),
        Math.round(
            startColor[2] + (endColor[2] - startColor[2]) * segmentFactor
        ),
    ];
};

// Legend component
const LayerLegend: React.FC<{
    layerName: string;
    dataRange?: { min: number; max: number };
}> = ({ layerName, dataRange }) => {
    const baseName = layerName.replace(".tif", "");

    // Don't show legend for True Color layer
    if (baseName === "TCI") {
        return null;
    }

    const palette = COLOR_PALETTES[baseName as keyof typeof COLOR_PALETTES];
    const rangeConfig = LAYER_RANGES[baseName as keyof typeof LAYER_RANGES];

    if (!palette || !rangeConfig) {
        return null;
    }

    // Determine the actual min/max values to display
    let minValue = rangeConfig.min;
    let maxValue = rangeConfig.max;

    // Use actual data range if specified in config
    if (rangeConfig.min === null && dataRange) {
        minValue = dataRange.min;
    }
    if (rangeConfig.max === null && dataRange) {
        maxValue = dataRange.max;
    }

    // If we still don't have values, don't render legend
    if (minValue === null || maxValue === null) {
        return (
            <div className="text-xs text-gray-500 mt-2">
                Legend unavailable - loading data range...
            </div>
        );
    }

    // Create gradient string
    const gradientStops = [];
    for (let i = 0; i <= 10; i++) {
        const factor = i / 10;
        const [r, g, b] = interpolateColorArray(palette, factor);
        gradientStops.push(`rgb(${r}, ${g}, ${b})`);
    }
    const gradientStyle = `linear-gradient(to right, ${gradientStops.join(
        ", "
    )})`;

    // Format values for display
    const formatValue = (value: number) => {
        if (Math.abs(value) < 0.01 && value !== 0) {
            return value.toExponential(2);
        }
        return value.toFixed(0);
    };

    return (
        <div className="mt-3 space-y-2">
            {/* Gradient bar */}
            <div className="relative">
                <div
                    className="h-3 w-full rounded border border-gray-300"
                    style={{ background: gradientStyle }}
                />

                {/* Value labels */}
                <div className="flex justify-between mt-1 text-xs text-gray-600">
                    <span>
                        {formatValue(minValue)}
                        {rangeConfig.unit}
                    </span>
                    <span>
                        {formatValue(maxValue)}
                        {rangeConfig.unit}
                    </span>
                </div>
            </div>
        </div>
    );
};

const LayerView: React.FC = () => {
    const dispatch = useDispatch<AppDispatch>();
    const layerState = useSelector((state: RootState) => state.layers);
    const dashboardState = useSelector((state: RootState) => state.dashboard);

    const {
        dateLayers,
        selectedDate,
        selectedLayer,
        loading,
        error,
        layerDataRanges,
    } = layerState;

    // Get available layers for the selected date
    const selectedDateLayers =
        dateLayers.find((dl) => dl.date === selectedDate)?.layers || [];

    // Add a "No Layer" option at the beginning with user-friendly display names
    const layersWithNoOption = [
        { name: "none", displayName: "No Layer" },
        ...selectedDateLayers.map((layer) => ({
            name: layer.name,
            displayName: getLayerDisplayName(layer.name),
        })),
    ];

    const handleDateChange = (date: string) => {
        dispatch(setSelectedDate(date));
        // Auto-select "No Layer" option for the new date
        dispatch(setSelectedLayer("none"));
    };

    const handleLayerChange = (layerName: string) => {
        dispatch(setSelectedLayer(layerName));
    };

    // Get current layer's data range
    const currentLayerDataRange =
        selectedLayer && selectedDate && layerDataRanges
            ? layerDataRanges[`${selectedDate}_${selectedLayer}`]
            : undefined;

    // Show loading if either dashboard is loading or layers are loading
    if (loading || dashboardState.loading) {
        return (
            <Card className="w-40 mr-6 bg-white/95 backdrop-blur-sm shadow-lg py-4">
                <CardContent className="px-4 py-0">
                    <div className="flex items-center space-x-2">
                        <Layers className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Loading layers</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error && !error.includes("404")) {
        return (
            <Card className="w-40 mr-6 bg-white/95 backdrop-blur-sm shadow-lg py-4">
                <CardContent className="px-4 py-0">
                    <div className="text-sm text-red-600">
                        Error loading layers: {error}
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Only show "No layer data available" if dashboard has finished loading and there's no error
    if (
        dateLayers.length === 0 &&
        !dashboardState.loading &&
        !dashboardState.error
    ) {
        return (
            <Card className="w-40 mr-6 bg-white/95 backdrop-blur-sm shadow-lg py-4">
                <CardContent className="px-4 py-0">
                    <div className="text-sm text-gray-600">
                        No layer data available
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="w-48 mr-6 bg-white/95 backdrop-blur-sm shadow-lg py-4">
            <CardContent className="px-4 py-0">
                <Accordion type="single" collapsible>
                    <AccordionItem value="layers" className="border-none">
                        <AccordionTrigger className="py-0 hover:no-underline">
                            <div className="flex items-center space-x-2">
                                <Layers className="w-4 h-4" />
                                <span className="font-medium text-sm">
                                    Layers
                                </span>
                            </div>
                        </AccordionTrigger>
                        <AccordionContent className="pt-4 space-y-4">
                            {/* Date Selection */}
                            <div className="space-y-2">
                                <label className="text-xs font-medium text-gray-700 flex items-center space-x-1">
                                    <Calendar className="w-3 h-3" />
                                    <span>Date</span>
                                </label>
                                <Select
                                    value={selectedDate || ""}
                                    onValueChange={handleDateChange}
                                >
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="Select date" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {dateLayers.map((dateLayer) => (
                                            <SelectItem
                                                key={dateLayer.date}
                                                value={dateLayer.date}
                                            >
                                                {dateLayer.date}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Layer Selection - Dropdown */}
                            {selectedDate && layersWithNoOption.length > 0 && (
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-gray-700 flex items-center space-x-1">
                                        <Image className="w-3 h-3" />
                                        <span>Layer</span>
                                    </label>
                                    <Select
                                        value={selectedLayer || "none"}
                                        onValueChange={handleLayerChange}
                                    >
                                        <SelectTrigger className="w-full">
                                            <SelectValue placeholder="Select layer" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {layersWithNoOption.map((layer) => (
                                                <SelectItem
                                                    key={layer.name}
                                                    value={layer.name}
                                                >
                                                    {layer.displayName}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            )}

                            {/* Legend - Show only when a layer (not "none") is selected */}
                            {selectedLayer && selectedLayer !== "none" && (
                                <LayerLegend
                                    layerName={selectedLayer}
                                    dataRange={currentLayerDataRange}
                                />
                            )}
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
            </CardContent>
        </Card>
    );
};

export default LayerView;
