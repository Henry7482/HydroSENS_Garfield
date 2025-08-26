import { Region } from "@/types/region";
import { LatLngBounds, LatLng } from "leaflet";
import { useEffect } from "react";
import { useMap } from "react-leaflet";

// This component will handle map operations like fitting bounds
function LeafletMapController({
    selectedRegionIndex,
    regions,
}: {
    selectedRegionIndex: number | null;
    regions: Region[];
}) {
    const map = useMap();

    useEffect(() => {
        if (selectedRegionIndex === null) {
            return;
        }

        const regionCoords = regions[selectedRegionIndex].coordinates;

        // Create bounds from polygon coordinates
        const bounds = new LatLngBounds(
            regionCoords.map((coord) => new LatLng(coord[0], coord[1]))
        );

        // Calculate padding to make the region fill half the left side
        const paddingX = 0;
        const paddingY = window.innerHeight;

        // Fit the map to the bounds with padding
        map.fitBounds(bounds, {
            paddingBottomRight: [paddingY, paddingX],
        });
    }, [selectedRegionIndex, regions, map]);

    return null;
}

export default LeafletMapController;
