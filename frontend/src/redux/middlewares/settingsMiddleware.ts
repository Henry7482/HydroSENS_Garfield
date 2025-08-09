import { Middleware } from "@reduxjs/toolkit";
import { RootState } from "../store";
import {
    SET_SELECTED_METRICS,
    SET_ENDMEMBER_TYPE,
    RESET_SETTINGS,
} from "../settingsActions";

const SETTINGS_STORAGE_KEY = "hydrosens_settings";

// Middleware to save settings to localStorage
export const settingsMiddleware: Middleware<{}, RootState> =
    (store) => (next) => (action) => {
        const result = next(action);

        // Save to localStorage when settings actions are dispatched
        if (
            action.type === SET_SELECTED_METRICS ||
            action.type === SET_ENDMEMBER_TYPE ||
            action.type === RESET_SETTINGS
        ) {
            const state = store.getState();
            try {
                const settingsToSave = {
                    selectedMetrics: state.settings.selectedMetrics,
                    endmemberType: state.settings.endmemberType,
                };
                localStorage.setItem(
                    SETTINGS_STORAGE_KEY,
                    JSON.stringify(settingsToSave)
                );
            } catch (error) {
                console.warn("Failed to save settings to localStorage:", error);
            }
        }

        return result;
    };

// Function to load settings from localStorage
export const loadSettingsFromStorage = () => {
    try {
        const savedSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (savedSettings) {
            return JSON.parse(savedSettings);
        }
    } catch (error) {
        console.warn("Failed to load settings from localStorage:", error);
    }
    return null;
};
