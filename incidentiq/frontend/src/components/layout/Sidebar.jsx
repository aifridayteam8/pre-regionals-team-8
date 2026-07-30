import { NavLink, useNavigate } from "react-router-dom";

import Icon from "../common/Icon";
import { useAuth } from "../../context/AuthContext.jsx";

const NAV_SECTIONS = [
  {
    title: "Operate",
    items: [
      { to: "/", label: "New Incident", icon: "upload" },
      { to: "/history", label: "History", icon: "history" },
    ],
  },
  {
    title: "Analyze",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
      { to: "/about", label: "About", icon: "info" },
    ],
  },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo">
          <Icon name="shield" size={18} />
        </span>

        <span>
          <span className="sidebar-brand-name">IncidentIQ</span>
          <span className="sidebar-brand-sub">AI Incident Reports</span>
        </span>
      </div>

      {NAV_SECTIONS.map((section) => (
        <nav key={section.title} className="sidebar-section">
          <p className="sidebar-section-title">{section.title}</p>

          {section.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                isActive ? "sidebar-link is-active" : "sidebar-link"
              }
            >
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      ))}

      <div className="sidebar-footer">
        {user?.username && (
          <span className="sidebar-user">
            Signed in as <strong>{user.username}</strong>
          </span>
        )}

        <button type="button" className="sidebar-logout" onClick={handleLogout}>
          <Icon name="logout" size={14} />
          Log out
        </button>

        <span>IncidentIQ v0.4.0</span>
      </div>
    </aside>
  );
}
