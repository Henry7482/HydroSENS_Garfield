import { Routes, Route } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useEffect } from "react";
import MapPage from "./pages/MapPage/MapPage";
import { loadRegionsFromStorageThunk } from "./redux/regionActions";
import { AppDispatch } from "./redux/store";

function AppContent() {
    const dispatch = useDispatch<AppDispatch>();

    // Load regions from localStorage on app initialization
    useEffect(() => {
        dispatch(loadRegionsFromStorageThunk());
    }, [dispatch]);

    return (
        <Routes>
            <Route path="/" element={<MapPage />} />
            <Route path="*" element={<MapPage />} />
        </Routes>
    );
}

export default AppContent;