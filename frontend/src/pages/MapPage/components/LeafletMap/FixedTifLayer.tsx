// components/LeafletMap/FixedTifLayer.tsx
import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import { useSelector, useDispatch } from "react-redux";
import { RootState, AppDispatch } from "@/redux/store";
import { setLayerDataRange } from "@/redux/layerActions";
import { COLOR_PALETTES } from "@/constants";

interface FixedTifLayerProps {
    opacity?: number;
}

// Type definitions for layer file
interface LayerFile {
    name: string;
    url: string;
}

// Helper function to interpolate between multiple colors in a palette
const interpolateColorArray = (
    colors: number[][],
    factor: number
): number[] => {
    // Clamp factor between 0 and 1
    factor = Math.max(0, Math.min(1, factor));

    // If only one color, return it
    if (colors.length === 1) {
        return [...colors[0]];
    }

    // If factor is 0, return first color
    if (factor === 0) {
        return [...colors[0]];
    }

    // If factor is 1, return last color
    if (factor === 1) {
        return [...colors[colors.length - 1]];
    }

    // Calculate which segment of the gradient we're in
    const segmentCount = colors.length - 1;
    const segmentSize = 1 / segmentCount;
    const segmentIndex = Math.floor(factor / segmentSize);
    const segmentFactor = (factor - segmentIndex * segmentSize) / segmentSize;

    // Handle edge case where we're exactly at the end
    const startIndex = Math.min(segmentIndex, segmentCount - 1);
    const endIndex = Math.min(startIndex + 1, colors.length - 1);

    // Interpolate between the two colors in this segment
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

// Function to get color for a specific layer and normalized value
const getLayerColor = (
    layerName: string,
    normalizedValue: number,
    opacity: number
): string => {
    // Extract base name without .tif extension
    const baseName = layerName.replace(".tif", "");

    // Get color palette for this layer
    const palette = COLOR_PALETTES[baseName as keyof typeof COLOR_PALETTES];

    if (!palette) {
        // Fallback to grayscale if layer not found
        const intensity = Math.floor(normalizedValue * 255);
        return `rgba(${intensity}, ${intensity}, ${intensity}, ${opacity})`;
    }

    // Interpolate through the color array
    const [r, g, b] = interpolateColorArray(palette, normalizedValue);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

const FixedTifLayer: React.FC<FixedTifLayerProps> = ({ opacity = 0.8 }) => {
    const map = useMap();
    const dispatch = useDispatch<AppDispatch>();
    const layerRef = useRef<{
        addTo: (map: any) => void;
        remove: () => void;
    } | null>(null);
    const layerState = useSelector((state: RootState) => state.layers);
    const regionState = useSelector((state: RootState) => state.regionState);

    useEffect(() => {
        // Create a custom pane for TIF layers with higher z-index
        if (!map.getPane("tifLayer")) {
            const tifPane = map.createPane("tifLayer");
            tifPane.style.zIndex = "650"; // Higher than overlay pane (600) but lower than popup (700)
        }
    }, [map]);

    useEffect(() => {
        let isMounted = true;

        // Cleanup previous layer
        if (layerRef.current) {
            try {
                map.removeLayer(layerRef.current);
            } catch (error) {
                console.warn("Error removing previous layer:", error);
            }
            layerRef.current = null;
        }

        // Only proceed if we have all required data and not selecting "none"
        if (
            regionState.selectedRegionIndex === null ||
            !layerState.selectedDate ||
            !layerState.selectedLayer ||
            layerState.selectedLayer === "none" ||
            layerState.dateLayers.length === 0
        ) {
            return;
        }

        const selectedDateData = layerState.dateLayers.find(
            (dl) => dl.date === layerState.selectedDate
        );

        if (!selectedDateData) return;

        const selectedLayerFile = selectedDateData.layers.find(
            (layer) => layer.name === layerState.selectedLayer
        );

        if (!selectedLayerFile) return;

        loadTifLayer(selectedLayerFile, isMounted);

        return () => {
            isMounted = false;
            if (layerRef.current) {
                try {
                    map.removeLayer(layerRef.current);
                } catch (error) {
                    console.warn("Error removing layer on cleanup:", error);
                }
                layerRef.current = null;
            }
        };
    }, [
        map,
        layerState.selectedDate,
        layerState.selectedLayer,
        layerState.dateLayers,
        regionState.selectedRegionIndex,
        opacity,
        dispatch,
    ]);

    const loadTifLayer = async (layerFile: LayerFile, isMounted: boolean) => {
        try {
            console.log(`Loading TIF layer: ${layerFile.name}`);

            // Fetch the blob from the URL
            const response = await fetch(layerFile.url);
            const blob = await response.blob();
            const arrayBuffer = await blob.arrayBuffer();

            if (!isMounted) return;

            // Dynamic imports
            const [parseGeoraster, GeoRasterLayer] = await Promise.all([
                import("georaster").then((module) => module.default),
                import("georaster-layer-for-leaflet").then(
                    (module) => module.default
                ),
            ]);

            if (!isMounted) return;

            console.log("Parsing georaster data...");
            const georaster = await parseGeoraster(arrayBuffer);

            if (!isMounted) return;

            console.log("Georaster info:", {
                width: georaster.width,
                height: georaster.height,
                numberOfRasters: georaster.numberOfRasters,
                projection: georaster.projection,
                pixelWidth: georaster.pixelWidth,
                pixelHeight: georaster.pixelHeight,
                bounds: `${georaster.xmin}, ${georaster.ymin}, ${georaster.xmax}, ${georaster.ymax}`,
                noDataValue: georaster.noDataValue,
                mins: georaster.mins,
                maxs: georaster.maxs,
            });

            // Store the data range in Redux for the legend
            const layerKey = `${layerState.selectedDate}_${layerState.selectedLayer}`;
            dispatch(
                setLayerDataRange(layerKey, {
                    min: georaster.mins[0],
                    max: georaster.maxs[0],
                })
            );

            // Check if the georaster bounds are within reasonable distance of current map view
            const georasterBounds = {
                south: georaster.ymin,
                north: georaster.ymax,
                west: georaster.xmin,
                east: georaster.xmax,
            };

            const mapBounds = map.getBounds();
            console.log("Map bounds:", {
                south: mapBounds.getSouth(),
                north: mapBounds.getNorth(),
                west: mapBounds.getWest(),
                east: mapBounds.getEast(),
            });

            // Create layer with custom pane to ensure it renders above polygons
            const geoRasterLayer = new GeoRasterLayer({
                georaster: georaster,
                opacity: opacity,
                pane: "tifLayer", // Use custom pane with higher z-index
                pixelValuesToColorFn: (pixelValues: number[]) => {
                    // Check if this is a multi-band RGB image (like TCI.tif)
                    if (
                        pixelValues.length >= 3 &&
                        layerFile.name.toLowerCase().includes("tci")
                    ) {
                        const [red, green, blue] = pixelValues;

                        // Handle no-data values for any band
                        if (
                            red === georaster.noDataValue ||
                            green === georaster.noDataValue ||
                            blue === georaster.noDataValue ||
                            red === null ||
                            green === null ||
                            blue === null ||
                            red === undefined ||
                            green === undefined ||
                            blue === undefined ||
                            isNaN(red) ||
                            isNaN(green) ||
                            isNaN(blue)
                        ) {
                            return null;
                        }

                        // Normalize RGB values to 0-255 range
                        // Assuming the input values are in the typical range for satellite imagery
                        const normalizeBand = (
                            value: number,
                            bandIndex: number
                        ) => {
                            const min = georaster.mins[bandIndex];
                            const max = georaster.maxs[bandIndex];
                            const normalized = (value - min) / (max - min);
                            return Math.max(
                                0,
                                Math.min(255, Math.round(normalized * 255))
                            );
                        };

                        const r = normalizeBand(red, 0);
                        const g = normalizeBand(green, 1);
                        const b = normalizeBand(blue, 2);

                        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
                    } else {
                        // Handle single-band images (existing logic)
                        const pixelValue = pixelValues[0];

                        // Handle no-data values
                        if (
                            pixelValue === georaster.noDataValue ||
                            pixelValue === null ||
                            pixelValue === undefined ||
                            isNaN(pixelValue)
                        ) {
                            return null;
                        }

                        // Use the actual data range from the georaster
                        const min = georaster.mins[0];
                        const max = georaster.maxs[0];
                        const normalized = (pixelValue - min) / (max - min);

                        // Clamp normalized value between 0 and 1
                        const clampedNormalized = Math.max(
                            0,
                            Math.min(1, normalized)
                        );

                        // Get color based on layer type and normalized value
                        return getLayerColor(
                            layerFile.name,
                            clampedNormalized,
                            opacity
                        );
                    }
                },
                resolution: 256,
                debugLevel: 1,
            });

            if (!isMounted) return;

            console.log("Adding georaster layer to map...");
            geoRasterLayer.addTo(map);
            layerRef.current = geoRasterLayer;

            // Log success
            geoRasterLayer.on("load", () => {
                console.log(
                    `✅ TIF layer ${layerFile.name} loaded and displayed successfully with custom color palette and data range stored`
                );
            });

            geoRasterLayer.on("error", (error: unknown) => {
                console.error(
                    `❌ Error with TIF layer ${layerFile.name}:`,
                    error
                );
            });
        } catch (error) {
            console.error(
                `❌ Failed to load TIF layer ${layerFile.name}:`,
                error
            );
        }
    };

    return null;
};

export default FixedTifLayer;
