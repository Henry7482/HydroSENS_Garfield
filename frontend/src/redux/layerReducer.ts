// redux/layerReducer.ts
import {
    FETCH_LAYERS_REQUEST,
    FETCH_LAYERS_SUCCESS,
    FETCH_LAYERS_FAILURE,
    SET_SELECTED_DATE,
    SET_SELECTED_LAYER,
    CLEAR_LAYERS,
    SET_LAYER_DATA_RANGE,
} from "./layerActions";
import { DateLayers } from "@/api/layers";

export interface LayerState {
    loading: boolean;
    error?: string;
    dateLayers: DateLayers[];
    selectedDate: string | null;
    selectedLayer: string | null;
    layerDataRanges: Record<string, { min: number; max: number }>;
}

const initialState: LayerState = {
    loading: false,
    dateLayers: [],
    selectedDate: null,
    selectedLayer: null,
    layerDataRanges: {},
};

export const layerReducer = (state = initialState, action: any): LayerState => {
    switch (action.type) {
        case FETCH_LAYERS_REQUEST:
            return { ...state, loading: true, error: undefined };
        case FETCH_LAYERS_SUCCESS:
            return {
                ...state,
                loading: false,
                dateLayers: action.payload,
                // Auto-select first date and default to "No Layer"
                selectedDate:
                    action.payload.length > 0 ? action.payload[0].date : null,
                selectedLayer: "none", // Default to "No Layer" instead of first actual layer
            };
        case FETCH_LAYERS_FAILURE:
            return { ...state, loading: false, error: action.payload };
        case SET_SELECTED_DATE:
            return {
                ...state,
                selectedDate: action.payload,
                // Reset selected layer when date changes
                selectedLayer: null,
            };
        case SET_SELECTED_LAYER:
            return { ...state, selectedLayer: action.payload };
        case SET_LAYER_DATA_RANGE:
            return {
                ...state,
                layerDataRanges: {
                    ...state.layerDataRanges,
                    [action.payload.layerKey]: action.payload.range,
                },
            };
        case CLEAR_LAYERS:
            return initialState;
        default:
            return state;
    }
};
