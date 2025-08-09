import {
    type SettingsActionTypes,
    SET_SELECTED_METRICS,
    SET_ENDMEMBER_TYPE,
    TOGGLE_SETTINGS_MODAL,
    RESET_SETTINGS,
    type MetricKey,
    type EndmemberType,
    AVAILABLE_METRICS,
} from "./settingsActions";
import { loadSettingsFromStorage } from "./middlewares/settingsMiddleware";

// Define the shape of the settings state
export interface SettingsState {
    selectedMetrics: MetricKey[];
    endmemberType: EndmemberType;
    isSettingsModalOpen: boolean;
}

// Load saved settings or use defaults
const savedSettings = loadSettingsFromStorage();

// Default state - all metrics selected, agricultural endmember type
const initialState: SettingsState = {
    selectedMetrics:
        savedSettings?.selectedMetrics ||
        AVAILABLE_METRICS.map((metric) => metric.key),
    endmemberType: savedSettings?.endmemberType || "3",
    isSettingsModalOpen: false,
};

// Reducer
export const settingsReducer = (
    state = initialState,
    action: SettingsActionTypes
): SettingsState => {
    switch (action.type) {
        case SET_SELECTED_METRICS:
            return {
                ...state,
                selectedMetrics: action.payload,
            };
        case SET_ENDMEMBER_TYPE:
            return {
                ...state,
                endmemberType: action.payload,
            };
        case TOGGLE_SETTINGS_MODAL:
            return {
                ...state,
                isSettingsModalOpen: action.payload,
            };
        case RESET_SETTINGS:
            // Reset to default values (all metrics selected, agricultural endmember)
            return {
                ...state,
                selectedMetrics: AVAILABLE_METRICS.map((metric) => metric.key),
                endmemberType: "3",
            };
        default:
            return state;
    }
};
