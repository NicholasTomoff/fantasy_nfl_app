import React, { createContext, useState, useContext, useEffect } from "react";
import { apiFetch } from "@/services/api";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  // ✅ Safely parse stored user
  let initialUser = null;
  try {
    const stored = localStorage.getItem("user");
    if (stored && stored !== "undefined") {
      initialUser = JSON.parse(stored);
    }
  } catch (err) {
    console.warn("⚠️ Failed to parse stored user:", err);
  }

  const [user, setUser] = useState(initialUser);
  const [activeLeagueId, setActiveLeagueId] = useState(null);

  const fetchLeagues = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      console.warn("No token found in localStorage. Skipping fetchLeagues.");
      return;
    }

    try {
      const res = await apiFetch("/api/leagues", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to fetch leagues (${res.status}): ${errorText}`);
      }

      const leagueData = await res.json();
      console.log("✅ Leagues fetched:", leagueData);

      setUser((prevUser) => {
        if (!prevUser) return null;
        const updatedUser = {
          ...prevUser,
          leagues: leagueData,
        };
        console.log("✅ User leagues after login:", updatedUser.leagues || []);
        return updatedUser;
      });
    } catch (err) {
      console.error("❌ Error fetching leagues:", err);
    }
  };


  // Auto-set activeLeagueId once user.leagues are loaded or updated
  useEffect(() => {
    if (!user || !Array.isArray(user.leagues)) return;
    if (user.leagues.length > 0 && !activeLeagueId) {
      const firstLeague = user.leagues[0];
      if (firstLeague?.id) {
        console.log("✅ Setting activeLeagueId to:", firstLeague.id);
        setActiveLeagueId(firstLeague.id);
      }
    }
  }, [user, activeLeagueId]);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setUser(null);
        return;
      }

      try {
        const res = await apiFetch("/api/users/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          if (res.status === 401) {
            if (process.env.NODE_ENV === "development") {
              console.warn("🔒 Not logged in or token expired (401)");
            }
            setUser(null);
            localStorage.removeItem("user");
            localStorage.removeItem("token");
            return;
          }
          throw new Error("Failed to load user");
        }

        const data = await res.json();
        setUser(data);
        localStorage.setItem("user", JSON.stringify(data));

        await fetchLeagues(); // Fetch leagues after setting user
      } catch (err) {
        console.error("❌ Unexpected error loading user:", err);
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
      }
    };

    fetchUser();
  }, []);

  const login = (data) => {
    localStorage.setItem("user", JSON.stringify(data.user));
    localStorage.setItem("token", data.token);
    setUser(data.user);
    fetchLeagues();
  };

  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, login, logout, activeLeagueId, setActiveLeagueId }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);

export default UserContext;
