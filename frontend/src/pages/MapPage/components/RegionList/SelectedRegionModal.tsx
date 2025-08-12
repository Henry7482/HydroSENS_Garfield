import { Button } from "@/components/ui/button";
import { selectRegion } from "@/redux/regionActions";
import { Region } from "@/types/region";
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import DeleteRegionButton from "./DeleteRegionButton";
import { RootState } from "@/redux/store";
import LineBreak from "../LineBreak";

interface SelectedRegionModalProps {
    region: Region;
}
function SelectedRegionModal({ region }: SelectedRegionModalProps) {
    const dispatch = useDispatch();

    const handleBackClick = () => {
        dispatch(selectRegion(null));
    };

    const { selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );

    return (
        <div className="absolute flex flex-col bg-white p-3 shadow-lg rounded-md gap-2 min-w-60 m-4">
            <div className="w-full">
                <Button
                    variant="link"
                    className="p-0 text-black"
                    onClick={handleBackClick}
                >
                    {"< Back"}
                </Button>
            </div>

            <LineBreak />

            <div className="flex flex-row justify-between p-2">
                <div className="flex gap-3">
                    <div
                        className="w-4 h-4 rounded-full mt-1.5"
                        style={{ backgroundColor: region.color }}
                    ></div>
                    <div className="flex flex-col items-start">
                        <div className="text-sm">{region.name}</div>
                        <div className="text-xs text-gray-500">
                            {Math.round(region.area)} km²
                        </div>
                    </div>
                </div>
                <DeleteRegionButton index={selectedRegionIndex || 0} />
            </div>
        </div>
    );
}

export default SelectedRegionModal;
