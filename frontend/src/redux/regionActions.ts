import { Region } from "@/types/region";
import { saveRegionsToStorage, loadRegionsFromStorage } from "@/utils/localStorage";

// Action Types
export const SELECT_REGION = "SELECT_REGION";
export const DELETE_REGION = "DELETE_REGION";
export const ADD_REGION = "ADD_REGION";
export const DESELECT_REGION = "DESELECT_REGION";
export const LOAD_REGIONS = "LOAD_REGIONS";
export const CLEAR_ALL_REGIONS = "CLEAR_ALL_REGIONS";
// Action Creators
export const selectRegion = (regionIndex: number | null) => ({
    type: SELECT_REGION,
    payload: regionIndex,
});

export const deleteRegion = (regionIndex: number) => ({
    type: DELETE_REGION,
    payload: regionIndex,
});

export const addRegion = (region: Region) => ({
    type: ADD_REGION,
    payload: region,
});

export const deselectRegion = (): DeselectRegionAction => ({
    type: DESELECT_REGION,
});

export const loadRegions = (regions: Region[]): LoadRegionsAction => ({
    type: LOAD_REGIONS,
    payload: regions,
});

export const clearAllRegions = (): ClearAllRegionsAction => ({
    type: CLEAR_ALL_REGIONS,
});
// Thunk Actions (if you're using redux-thunk)
export const loadRegionsFromStorageThunk = () => {
    return (dispatch: any) => {
        try {
            const regions = loadRegionsFromStorage();
            dispatch(loadRegions(regions));
        } catch (error) {
            console.error("Failed to load regions from storage:", error);
        }
    };
};

export const saveRegionsToStorageThunk = () => {
    return (dispatch: any, getState: any) => {
        try {
            const { regionState } = getState();
            saveRegionsToStorage(regionState.regions);
        } catch (error) {
            console.error("Failed to save regions to storage:", error);
        }
    };
};

export const clearAllRegionsThunk = () => {
    return (dispatch: any) => {
        dispatch(clearAllRegions());
        // Also clear from localStorage
        try {
            const { clearRegionsFromStorage } = require("@/utils/localStorage");
            clearRegionsFromStorage();
        } catch (error) {
            console.error("Failed to clear regions from storage:", error);
        }
    };
};

// Action Types Definition
export interface SelectRegionAction {
    type: typeof SELECT_REGION;
    payload: number | null;
}

export interface DeleteRegionAction {
    type: typeof DELETE_REGION;
    payload: number;
}

export interface AddRegionAction {
    type: typeof ADD_REGION;
    payload: Region;
}

export interface DeselectRegionAction {
    type: typeof DESELECT_REGION;
}

export interface LoadRegionsAction {
    type: typeof LOAD_REGIONS;
    payload: Region[];
}

export interface ClearAllRegionsAction {
    type: typeof CLEAR_ALL_REGIONS;
}

export type RegionActionTypes =
    | AddRegionAction
    | DeleteRegionAction
    | SelectRegionAction
    | DeselectRegionAction
    | LoadRegionsAction
    | ClearAllRegionsAction;

