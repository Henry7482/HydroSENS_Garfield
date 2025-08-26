import React, { useCallback, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDispatch, useSelector } from "react-redux";
import { addRegion } from "@/redux/regionActions";
import { setRegionName, resetDrawingState } from "@/redux/regionDrawingActions";
import { Region } from "@/types/region";
import { RootState } from "@/redux/store";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import { generateRandomColor } from "@/utils/colors";
import { calculatePolygonArea } from "@/utils/map";
import { setViewMode } from "@/redux/viewModeActions";
import { ViewMode } from "@/types/viewMode";
import LineBreak from "../LineBreak";
import { useRegionSizeLimit } from "./AddRegionModal.hooks";
import ShapefileUploadModal from "./ShapefileUploadModal";
import {
    Square,
    Circle,
    Edit3,
    Trash2,
    Check,
    InfoIcon,
    Upload,
    Pentagon,
    AlertCircle,
} from "lucide-react";
import { MAX_REGION_AREA_KMSQ } from "@/constants";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";

export type DrawingMode = "polygon" | "rectangle" | "circle" | "edit" | null;

interface AddRegionModalProps {
    onDrawingModeChange: (mode: DrawingMode) => void;
    currentDrawingMode: DrawingMode;
    hasActiveShape: boolean;
    onDeleteShape: () => void;
    onFinishEdit: () => void;
}

function AddRegionModal({
    onDrawingModeChange,
    currentDrawingMode,
    hasActiveShape,
    onDeleteShape,
    onFinishEdit,
}: AddRegionModalProps) {
    const dispatch = useDispatch();
    const [isShapefileModalOpen, setIsShapefileModalOpen] = useState(false);

    const { regionName, currentCoordinates } = useSelector(
        (state: RootState) => state.regionDrawingState
    );

    const { regions } = useSelector((state: RootState) => state.regionState);

    // Check for duplicate region names
    const isDuplicateName = useMemo(() => {
        if (!regionName.trim()) return false;
        return regions.some(
            (region) =>
                region.name.toLowerCase() === regionName.trim().toLowerCase()
        );
    }, [regionName, regions]);

    const currentArea = useMemo(() => {
        if (currentCoordinates.length === 0) {
            return 0;
        }

        try {
            const area = calculatePolygonArea(currentCoordinates);
            console.log(
                "Calculated area:",
                area,
                "for coordinates:",
                currentCoordinates.length
            );
            return area;
        } catch (error) {
            console.error("Error calculating area:", error);
            return 0;
        }
    }, [currentCoordinates]);

    const {
        shouldShowAreaLimit,
        areaSizePercent,
        areaSizeText,
        isOverAreaSizeLimit,
    } = useRegionSizeLimit(currentArea);

    const isEditMode = currentDrawingMode === "edit";

    const handleRegionNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        dispatch(setRegionName(e.target.value));
    };

    const handleDrawingModeClick = (mode: DrawingMode) => {
        if (currentDrawingMode === mode) {
            // Toggle off if clicking the same mode
            onDrawingModeChange(null);
        } else {
            onDrawingModeChange(mode);
        }
    };

    const handleSave = useCallback(() => {
        if (
            !regionName.trim() ||
            currentCoordinates.length === 0 ||
            isDuplicateName
        )
            return;

        const newRegion: Region = {
            name: regionName.trim(),
            coordinates: currentCoordinates,
            color: generateRandomColor(),
            area: currentArea,
        };

        dispatch(addRegion(newRegion));
        handleClose();
    }, [currentArea, currentCoordinates, regionName, isDuplicateName]);

    const handleClose = () => {
        dispatch(resetDrawingState());
        dispatch(setViewMode(ViewMode.MAIN_VIEW));
        onDrawingModeChange(null);
    };

    const handleDelete = () => {
        onDeleteShape();
    };

    const handleEditDone = () => {
        // Complete the edit mode and save the edited coordinates
        onFinishEdit();
    };

    const handleOpenShapefileModal = () => {
        setIsShapefileModalOpen(true);
    };

    const handleCloseShapefileModal = () => {
        setIsShapefileModalOpen(false);
    };

    const handleShapefileLoaded = () => {
        // Shapefile has been loaded, coordinates are now in Redux
        // The modal will close itself, so we don't need to do anything special here
    };

    return (
        <>
            <div className="absolute m-4 w-80 p-4 border-r border-gray-200 rounded-lg bg-white flex flex-col z-100">
                <div className="space-y-3">
                    <div className="space-y-2">
                        <Button
                            variant="link"
                            className="text-black p-0"
                            onClick={handleClose}
                        >
                            {"< Back"}
                        </Button>

                        <LineBreak />

                        {/* Drawing Tools Section */}
                        <div className="space-y-3">
                            <label className="block text-sm font-medium mb-2">
                                Drawing Tools
                            </label>
                            <div className="grid grid-cols-3 gap-2">
                                <Button
                                    variant={
                                        currentDrawingMode === "polygon"
                                            ? "default"
                                            : "outline"
                                    }
                                    size="sm"
                                    onClick={() =>
                                        handleDrawingModeClick("polygon")
                                    }
                                    className="flex flex-col items-center gap-1 h-16"
                                    disabled={isEditMode}
                                >
                                    <Pentagon size={20} />
                                    <span className="text-xs">Polygon</span>
                                </Button>
                                <Button
                                    variant={
                                        currentDrawingMode === "rectangle"
                                            ? "default"
                                            : "outline"
                                    }
                                    size="sm"
                                    onClick={() =>
                                        handleDrawingModeClick("rectangle")
                                    }
                                    className="flex flex-col items-center gap-1 h-16"
                                    disabled={isEditMode}
                                >
                                    <Square size={20} />
                                    <span className="text-xs">Rectangle</span>
                                </Button>
                                <Button
                                    variant={
                                        currentDrawingMode === "circle"
                                            ? "default"
                                            : "outline"
                                    }
                                    size="sm"
                                    onClick={() =>
                                        handleDrawingModeClick("circle")
                                    }
                                    className="flex flex-col items-center gap-1 h-16"
                                    disabled={isEditMode}
                                >
                                    <Circle size={20} />
                                    <span className="text-xs">Circle</span>
                                </Button>
                            </div>
                        </div>

                        {/* Shapefile Upload Section */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium mb-2">
                                Import from File
                            </label>
                            <Button
                                variant="outline"
                                onClick={handleOpenShapefileModal}
                                className="w-full flex items-center gap-2"
                                disabled={isEditMode}
                            >
                                <Upload size={16} />
                                <span className="text-sm">
                                    Upload Shapefile
                                </span>
                            </Button>
                        </div>

                        {/* Edit Tools Section - Only show when there's an active shape */}
                        {hasActiveShape && (
                            <div className="space-y-2 ">
                                <div className="flex gap-2">
                                    {!isEditMode ? (
                                        // Normal mode - show Edit and Delete buttons
                                        <>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() =>
                                                    handleDrawingModeClick(
                                                        "edit"
                                                    )
                                                }
                                                className="flex items-center gap-2 flex-1"
                                            >
                                                <Edit3 size={16} />
                                                <span className="text-xs">
                                                    Edit
                                                </span>
                                            </Button>
                                        </>
                                    ) : (
                                        <>
                                            <Button
                                                variant="default"
                                                size="sm"
                                                onClick={handleEditDone}
                                                className="flex items-center gap-2 flex-1 bg-green-600 hover:bg-green-700"
                                            >
                                                <Check size={16} />
                                                <span className="text-xs">
                                                    Confirm
                                                </span>
                                            </Button>
                                        </>
                                    )}

                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={handleDelete}
                                        className="flex items-center gap-2 flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                                    >
                                        <Trash2 size={16} />
                                        <span className="text-xs">Delete</span>
                                    </Button>
                                </div>

                                {shouldShowAreaLimit && (
                                    <div>
                                        <div className="flex justify-between pt-2">
                                            <div className="flex gap-2 items-center justify-center">
                                                <label className="block text-sm font-medium mb-2 align-middle mt-1">
                                                    Area Size Limit
                                                </label>
                                                <Tooltip>
                                                    <TooltipTrigger>
                                                        <InfoIcon size="18px" />
                                                    </TooltipTrigger>
                                                    <TooltipContent className="z-100">
                                                        <p>
                                                            {`Your region can not
                                                        exceed an area size of
                                                        ${MAX_REGION_AREA_KMSQ} km²`}
                                                        </p>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </div>
                                            <div
                                                className="text-sm mt-1"
                                                style={{
                                                    color: isOverAreaSizeLimit
                                                        ? "red"
                                                        : "gray",
                                                }}
                                            >
                                                {areaSizeText}
                                            </div>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                                            <div
                                                className=" h-2.5 rounded-full max-w-full"
                                                style={{
                                                    width: areaSizePercent,
                                                    background:
                                                        isOverAreaSizeLimit
                                                            ? "red"
                                                            : "rgb(65 109 251)",
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        <label className="block text-sm font-medium mb-2 mt-5">
                            Area Name
                        </label>
                        <Input
                            value={regionName}
                            onChange={handleRegionNameChange}
                            placeholder="Enter area name..."
                            className={`w-full ${
                                isDuplicateName
                                    ? "border-red-500 focus:border-red-500"
                                    : ""
                            }`}
                            disabled={isEditMode}
                        />
                        {isDuplicateName && (
                            <div className="flex items-center gap-2 text-red-600 text-sm mt-1">
                                <AlertCircle size={14} />
                                <span>
                                    A region with this name already exists
                                </span>
                            </div>
                        )}
                    </div>

                    <div className="flex gap-2">
                        <Button
                            onClick={handleSave}
                            disabled={
                                isEditMode ||
                                isOverAreaSizeLimit ||
                                !regionName.trim() ||
                                currentCoordinates.length === 0 ||
                                isDuplicateName
                            }
                            className="flex-1"
                        >
                            Save Area
                        </Button>
                        <Button
                            variant="outline"
                            onClick={handleClose}
                            className="flex-1"
                            disabled={isEditMode}
                        >
                            Cancel
                        </Button>
                    </div>
                </div>
            </div>

            {/* Shapefile Upload Modal */}
            <ShapefileUploadModal
                isOpen={isShapefileModalOpen}
                onClose={handleCloseShapefileModal}
                onShapefileLoaded={handleShapefileLoaded}
            />
        </>
    );
}

export default AddRegionModal;
