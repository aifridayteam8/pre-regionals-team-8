import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Sidebar() {

    const navigate = useNavigate();

    const {
        logout,
        user
    } = useAuth();

    function handleLogout() {

        logout();

        navigate("/login");

    }

    return (

        <aside className="sidebar">

            <h2>IncidentIQ</h2>

            <div
                style={{
                    marginBottom: "20px",
                    fontSize: "14px"
                }}
            >

                Welcome

                <br />

                <strong>

                    {user?.username}

                </strong>

            </div>

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

            <button
                onClick={handleLogout}
                style={{
                    marginTop: "auto",
                    padding: "12px",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    background: "#dc2626",
                    color: "#fff"
                }}
            >

                Logout

            </button>

        </aside>

    );

}