import React, { createContext, useContext, useState, useEffect } from "react";
import { apiFetch } from "@/services/api";

const SeasonContext = createContext();

export const SeasonProvider = ({ children }) => {
    const today = new Date();
    const month = today.getMonth(); // 0 = Jan, 6 = Jul
    const year = today.getFullYear();

    const activeSeason = month >= 6 ? year : year - 1;

    const [season, setSeason] = useState(activeSeason);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [currentFinalizedWeek, setCurrentFinalizedWeek] = useState(null);

    // Initial load of season
    useEffect(() => {
        const fetchInitial = async () => {
            const token = localStorage.getItem("token");
            try {
                const res = await apiFetch("/api/seasons/current", {
                    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                });
                const data = await res.json();
                const fetchedSeason = data?.season || activeSeason;
                setSeason(parseInt(fetchedSeason, 10));
            } catch (err) {
                console.error("❌ Error fetching initial season:", err);
            }
        };
        fetchInitial();
    }, []);

    // Refetch currentWeek & currentFinalizedWeek whenever season changes
    useEffect(() => {
        const fetchWeeksForSeason = async () => {
            if (!season) return;
            const token = localStorage.getItem("token");

            try {
                // Fetch current week
                const weekRes = await apiFetch(`/api/weeks/current?season=${season}`, {
                    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                });
                const { week } = await weekRes.json();

                // Fetch current finalized week
                const finalizedRes = await apiFetch(`/api/weeks/finalized?season=${season}`, {
                    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                });
                const finalizedData = await finalizedRes.json();
                const finalizedWeek = finalizedData.week;

                // For previous season, default currentWeek to 18 (if needed)
                setCurrentWeek(season === activeSeason - 1 ? 18 : week);
                setCurrentFinalizedWeek(finalizedWeek);

                console.log("📅 Season & weeks updated:", {
                    season,
                    activeSeason,
                    currentWeek: season === activeSeason - 1 ? 18 : week,
                    currentFinalizedWeek: finalizedWeek,
                });
            } catch (err) {
                console.error("❌ Error fetching weeks for season:", err);
            }
        };

        fetchWeeksForSeason();
    }, [season]);

    return (
        <SeasonContext.Provider
            value={{
                season,
                setSeason,
                currentWeek,
                setCurrentWeek,
                currentFinalizedWeek,
                setCurrentFinalizedWeek,
            }}
        >
            {children}
        </SeasonContext.Provider>
    );
};

export const useSeason = () => useContext(SeasonContext);
