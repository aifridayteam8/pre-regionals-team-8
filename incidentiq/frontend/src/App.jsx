import { Routes, Route } from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";

import NewIncident from "./pages/NewIncident";
import History from "./pages/History";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />

      <div className="app-main">
        <Topbar health="healthy" />

        <main className="page-container">
          <Routes>
            <Route path="/" element={<NewIncident />} />
            <Route path="/history" element={<History />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
