import { useEffect, useMemo, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { GaugeCard } from "./GaugeCard";
import { ChartCard } from "./ChartCard";
import { Star, Loader2 } from "lucide-react";

import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "@/redux/store";
import { selectRegion } from "@/redux/regionActions";
import { fetchHydrosens } from "@/redux/dashboardActions";
import { fetchLayers, clearLayers } from "@/redux/layerActions";
import { HydrosensOutputs } from "@/types/hydrosens";
import DownloadCSVButton from "./DownloadCSVButton";

import { generateReport, GenerateReportPayload } from "@/api/reports";
import { PDFViewerOverlay } from "./PDFViewerOverlay";

// Add interface for props
interface RegionDashboardProps {
    onPdfOverlayToggle?: (isOpen: boolean) => void;
}

/* ------------------------------------------------------------------ */
/*  Colour / unit meta per metric key                                 */
/* ------------------------------------------------------------------ */
const metricMeta = {
    ndvi: {
        label: "NDVI",
        color: "#8b5cf6",
        min: 0,
        max: 1,
        unit: undefined,
        chartType: "line",
    },
    "vegetation-fraction": {
        label: "Vegetation Fraction",
        color: "#479e15",
        min: 0,
        max: 1,
        unit: undefined,
        chartType: "line",
    },
    "soil-fraction": {
        label: "Soil Fraction",
        color: "#d95632",
        min: 0,
        max: 1,
        unit: undefined,
        chartType: "line",
    },
    precipitation: {
        label: "Precipitation",
        color: "#2a72d1",
        min: 0,
        max: 100,
        unit: "mm",
        chartType: "bar",
    },
    temperature: {
        label: "Temperature",
        color: "#fb923c",
        min: -35,
        max: 80,
        unit: "°C",
        chartType: "line",
    },
    "curve-number": {
        label: "Curve Number",
        color: "#f472b6",
        min: 0,
        max: 100,
        unit: undefined,
        chartType: "line",
    },
} as const;

function RegionDashboard({ onPdfOverlayToggle }: RegionDashboardProps) {
    const dispatch = useDispatch<AppDispatch>();
    const regionState = useSelector((s: RootState) => s.regionState);
    const dateState = useSelector((s: RootState) => s.dateState);
    const dashboard = useSelector((s: RootState) => s.dashboard);
    const settings = useSelector((s: RootState) => s.settings);
    const layerState = useSelector((s: RootState) => s.layers);

    // Report generation state
    const [isGeneratingReport, setIsGeneratingReport] = useState(false);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false);

    // Track if we've already fetched layers for the current dashboard data
    const [layersFetchedForOutputs, setLayersFetchedForOutputs] =
        useState<string>("");

    // Track if dashboard has just finished loading
    const [dashboardJustLoaded, setDashboardJustLoaded] = useState(false);

    /* Track when dashboard finishes loading */
    useEffect(() => {
        if (
            !dashboard.loading &&
            !dashboard.error &&
            dashboard?.outputs &&
            Object.keys(dashboard.outputs).length > 0
        ) {
            setDashboardJustLoaded(true);
        } else {
            setDashboardJustLoaded(false);
        }
    }, [dashboard.loading, dashboard.error, dashboard.outputs]);

    /* Fetch layers after dashboard data is loaded successfully */
    useEffect(() => {
        if (
            dashboardJustLoaded &&
            regionState.selectedRegionIndex !== null &&
            !layerState.loading
        ) {
            const formatLocal = (d: Date) => {
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, "0");
                const day = String(d.getDate()).padStart(2, "0");
                return `${year}-${month}-${day}`;
            };
            const selectedRegion =
                regionState.regions[regionState.selectedRegionIndex];

            // Create a unique key for this dashboard outputs
            const outputsKey = JSON.stringify(dashboard.outputs);

            // Only fetch if we haven't already fetched for this exact dashboard data
            if (layersFetchedForOutputs !== outputsKey) {
                setLayersFetchedForOutputs(outputsKey);
                dispatch(
                    fetchLayers({
                        region_name: selectedRegion.name,
                        start_date: formatLocal(new Date(dateState.startDate)),
                        end_date: formatLocal(new Date(dateState.endDate)),
                    })
                );
            }
        }
    }, [
        dispatch,
        dashboardJustLoaded,
        dashboard.outputs,
        regionState.selectedRegionIndex,
        regionState.regions[regionState.selectedRegionIndex || 0]?.name,
        dateState.startDate,
        dateState.endDate,
        layerState.loading,
        layersFetchedForOutputs,
    ]);
    // Notify parent component when PDF overlay state changes
    useEffect(() => {
        onPdfOverlayToggle?.(isPdfViewerOpen);
    }, [isPdfViewerOpen, onPdfOverlayToggle]);

    // Debug: Log the entire region state whenever it changes
    useEffect(() => {
        console.log("=== REGION STATE DEBUG ===");
        console.log("regionState:", regionState);
        console.log("selectedRegionIndex:", regionState.selectedRegionIndex);
        console.log("regions array:", regionState.regions);
        console.log("regions length:", regionState.regions?.length);
        if (regionState.regions && regionState.regions.length > 0) {
            regionState.regions.forEach((region, index) => {
                console.log(`Region ${index}:`, region.name, region);
            });
        }
        if (regionState.selectedRegionIndex !== null && regionState.regions) {
            const selectedRegion =
                regionState.regions[regionState.selectedRegionIndex];
            console.log("Currently selected region:", selectedRegion);
        }
    }, [regionState]);

    /* Trigger fetch whenever region or date changes */
    useEffect(() => {
        if (
            regionState.selectedRegionIndex != null &&
            dateState.startDate &&
            dateState.endDate
        ) {
            dispatch(fetchHydrosens());
        }
    }, [
        dispatch,
        regionState.selectedRegionIndex,
        dateState.startDate,
        dateState.endDate,
    ]);

    /* Fetch layers after dashboard data is loaded successfully */
    // useEffect(() => {
    //     if (
    //         !dashboard.loading &&
    //         !dashboard.error &&
    //         Object.keys(dashboard.outputs).length > 0
    //     ) {
    //         dispatch(fetchLayers());
    //     }
    // }, [dispatch, dashboard.loading, dashboard.error, dashboard.outputs]);

    /* Clear layers when region is deselected */
    useEffect(() => {
        if (regionState.selectedRegionIndex === null) {
            dispatch(clearLayers());
        }
    }, [dispatch, regionState.selectedRegionIndex]);

    /* Transform API outputs → gauges + chart series, filtered by selected metrics */
    const { gauges, charts } = useMemo(() => {
        const outputs: HydrosensOutputs = dashboard.outputs;
        if (!outputs || !Object.keys(outputs).length) {
            return {
                gauges: [],
                charts: {} as Record<string, { date: string; value: number }[]>,
            };
        }

        // Get only the selected metrics from settings
        const selectedMetrics = settings.selectedMetrics;

        // 1) Build time‐series arrays (only for selected metrics)
        const chartSeries: Record<string, { date: string; value: number }[]> =
            {};
        selectedMetrics.forEach((k) => {
            chartSeries[k] = [];
        });

        Object.entries(outputs).forEach(([date, metrics]) => {
            selectedMetrics.forEach((k) => {
                chartSeries[k].push({
                    date,
                    value: (metrics as unknown as Record<string, number>)[k],
                });
            });
        });

        // 2) Compute average over all returned dates (for gauges, only selected metrics)
        const dateKeys = Object.keys(outputs);
        const nDates = dateKeys.length;
        const gaugeArr = selectedMetrics.map((k) => {
            let sum = 0;
            const values: number[] = [];
            for (const d of dateKeys) {
                const value = (outputs[d] as unknown as Record<string, number>)[
                    k
                ];
                sum += value;
                values.push(value);
            }
            const avg = sum / nDates;

            // Round to two decimals, small values become 0.00
            const rounded = Number(Math.abs(avg) < 0.01 ? 0 : avg.toFixed(2));

            // Calculate dynamic min/max for temperature and precipitation
            let min: number, max: number;
            if (k === "temperature" || k === "precipitation") {
                const dataMin = Math.min(...values);
                const dataMax = Math.max(...values);

                if (nDates === 1) {
                    // If only one date, pad the range so the average is in the middle
                    const range = Math.max(1, Math.abs(dataMax - dataMin) || 1);
                    const padding = range * 0.5;
                    min = Number((dataMin - padding).toFixed(2));
                    max = Number((dataMax + padding).toFixed(2));
                } else {
                    // Use actual data range with small padding
                    const range = dataMax - dataMin;
                    const padding = range * 0.1; // 10% padding
                    min = Number((dataMin - padding).toFixed(2));
                    max = Number((dataMax + padding).toFixed(2));
                }

                // Ensure precipitation min is never negative
                if (k === "precipitation") {
                    min = Math.max(0, min);
                }
            } else {
                // Use static min/max for other metrics
                min = metricMeta[k].min;
                max = metricMeta[k].max;
            }

            // Determine qualitative description
            const { label, unit } = metricMeta[k];
            const ratio = (avg - min) / (max - min);
            let desc = "";
            if (ratio < 0.25) desc = `Very Low ${label}`;
            else if (ratio < 0.5) desc = `Low ${label}`;
            else if (ratio < 0.75) desc = `Moderate ${label}`;
            else desc = `High ${label}`;

            return {
                key: k,
                value: rounded,
                min: min,
                max: max,
                label: label,
                unit: unit,
                color: metricMeta[k].color,
                chartType: metricMeta[k].chartType ?? "line",
                description: desc,
            };
        });
        console.log(gaugeArr);

        return { gauges: gaugeArr, charts: chartSeries };
    }, [dashboard.outputs, settings.selectedMetrics]);

    /* Handler for the "Back" button */
    const handleBack = () => {
        dispatch(selectRegion(null));
    };

    /* Handler for Generate Report button */
    const handleGenerateReport = async () => {
        if (regionState.selectedRegionIndex === null) return;

        console.log("=== DEBUGGING REGION ACCESS ===");
        console.log("Selected region index:", regionState.selectedRegionIndex);
        console.log("Total regions in Redux:", regionState.regions?.length);
        console.log("All regions in Redux state:", regionState.regions);

        const region = regionState.regions[regionState.selectedRegionIndex];

        console.log("Selected region object:", region);
        if (region) {
            console.log("Region name:", region.name);
            console.log("Region object keys:", Object.keys(region));
            console.log("Region name type:", typeof region.name);
            console.log("Region name length:", region.name?.length);
        } else {
            console.log("ERROR: Region is undefined!");
            return;
        }

        setIsGeneratingReport(true);

        try {
            const formatLocal = (d: Date) => {
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, "0");
                const day = String(d.getDate()).padStart(2, "0");
                return `${year}-${month}-${day}`;
            };

            const coordinates = region.coordinates.map(([lat, lon]) => [
                lon,
                lat,
            ]);

            const payload: GenerateReportPayload = {
                region_name: region.name || "Unknown Region",
                start_date: formatLocal(new Date(dateState.startDate)),
                end_date: formatLocal(new Date(dateState.endDate)),
                coordinates: coordinates,
            };

            console.log("Final payload:", payload);

            const pdfBlob = await generateReport(payload);
            const url = URL.createObjectURL(pdfBlob);
            setPdfUrl(url);
            setIsPdfViewerOpen(true);
        } catch (error) {
            console.error("Error generating report:", error);
        } finally {
            setIsGeneratingReport(false);
        }
    };

    /* Handler for closing PDF viewer */
    const handleClosePdfViewer = () => {
        setIsPdfViewerOpen(false);
        // Delay clearing the pdfUrl to allow exit animation to complete
        setTimeout(() => {
            if (pdfUrl) {
                URL.revokeObjectURL(pdfUrl);
                setPdfUrl(null);
            }
        }, 300); // Match the animation duration
    };

    const hasData = gauges.length > 0 && !dashboard.loading && !dashboard.error;

    return (
        <>
            <div className="absolute top-0 right-0 w-[50vw] h-full bg-gray-100 border-l shadow-lg">
                <ScrollArea className="h-full">
                    <div className="px-6 py-4 space-y-6">
                        {/* Header */}
                        <header className="flex items-center justify-between">
                            <button
                                className="text-sm font-medium text-slate-600 hover:underline"
                                onClick={handleBack}
                            >
                                &lt; Back
                            </button>
                            <h2 className="text-sm font-semibold text-slate-600">
                                Average Values
                            </h2>
                        </header>

                        {/* Loading */}
                        {dashboard.loading && (
                            <div className="flex flex-col items-center justify-center h-64">
                                <span className="text-lg font-medium text-slate-700">
                                    Loading
                                </span>
                                <div className="flex items-center space-x-1 mt-2">
                                    <span
                                        className="w-2 h-2 bg-slate-600 rounded-full animate-ping"
                                        style={{ animationDelay: "0s" }}
                                    />
                                    <span
                                        className="w-2 h-2 bg-slate-600 rounded-full animate-ping"
                                        style={{ animationDelay: "0.2s" }}
                                    />
                                    <span
                                        className="w-2 h-2 bg-slate-600 rounded-full animate-ping"
                                        style={{ animationDelay: "0.4s" }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* No Data */}

                        {settings.selectedMetrics.length === 0 && (
                            <div className="flex items-center justify-center h-64">
                                <span className="text-lg text-slate-600">
                                    No metrics selected. Please open settings to
                                    select metrics to display.
                                </span>
                            </div>
                        )}
                        {!dashboard.loading &&
                            !dashboard.error &&
                            gauges?.length === 0 && (
                                <div className="flex items-center justify-center h-64">
                                    <span className="text-lg text-slate-600">
                                        No data is available for this date
                                        range. Please selected a different date
                                        range.
                                    </span>
                                </div>
                            )}

                        {/* Error */}
                        {dashboard.error && (
                            <p className="text-center text-red-600">
                                {dashboard.error}
                            </p>
                        )}

                        {/* Gauges */}
                        {hasData && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {gauges.map((g) => (
                                    <GaugeCard
                                        key={g.key}
                                        label={
                                            g.unit
                                                ? `${g.label} (${g.unit})`
                                                : g.label
                                        }
                                        value={g.value}
                                        min={g.min}
                                        max={g.max}
                                        description={g.description}
                                        icon={undefined}
                                        color={g.color}
                                    />
                                ))}
                            </div>
                        )}

                        {/* Action Buttons */}
                        {hasData && (
                            <div className="flex flex-col sm:flex-row gap-4 pt-2">
                                <DownloadCSVButton />
                                <Button
                                    className="flex-1 h-12 gap-2"
                                    onClick={handleGenerateReport}
                                    disabled={isGeneratingReport}
                                >
                                    {isGeneratingReport ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Loading...
                                        </>
                                    ) : (
                                        <>
                                            <Star className="w-4 h-4" />
                                            Generate Report
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}

                        {/* Time‐series Charts */}
                        {hasData && (
                            <div className="space-y-6">
                                {gauges.map((g) => (
                                    <ChartCard
                                        key={g.key}
                                        label={
                                            g.unit
                                                ? `${g.label} (${g.unit})`
                                                : g.label
                                        }
                                        data={charts[g.key]}
                                        chartType={g.chartType}
                                        color={g.color}
                                        unit={g.unit}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* PDF Viewer Overlay */}
            {pdfUrl && (
                <PDFViewerOverlay
                    pdfUrl={pdfUrl}
                    onClose={handleClosePdfViewer}
                    isOpen={isPdfViewerOpen}
                />
            )}
        </>
    );
}

export default RegionDashboard;
