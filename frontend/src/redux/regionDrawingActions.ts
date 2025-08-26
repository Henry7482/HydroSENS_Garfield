// Action Types
export const SET_REGION_NAME = "SET_REGION_NAME";
export const SET_CURRENT_COORDINATES = "SET_CURRENT_COORDINATES";
export const RESET_DRAWING_STATE = "RESET_DRAWING_STATE";
export const HANDLE_SHAPE_CREATED = "HANDLE_SHAPE_CREATED";
export const HANDLE_SHAPE_EDITED = "HANDLE_SHAPE_EDITED";
export const HANDLE_SHAPE_DELETED = "HANDLE_SHAPE_DELETED";

// Action Creators
export const setRegionName = (name: string) => ({
    type: SET_REGION_NAME,
    payload: name,
});

export const setCurrentCoordinates = (coordinates: [number, number][]) => ({
    type: SET_CURRENT_COORDINATES,
    payload: coordinates,
});

export const resetDrawingState = () => ({
    type: RESET_DRAWING_STATE,
});

// Complex action creators with logic
export const handleShapeCreated = (layer: any) => {
    return {
        type: HANDLE_SHAPE_CREATED,
        payload: layer,
    };
};

export const handleShapeEdited = (layers: any) => {
    return {
        type: HANDLE_SHAPE_EDITED,
        payload: layers,
    };
};

export const handleShapeDeleted = () => ({
    type: HANDLE_SHAPE_DELETED,
});

// Action Types Definition
export interface SetRegionNameAction {
    type: typeof SET_REGION_NAME;
    payload: string;
}

export interface SetCurrentCoordinatesAction {
    type: typeof SET_CURRENT_COORDINATES;
    payload: [number, number][];
}

export interface ResetDrawingStateAction {
    type: typeof RESET_DRAWING_STATE;
}

export interface HandleShapeCreatedAction {
    type: typeof HANDLE_SHAPE_CREATED;
    payload: any;
}

export interface HandleShapeEditedAction {
    type: typeof HANDLE_SHAPE_EDITED;
    payload: any;
}

export interface HandleShapeDeletedAction {
    type: typeof HANDLE_SHAPE_DELETED;
}

export type RegionDrawingActionTypes =
    | SetRegionNameAction
    | SetCurrentCoordinatesAction
    | ResetDrawingStateAction
    | HandleShapeCreatedAction
    | HandleShapeEditedAction
    | HandleShapeDeletedAction;
