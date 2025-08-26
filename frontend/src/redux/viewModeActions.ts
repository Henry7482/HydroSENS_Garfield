// Action Types
export const SET_VIEW_MODE = "SET_VIEW_MODE";

// Action Creators - modified to handle timestamps
export const setViewMode = (viewMode: string) => ({
    type: SET_VIEW_MODE,
    payload: viewMode,
});

// Action Types Definition - updated to use number (timestamp) instead of Date
export interface SetViewModeAction {
    type: typeof SET_VIEW_MODE;
    payload: string;
}

export type ViewModeActionTypes = SetViewModeAction;
