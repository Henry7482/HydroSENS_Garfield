import {
    RegionDrawingActionTypes,
    SET_REGION_NAME,
    SET_CURRENT_COORDINATES,
    RESET_DRAWING_STATE,
    HANDLE_SHAPE_CREATED,
    HANDLE_SHAPE_EDITED,
    HANDLE_SHAPE_DELETED,
} from "./regionDrawingActions";

// Define the shape of the region drawing state
export interface RegionDrawingState {
    regionName: string;
    currentCoordinates: [number, number][];
}

const initialState: RegionDrawingState = {
    regionName: "",
    currentCoordinates: [],
};

// Helper function to extract coordinates from layer
const extractCoordinatesFromLayer = (layer: any): [number, number][] => {
    const coordinates: [number, number][] = [];

    if (layer.getLatLngs) {
        // For polygons and rectangles
        const latLngs = Array.isArray(layer.getLatLngs()[0])
            ? layer.getLatLngs()[0]
            : layer.getLatLngs();
        coordinates.push(
            ...latLngs.map((latLng: any) => [latLng.lat, latLng.lng])
        );
    } else if (layer.getLatLng && layer.getRadius) {
        // For circles, create polygon approximation
        const center = layer.getLatLng();
        const radius = layer.getRadius();
        const points = 20;

        for (let i = 0; i < points; i++) {
            const angle = (i * 2 * Math.PI) / points;
            const lat = center.lat + (radius / 111000) * Math.cos(angle);
            const lng =
                center.lng +
                (radius / (111000 * Math.cos((center.lat * Math.PI) / 180))) *
                    Math.sin(angle);
            coordinates.push([lat, lng]);
        }
    }

    return coordinates;
};

// Reducer
export const regionDrawingReducer = (
    state = initialState,
    action: RegionDrawingActionTypes
): RegionDrawingState => {
    switch (action.type) {
        case SET_REGION_NAME:
            return {
                ...state,
                regionName: action.payload,
            };
        case SET_CURRENT_COORDINATES:
            return {
                ...state,
                currentCoordinates: action.payload,
            };
        case RESET_DRAWING_STATE:
            return initialState;
        case HANDLE_SHAPE_CREATED: {
            const coordinates = extractCoordinatesFromLayer(action.payload);
            return {
                ...state,
                currentCoordinates: coordinates,
            };
        }
        case HANDLE_SHAPE_EDITED: {
            let coordinates: [number, number][] = [];

            action.payload.eachLayer((layer: any) => {
                coordinates = extractCoordinatesFromLayer(layer);
            });

            return {
                ...state,
                currentCoordinates: coordinates,
            };
        }
        case HANDLE_SHAPE_DELETED:
            return {
                ...state,
                currentCoordinates: [],
            };
        default:
            return state;
    }
};
