// utils/map.ts - Improved area calculation

/**
 * Calculate the area of a polygon using the shoelace formula
 * Coordinates should be in [lat, lng] format
 */
export const calculatePolygonArea = (
    coordinates: [number, number][]
): number => {
    if (!coordinates || coordinates.length < 3) {
        return 0;
    }

    // Validate coordinates
    const validCoordinates = coordinates.filter(
        (coord) =>
            Array.isArray(coord) &&
            coord.length === 2 &&
            typeof coord[0] === "number" &&
            typeof coord[1] === "number" &&
            !isNaN(coord[0]) &&
            !isNaN(coord[1])
    );

    if (validCoordinates.length < 3) {
        console.warn("Not enough valid coordinates for area calculation");
        return 0;
    }

    // Ensure the polygon is closed (first and last points are the same)
    const coords = [...validCoordinates];
    if (
        coords[0][0] !== coords[coords.length - 1][0] ||
        coords[0][1] !== coords[coords.length - 1][1]
    ) {
        coords.push(coords[0]); // Close the polygon
    }

    try {
        // Calculate area using the shoelace formula (in square degrees)
        let area = 0;
        for (let i = 0; i < coords.length - 1; i++) {
            const [lat1, lng1] = coords[i];
            const [lat2, lng2] = coords[i + 1];
            area += lng1 * lat2 - lng2 * lat1;
        }
        area = Math.abs(area) / 2;

        // Convert from square degrees to square kilometers
        // This is an approximation - for more accurate results, you might want to use a proper geodetic library
        const avgLat =
            coords.reduce((sum, coord) => sum + coord[0], 0) / coords.length;
        const latRadians = (avgLat * Math.PI) / 180;

        // Earth's radius in km
        const earthRadius = 6371;

        // Conversion factors for degrees to km at the average latitude
        const kmPerDegreeLat = (earthRadius * Math.PI) / 180;
        const kmPerDegreeLng = kmPerDegreeLat * Math.cos(latRadians);

        // Convert area to square kilometers
        const areaKm2 = area * kmPerDegreeLat * kmPerDegreeLng;

        return Math.max(0, areaKm2); // Ensure non-negative
    } catch (error) {
        console.error("Error in area calculation:", error);
        return 0;
    }
};

/**
 * Alternative area calculation using Haversine formula for more accuracy
 * This is more computationally intensive but more accurate for larger areas
 */
export const calculatePolygonAreaHaversine = (
    coordinates: [number, number][]
): number => {
    if (!coordinates || coordinates.length < 3) {
        return 0;
    }

    const validCoordinates = coordinates.filter(
        (coord) =>
            Array.isArray(coord) &&
            coord.length === 2 &&
            typeof coord[0] === "number" &&
            typeof coord[1] === "number" &&
            !isNaN(coord[0]) &&
            !isNaN(coord[1])
    );

    if (validCoordinates.length < 3) {
        return 0;
    }

    // Earth's radius in kilometers
    const R = 6371;

    const toRadians = (degrees: number) => (degrees * Math.PI) / 180;

    try {
        let area = 0;
        const n = validCoordinates.length;

        for (let i = 0; i < n; i++) {
            const j = (i + 1) % n;
            const [lat1, lng1] = validCoordinates[i];
            const [lat2, lng2] = validCoordinates[j];

            const φ1 = toRadians(lat1);
            const φ2 = toRadians(lat2);
            const Δλ = toRadians(lng2 - lng1);

            const E =
                2 *
                Math.atan2(
                    Math.tan(Δλ / 2),
                    Math.tan(φ1 / 2) + Math.tan(φ2 / 2)
                );
            const F =
                2 *
                Math.atan2(
                    Math.tan(Δλ / 2),
                    Math.tan(φ1 / 2) - Math.tan(φ2 / 2)
                );

            area += E - F;
        }

        if (isPoleEnclosedBy(validCoordinates))
            area = Math.abs(area) - 2 * Math.PI;

        const areaKm2 = Math.abs((area * R * R) / 2);
        return areaKm2;
    } catch (error) {
        console.error("Error in Haversine area calculation:", error);
        // Fallback to simple calculation
        return calculatePolygonArea(coordinates);
    }
};

function isPoleEnclosedBy(coordinates: [number, number][]): boolean {
    // Simple check - for more complex polygons, you'd need a more sophisticated algorithm
    const nVertices = coordinates.length;
    let j = nVertices - 1;
    let c = false;

    for (let i = 0; i < nVertices; j = i++) {
        if (
            coordinates[i][1] > 90 !== coordinates[j][1] > 90 &&
            coordinates[i][0] <
                ((coordinates[j][0] - coordinates[i][0]) *
                    (90 - coordinates[i][1])) /
                    (coordinates[j][1] - coordinates[i][1]) +
                    coordinates[i][0]
        ) {
            c = !c;
        }
    }
    return c;
}
