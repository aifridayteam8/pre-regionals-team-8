import { createContext, useContext, useEffect, useState } from "react";

import {
    login as loginApi,
    logout as logoutApi,
    getCurrentUser
} from "../api/auth";

const AuthContext = createContext();

export function AuthProvider({ children }) {

    const [user, setUser] = useState(null);

    const [loading, setLoading] = useState(true);

    useEffect(() => {

        const existingUser = getCurrentUser();

        if (existingUser) {
            setUser(existingUser);
        }

        setLoading(false);

    }, []);

    async function login(username, password) {

        const result = await loginApi(username, password);

        setUser(result.user);

        return result;
    }

    function logout() {

        logoutApi();

        setUser(null);
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                login,
                logout,
                isAuthenticated: !!user
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {

    return useContext(AuthContext);

}