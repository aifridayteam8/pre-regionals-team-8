import { useState } from "react";

import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import "../styles/login.css";

export default function Login() {

    const navigate = useNavigate();

    const { login } = useAuth();

    const [username, setUsername] = useState("");

    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");

    async function handleSubmit(e) {

        e.preventDefault();

        setLoading(true);

        setError("");

        try {

            await login(username, password);

            navigate("/");

        }

        catch (err) {

            setError(err.message);

        }

        finally {

            setLoading(false);

        }

    }

    return (

        <div className="login-page">

            <div className="login-card">

                <h1>IncidentIQ</h1>

                <p className="subtitle">
                    AI Infrastructure Incident Analysis
                </p>

                <form onSubmit={handleSubmit}>

                    <label>

                        Username

                        <input
                            type="text"
                            value={username}
                            onChange={(e) =>
                                setUsername(e.target.value)
                            }
                            required
                        />

                    </label>

                    <label>

                        Password

                        <input
                            type="password"
                            value={password}
                            onChange={(e) =>
                                setPassword(e.target.value)
                            }
                            required
                        />

                    </label>

                    {error && (
                        <div className="error">

                            {error}

                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                    >

                        {
                            loading
                                ? "Signing In..."
                                : "Sign In"
                        }

                    </button>

                </form>

            </div>

        </div>

    );

}