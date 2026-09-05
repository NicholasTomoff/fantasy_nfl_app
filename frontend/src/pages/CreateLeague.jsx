import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/services/api";

const CreateLeague = () => {
    const { user } = useUser();
    const navigate = useNavigate();

    const [name, setName] = useState("");
    const [minPlayers, setMinPlayers] = useState(4);
    const [seasonYear, setSeasonYear] = useState(new Date().getFullYear());
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError("");
        if (!name.trim()) {
            setError("League name is required");
            return;
        }
        setLoading(true);

        const token = localStorage.getItem("token");  // ✅ FIX: get token here
        if (!token) {
            console.warn("No auth token found in localStorage");
            return;
        }

        try {
            // No trailing slash: the route is registered as "/api/leagues", and
            // FastAPI answers "/api/leagues/" with a 307 the browser refuses to
            // follow cross-origin on a preflighted request.
            // Headers are left to apiFetch, which attaches the bearer token
            // correctly -- options.headers is spread last and would override it.
            const res = await apiFetch("/api/leagues", {
                method: "POST",
                body: JSON.stringify({ name, min_players: minPlayers, season_year: seasonYear }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to create league");
            }

            const newLeague = await res.json();
            navigate("/leagues");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    if (!user) {
        return <p>You must be logged in to create a league.</p>;
    }

    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-gray-800 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-yellow-400 mb-4">Create a New League</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block mb-1">League Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full p-2 rounded bg-gray-700 border border-gray-600"
                        required
                    />
                </div>

                <div>
                    <label className="block mb-1">Minimum Players to Start</label>
                    <input
                        type="number"
                        min={2}
                        max={100}
                        value={minPlayers}
                        onChange={(e) => setMinPlayers(Number(e.target.value))}
                        className="w-full p-2 rounded bg-gray-700 border border-gray-600"
                    />
                </div>

                <div>
                    <label className="block mb-1">Season Year</label>
                    <input
                        type="number"
                        value={seasonYear}
                        onChange={(e) => setSeasonYear(Number(e.target.value))}
                        className="w-full p-2 rounded bg-gray-700 border border-gray-600"
                    />
                </div>

                {error && <div className="text-red-500">{error}</div>}

                <Button type="submit" disabled={loading} className="w-full bg-yellow-500 hover:bg-yellow-600 text-black">
                    {loading ? "Creating..." : "Create League"}
                </Button>
            </form>
        </div>
    );
};

export default CreateLeague;
