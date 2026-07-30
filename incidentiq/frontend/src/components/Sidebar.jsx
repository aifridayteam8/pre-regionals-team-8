import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside className="sidebar">

      <h2>IncidentIQ</h2>

      <nav>

        <NavLink to="/">
          New Incident
        </NavLink>

        <NavLink to="/history">
          History
        </NavLink>

        <NavLink to="/dashboard">
          Dashboard
        </NavLink>

        <NavLink to="/about">
          About
        </NavLink>

      </nav>

    </aside>
  );
}