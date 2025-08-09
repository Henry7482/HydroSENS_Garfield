import {
  FETCH_HYDROSENS_REQUEST,
  FETCH_HYDROSENS_SUCCESS,
  FETCH_HYDROSENS_FAILURE,
} from "./dashboardActions";
import { HydrosensOutputs } from "@/types/hydrosens";

export interface DashboardState {
  loading: boolean;
  error?: string;
  outputs: HydrosensOutputs;   // date-keyed metrics
}

const initialState: DashboardState = {
  loading: false,
  outputs: {},
};

export const dashboardReducer = (
  state = initialState,
  action: any
): DashboardState => {
  switch (action.type) {
    case FETCH_HYDROSENS_REQUEST:
      return { ...state, loading: true, error: undefined };
    case FETCH_HYDROSENS_SUCCESS:
      return { ...state, loading: false, outputs: action.payload };
    case FETCH_HYDROSENS_FAILURE:
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
};
