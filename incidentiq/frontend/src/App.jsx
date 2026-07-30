import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/layout/Sidebar";
import HealthDot from "./components/layout/HealthDot";
import ProtectedRoute from "./components/layout/ProtectedRoute";

import Login from "./pages/Login";
import NewIncident from "./pages/NewIncident";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import About from "./pages/About";

function ProtectedLayout() {

    return (

        <div className="app-layout">

            <Sidebar />

            <main className="page-container">

                <HealthDot />

                <Routes>

                    <Route
                        path="/"
                        element={<NewIncident />}
                    />

                    <Route
                        path="/dashboard"
                        element={<Dashboard />}
                    />

                    <Route
                        path="/history"
                        element={<History />}
                    />

                    <Route
                        path="/about"
                        element={<About />}
                    />

                </Routes>

            </main>

        </div>

    );

}

export default function App() {

    return (

        <Routes>

            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/*"
                element={
                    <ProtectedRoute>

                        <ProtectedLayout />

                    </ProtectedRoute>
                }
            />

        </Routes>

    );

}