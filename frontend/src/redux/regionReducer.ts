import { calculatePolygonArea } from "@/utils/map";
import { saveRegionsToStorage } from "@/utils/localStorage";
import initialRegions from "../data/initialRegions";
import { Region } from "../types/region";
import {
    RegionActionTypes,
    ADD_REGION,
    DELETE_REGION,
    SELECT_REGION,
    DESELECT_REGION,
    LOAD_REGIONS,
    CLEAR_ALL_REGIONS,
} from "./regionActions";
import { generateRandomColor } from "@/utils/colors";

// Define the shape of the region state
export interface RegionState {
    regions: Region[];
    selectedRegionIndex: number | null;
}

const initialState: RegionState = {
    regions: initialRegions,
    selectedRegionIndex: null,
};

// Helper function to save state to localStorage after mutations
const saveStateToStorage = (regions: Region[]) => {
    try {
        saveRegionsToStorage(regions);
    } catch (error) {
        console.error("Failed to save regions to storage in reducer:", error);
    }
};

// Reducer
export const regionReducer = (
    state = initialState,
    action: RegionActionTypes
): RegionState => {
    switch (action.type) {
        case SELECT_REGION:
            return {
                ...state,
                selectedRegionIndex: action.payload,
            };
        case DESELECT_REGION:
            return {
                ...state,
                selectedRegionIndex: null,
            };
        case DELETE_REGION: {
            // Create a new array without the region at the specified index
            const updatedRegions = state.regions.filter(
                (_, index) => index !== action.payload
            );

            // Save to localStorage
            saveStateToStorage(updatedRegions);

            // Reset the selected region if we deleted the selected one
            let newSelectedIndex = state.selectedRegionIndex;
            if (state.selectedRegionIndex === action.payload) {
                newSelectedIndex = null;
            } else if (
                state.selectedRegionIndex !== null &&
                state.selectedRegionIndex > action.payload
            ) {
                // Adjust selected index if it's after the deleted item
                newSelectedIndex = state.selectedRegionIndex - 1;
            }

            return {
                ...state,
                regions: updatedRegions,
                selectedRegionIndex: newSelectedIndex,
            };
        }
        case ADD_REGION: {
            const newRegion = {
                ...action.payload,
                color: action.payload.color || generateRandomColor(),
                area:
                    action.payload.area ||
                    calculatePolygonArea(action.payload.coordinates),
            };

            const newRegions = [...state.regions, newRegion];
            
            // Save to localStorage
            saveStateToStorage(newRegions);

            return {
                ...state,
                regions: newRegions,
            };
        }
        case LOAD_REGIONS:
            return {
                ...state,
                regions: action.payload,
                selectedRegionIndex: null, // Clear selection when loading
            };
        case CLEAR_ALL_REGIONS: {
            // Save empty array to localStorage
            saveStateToStorage([]);
            
            return {
                ...state,
                regions: [],
                selectedRegionIndex: null,
            };
        }
        default:
            return state;
    }
};

export default regionReducer;