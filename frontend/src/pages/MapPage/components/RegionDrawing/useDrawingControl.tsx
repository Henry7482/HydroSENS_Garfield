import { useState, useCallback, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import { handleShapeDeleted } from "@/redux/regionDrawingActions";
import { CustomDrawingControlRef } from "./CustomDrawingControl";

export type DrawingMode = "polygon" | "rectangle" | "circle" | "edit" | null;

export const useDrawingControl = () => {
    const dispatch = useDispatch();
    const [currentDrawingMode, setCurrentDrawingMode] =
        useState<DrawingMode>(null);
    const drawingControlRef = useRef<CustomDrawingControlRef>(null);

    const { currentCoordinates } = useSelector(
        (state: RootState) => state.regionDrawingState
    );

    const handleDrawingModeChange = useCallback((mode: DrawingMode) => {
        setCurrentDrawingMode(mode);
    }, []);

    const handleShapeCreated = useCallback(() => {
        // Reset drawing mode after shape is created
        setCurrentDrawingMode(null);
    }, []);

    const handleModeComplete = useCallback(() => {
        // Reset drawing mode after edit/delete operations
        setCurrentDrawingMode(null);
    }, []);

    const handleEditMode = useCallback(() => {
        setCurrentDrawingMode("edit");
    }, []);

    const handleDeleteShape = useCallback(() => {
        // Clear shapes through the drawing control ref
        if (drawingControlRef.current) {
            drawingControlRef.current.clearShapes();
        } else {
            // Fallback to just dispatching the action
            dispatch(handleShapeDeleted());
        }
        setCurrentDrawingMode(null);
    }, [dispatch]);

    const handleFinishEdit = useCallback(() => {
        // Finish editing and save the current state
        if (drawingControlRef.current) {
            drawingControlRef.current.finishEdit();
        }
        setCurrentDrawingMode(null);
    }, []);

    const hasActiveShape = currentCoordinates.length > 0;

    return {
        currentDrawingMode,
        hasActiveShape,
        drawingControlRef,
        handleDrawingModeChange,
        handleShapeCreated,
        handleModeComplete,
        handleEditMode,
        handleDeleteShape,
        handleFinishEdit,
    };
};
