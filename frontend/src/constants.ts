export const MAX_REGION_AREA_KMSQ = 75;
export const MAX_REGION_SIZE_BYTES = 50331648;
// Define color palettes for each layer type as arrays of RGB colors
export const COLOR_PALETTES = {
    vegetation: [
        [255, 255, 255], // White
        [0, 100, 0], // Dark green
    ],
    impervious: [
        [255, 255, 255], // White
        [64, 64, 64], // Dark gray
    ],
    CCN_final: [
        [0, 0, 255], // Blue
        [0, 255, 255], // Cyan
        [0, 255, 0], // Green
        [255, 255, 0], // Yellow
        [255, 0, 0], // Red
    ],
    Runoff: [
        [255, 255, 255], // White
        [0, 0, 139], // Dark blue
    ],
    NDVI: [
        [100, 0, 0],
        [255, 0, 0],
        [255, 255, 0],
        [0, 200, 0],
        [0, 100, 0],
    ],
    Vegetation_Health: [
        [255, 255, 0], // Yellow
        [0, 128, 0], // Green
    ],
    soil: [
        [255, 255, 255], // White
        [101, 67, 33], // Dark brown
    ],
};
