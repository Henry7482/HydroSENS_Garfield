import { BrowserRouter, Route, Routes } from "react-router-dom";
import MapPage from "./pages/MapPage/MapPage";
import { Provider } from "react-redux";
import { store } from "./redux/store";
import AppContent from "./AppContent";

function App() {
    return (
        <Provider store={store}>
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        </Provider>
    );
}

export default App;