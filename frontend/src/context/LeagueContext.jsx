// LeagueContext.jsx
import React, { createContext, useContext, useState, useEffect } from "react";

const LeagueContext = createContext();

export const LeagueProvider = ({ children }) => {
    const [activeLeagueId, setActiveLeagueId] = useState(null);
    const [activeLeagueName, setActiveLeagueName] = useState(null);

    // Load from localStorage on mount
    useEffect(() => {
        const storedId = localStorage.getItem("activeLeagueId");
        if (storedId) {
            setActiveLeagueId(Number(storedId));
        }
    }, []);

    // Save to localStorage on change
    useEffect(() => {
        if (activeLeagueId !== null) {
            localStorage.setItem("activeLeagueId", activeLeagueId);
        }
    }, [activeLeagueId]);

    const setActiveLeague = (id, name = null) => {
        setActiveLeagueId(id);
        if (name) setActiveLeagueName(name);
    };

    return (
        <LeagueContext.Provider
            value={{ activeLeagueId, setActiveLeagueId, activeLeagueName, setActiveLeagueName, setActiveLeague }}
        >
            {children}
        </LeagueContext.Provider>
    );
};

export const useLeague = () => useContext(LeagueContext);
