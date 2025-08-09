import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, ZoomControl, useMap } from "react-leaflet";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "../../../../redux/store";
import { selectRegion } from "../../../../redux/regionActions";
import RegionPolygons from "./RegionPolygons";
import { ViewMode } from "@/types/viewMode";
import CustomDrawingControl from "../RegionDrawing/CustomDrawingControl";
import AddRegionModal from "../RegionDrawing/AddRegionModal";
import LeafletMapController from "./LeafletMapController";
import { useDrawingControl } from "../RegionDrawing/useDrawingControl";
import FixedTifLayer from "./FixedTifLayer";

// Component to handle map center updates
function MapCenterUpdater({ center }: { center: [number, number] }) {
    const map = useMap();

    useEffect(() => {
        map.setView(center, map.getZoom());
    }, [center, map]);

    return null;
}

function LeafletMap() {
    const dispatch = useDispatch();
    const { regions, selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );
    const { viewMode } = useSelector((state: RootState) => state.viewModeState);

    // State for user location
    const [userLocation, setUserLocation] = useState<[number, number]>([
        52.52, 13.405,
    ]);
    const [locationLoaded, setLocationLoaded] = useState(false);

    const {
        currentDrawingMode,
        hasActiveShape,
        drawingControlRef,
        handleDrawingModeChange,
        handleShapeCreated,
        handleModeComplete,
        handleDeleteShape,
        handleFinishEdit,
    } = useDrawingControl();

    // Get user location on component mount
    useEffect(() => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    setUserLocation([latitude, longitude]);
                    setLocationLoaded(true);
                },
                (error) => {
                    console.warn("Error getting location:", error);
                    // Keep default location if geolocation fails
                    setLocationLoaded(true);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000,
                }
            );
        } else {
            console.warn("Geolocation is not supported by this browser");
            setLocationLoaded(true);
        }
    }, []);

    // Handler for polygon click
    const handleRegionClick = (index: number) => {
        dispatch(selectRegion(index));
    };

    return (
        <>
            <MapContainer
                center={userLocation}
                zoom={12}
                className="absolute h-full w-full z-0"
                zoomControl={false}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Update map center when user location is loaded */}
                {locationLoaded && <MapCenterUpdater center={userLocation} />}

                <RegionPolygons
                    regions={regions}
                    onRegionClicked={
                        viewMode === ViewMode.MAIN_VIEW
                            ? handleRegionClick
                            : () => {}
                    }
                />

                {/* TIF layer overlay - only when region is selected */}
                {selectedRegionIndex !== null && <FixedTifLayer />}

                <LeafletMapController
                    selectedRegionIndex={selectedRegionIndex}
                    regions={regions}
                />

                {viewMode === ViewMode.DRAWING_VIEW && (
                    <CustomDrawingControl
                        ref={drawingControlRef}
                        drawingMode={currentDrawingMode}
                        onShapeCreated={handleShapeCreated}
                        onModeComplete={handleModeComplete}
                    />
                )}

                <ZoomControl position="bottomleft" />
            </MapContainer>

            {viewMode === ViewMode.DRAWING_VIEW && (
                <AddRegionModal
                    onDrawingModeChange={handleDrawingModeChange}
                    currentDrawingMode={currentDrawingMode}
                    hasActiveShape={hasActiveShape}
                    onDeleteShape={handleDeleteShape}
                    onFinishEdit={handleFinishEdit}
                />
            )}
        </>
    );
}

export default LeafletMap;
