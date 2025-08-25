import React, { useRef } from "react";
import { FeatureGroup } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import { useDispatch } from "react-redux";
import {
    handleShapeCreated,
    handleShapeEdited,
    handleShapeDeleted,
} from "@/redux/regionDrawingActions";
import { drawOptions } from "./drawOptions";

function RegionDrawingEditControl() {
    const dispatch = useDispatch();

    const featureGroupRef = useRef<any>(null);

    const handleCreated = (e: any) => {
        const layer = e.layer;
        dispatch(handleShapeCreated(layer));

        // Clear previous shapes and add new layer
        if (featureGroupRef.current) {
            featureGroupRef.current.clearLayers();
            featureGroupRef.current.addLayer(layer);
        }
    };

    const handleEdited = (e: any) => {
        dispatch(handleShapeEdited(e.layers));
    };

    const handleDeleted = () => {
        dispatch(handleShapeDeleted());
    };

    return (
        <FeatureGroup ref={featureGroupRef}>
            <EditControl
                position="topright"
                onCreated={handleCreated}
                onEdited={handleEdited}
                onDeleted={handleDeleted}
                draw={drawOptions}
                edit={{
                    remove: true,
                    edit: {},
                }}
            />
        </FeatureGroup>
    );
}

export default RegionDrawingEditControl;
