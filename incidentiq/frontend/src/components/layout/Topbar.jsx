import { useLocation } from "react-router-dom";

import Icon from "../common/Icon";
import HealthDot from "./HealthDot";

const SECTION_BY_PATH = {
  "/": "New Incident",
  "/history": "History",
  "/dashboard": "Dashboard",
  "/about": "About",
};

export default function Topbar({ health = "checking" }) {
  const { pathname } = useLocation();

  return (
    <div className="topbar">
      <nav className="topbar-breadcrumb" aria-label="Breadcrumb">
        <span>IncidentIQ</span>
        <span aria-hidden="true">/</span>
        <span className="topbar-breadcrumb-current">
          {SECTION_BY_PATH[pathname] ?? "Not found"}
        </span>
      </nav>

      <span className="topbar-spacer" />

      <label className="topbar-search">
        <Icon name="search" size={14} />
        <input type="search" placeholder="Search incidents, services..." aria-label="Search" />
        <kbd>/</kbd>
      </label>

      <HealthDot status={health} />

      <span className="topbar-avatar" title="Signed in as SRE on-call">
        SR
      </span>
    </div>
  );
}
