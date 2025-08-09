import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";
import { regionReducer } from "./regionReducer";
import { dateReducer } from "./dateReducers";
import { viewModeReducer } from "./viewModeReducers";
import { regionDrawingReducer } from "./regionDrawingReducer";
import { dashboardReducer } from "./dashboardReducer";
import { settingsReducer } from "./settingsReducer";
import { layerReducer } from "./layerReducer";
import { settingsMiddleware } from "./middlewares/settingsMiddleware";

// Combine all reducers
const rootReducer = combineReducers({
    regionState: regionReducer,
    dateState: dateReducer,
    viewModeState: viewModeReducer,
    regionDrawingState: regionDrawingReducer,
    dashboard: dashboardReducer,
    settings: settingsReducer,
    layers: layerReducer,
});

// Create the store with settings middleware
export const store = configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(settingsMiddleware),
});

// Define the RootState type for TypeScript
export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;
