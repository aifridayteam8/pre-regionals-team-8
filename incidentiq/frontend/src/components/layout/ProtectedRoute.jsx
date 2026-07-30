import { Navigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute({ children }) {

    const {
        loading,
        isAuthenticated
    } = useAuth();

    if (loading) {

        return (
            <div
                style={{
                    height: "100vh",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    fontSize: "20px"
                }}
            >
                Loading...
            </div>
        );

    }

    if (!isAuthenticated) {

        return <Navigate to="/login" replace />;

    }

    return children;

}