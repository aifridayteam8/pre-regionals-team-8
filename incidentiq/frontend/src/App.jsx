import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";

import NewIncident from "./pages/NewIncident";
import History from "./pages/History";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";

import { getHealth } from "./api/client";

export default function App() {
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    let cancelled = false;

    function check() {
      getHealth()
        .then(() => !cancelled && setHealth("healthy"))
        .catch(() => !cancelled && setHealth("down"));
    }

    check();
    const timer = setInterval(check, 30_000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="app-main">
        <Topbar health={health} />

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
