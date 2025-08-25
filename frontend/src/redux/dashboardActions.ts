import { ThunkAction } from "redux-thunk";
import { RootState } from "@/redux/store";
import { HydrosensOutputs } from "@/types/hydrosens";
import { regionToShapefileZip } from "@/utils/regionToShapefile";
import { AnyAction } from "@reduxjs/toolkit";
import { postHydrosens } from "@/api/hydrosens";
// import { postHydrosens } from "@/api/mocks/hydrosens"; // Use this if you don't want to connect to BE

/* Action types */
export const FETCH_HYDROSENS_REQUEST = "FETCH_HYDROSENS_REQUEST";
export const FETCH_HYDROSENS_SUCCESS = "FETCH_HYDROSENS_SUCCESS";
export const FETCH_HYDROSENS_FAILURE = "FETCH_HYDROSENS_FAILURE";

/* Action creators */
export const fetchHydrosensRequest = () => ({ type: FETCH_HYDROSENS_REQUEST });
export const fetchHydrosensSuccess = (data: HydrosensOutputs) => ({
    type: FETCH_HYDROSENS_SUCCESS,
    payload: data,
});
export const fetchHydrosensFailure = (msg: string) => ({
    type: FETCH_HYDROSENS_FAILURE,
    payload: msg,
});

/* Thunk that calls the API */
export const fetchHydrosens =
    (): ThunkAction<void, RootState, unknown, AnyAction> =>
    async (dispatch, getState) => {
        try {
            dispatch(fetchHydrosensRequest());

            const { regionState, dateState, settings } = getState();
            const selectedIndex = regionState.selectedRegionIndex;
            const region = regionState.regions[selectedIndex!];

            // Check if any metrics are selected
            if (
                !settings.selectedMetrics ||
                settings.selectedMetrics.length === 0
            ) {
                throw new Error(
                    "No metrics selected. Please select metrics in settings."
                );
            }

            // Format date as yyyy-mm-dd
            const formatLocal = (d: Date) => {
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, "0");
                const day = String(d.getDate()).padStart(2, "0");
                return `${year}-${month}-${day}`;
            };

            // Convert coordinates to [lon, lat]
            const coordinates = region.coordinates.map(([lat, lon]) => [
                lon,
                lat,
            ]);

            // Build statistics string from selected metrics in settings
            // const statisticsString = settings.selectedMetrics.join(", ");
            const fullStatisticsString =
                "curve-number, ndvi, precipitation, soil-fraction, temperature, vegetation-fraction";

            const payload = {
                amc: 2,
                precipitation: 100.0,
                crs: "EPSG:4326",
                start_date: formatLocal(new Date(dateState.startDate)),
                end_date: formatLocal(new Date(dateState.endDate)),
                coordinates: coordinates,
                num_coordinates: coordinates.length,
                statistics: fullStatisticsString,
                region_name: region.name || "Unknown Region",
                endmember: Number(settings.endmemberType),
            };

            console.log("Payload with dynamic statistics:", payload);
            console.log("Selected metrics:", settings.selectedMetrics);

            const res = await postHydrosens(payload);
            dispatch(fetchHydrosensSuccess(res));
        } catch (err: any) {
            dispatch(fetchHydrosensFailure(err.message || "Unknown error"));
        }
    };
