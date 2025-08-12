import React from "react";
import { Region } from "@/types/region";
import { Polygon } from "react-leaflet";
import { RootState } from "@/redux/store";
import { useSelector } from "react-redux";

interface RegionPolygonsProps {
    regions: Region[];
    onRegionClicked: (index: number) => void;
}

function RegionPolygons({ regions, onRegionClicked }: RegionPolygonsProps) {
    const { selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );

    return (
        <div>
            {regions.map((region, index) => (
                <Polygon
                    key={index}
                    positions={region.coordinates}
                    pathOptions={{
                        color: region.color,
                        fillOpacity: selectedRegionIndex === index ? 0.5 : 0.2,
                        weight: selectedRegionIndex === index ? 3 : 1,
                    }}
                    eventHandlers={{
                        click: () => onRegionClicked(index),
                    }}
                />
            ))}
        </div>
    );
}

export default RegionPolygons;
