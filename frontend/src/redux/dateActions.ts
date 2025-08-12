// Action Types
export const SET_START_DATE = "SET_START_DATE";
export const SET_END_DATE = "SET_END_DATE";

// Action Creators - modified to handle timestamps
export const setStartDate = (date: number) => ({
    type: SET_START_DATE,
    payload: date,
});

export const setEndDate = (date: number) => ({
    type: SET_END_DATE,
    payload: date,
});

// Action Types Definition - updated to use number (timestamp) instead of Date
export interface SetStartDateAction {
    type: typeof SET_START_DATE;
    payload: number;
}

export interface SetEndDateAction {
    type: typeof SET_END_DATE;
    payload: number;
}

export type DateActionTypes = SetStartDateAction | SetEndDateAction;
