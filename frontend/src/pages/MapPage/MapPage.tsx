"use client";
import "leaflet/dist/leaflet.css";

import LeafletMap from "./components/LeafletMap/LeafletMap";
import RegionList from "./components/RegionList/RegionList";
import DateRangePicker from "./components/DateRangePicker/DateRangePicker";
import RegionDashboard from "./components/RegionDashboard";
import LayerView from "./components/LayerView/LayerView";
import SettingsButton from "./components/SettingsButton/SettingsButton";
import SettingsModal from "./components/SettingsModal/SettingsModal";

import { useSelector } from "react-redux";
import type { RootState } from "../../redux/store";
import { useState } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { ViewMode } from "@/types/viewMode";

function MapPage() {
    const { selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );
    const { viewMode } = useSelector((state: RootState) => state.viewModeState);

    // State to track PDF overlay visibility
    const [isPdfOverlayOpen, setIsPdfOverlayOpen] = useState(false);

    return (
        <div className="relative h-screen w-full overflow-hidden">
            {/* base map */}
            <LeafletMap />

            {/* Settings Button - Hide when PDF overlay is open */}
            {!isPdfOverlayOpen && <SettingsButton />}

            {/* region list (left sidebar) */}
            {viewMode === ViewMode.MAIN_VIEW && <RegionList />}

            {/* date-range picker — anchored at bottom-center of the map */}
            {viewMode === ViewMode.MAIN_VIEW && (
                <div
                    className="absolute bottom-4 flex flex-row justify-end items-end gap-10 pointer-events-none"
                    style={{
                        width: selectedRegionIndex !== null ? "50vw" : "100vw",
                        justifyContent:
                            selectedRegionIndex !== null ? "end" : "center",
                    }}
                >
                    {/* pointer-events auto so picker is clickable but wrapper isn't */}
                    <div className="relative pointer-events-auto">
                        <DateRangePicker />
                    </div>

                    {/* Layer View - Only show when region is selected */}
                    {selectedRegionIndex !== null && (
                        <div className="relative flex justify-center pointer-events-auto self-end">
                            <LayerView />
                        </div>
                    )}
                </div>
            )}

            {/* sliding dashboard (right) */}
            <AnimatePresence>
                {selectedRegionIndex != null && (
                    <motion.div
                        key="dashboard"
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "tween", duration: 0.35 }}
                        className="absolute inset-y-0 right-0 w-[50vw]"
                    >
                        <RegionDashboard onPdfOverlayToggle={setIsPdfOverlayOpen} />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Settings Modal */}
            <SettingsModal />
        </div>
    );
}

export default MapPage;