import { subDays } from "date-fns";
import { DateActionTypes, SET_START_DATE, SET_END_DATE } from "./dateActions";

// Define the shape of the date state
export interface DateState {
    startDate: number;
    endDate: number;
}

const initialState: DateState = {
    startDate: subDays(new Date(), 12).getTime(),
    endDate: subDays(new Date(), 5).getTime(),
};

// Reducer
export const dateReducer = (
    state = initialState,
    action: DateActionTypes
): DateState => {
    switch (action.type) {
        case SET_START_DATE:
            return {
                ...state,
                startDate: action.payload,
            };
        case SET_END_DATE:
            return {
                ...state,
                endDate: action.payload,
            };
        default:
            return state;
    }
};
