import React, { useState, useEffect, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";
import {
  Home,
  Users,
  UserPlus,
  BarChart2,
  ListOrdered,
  Info,
  Zap,
} from "lucide-react";
import { useSeason } from "@/context/SeasonContext";
import { useLeague } from "@/context/LeagueContext";

const Layout = ({ children }) => {
  const {
    user,
    logout,
    selectedSeason,
    setSelectedSeason,
  } = useUser();

  const location = useLocation();
  const navigate = useNavigate();

  const rawName = user?.name;
  const isValidName = typeof rawName === "string" && rawName.trim().length > 0;
  const nameParts = isValidName ? rawName.trim().split(" ") : ["Player"];
  const firstName = nameParts[0];
  const firstInitial = nameParts[0]?.charAt(0).toUpperCase() || "U";
  const lastInitial = nameParts[1]?.charAt(0).toUpperCase() || "";
  const initials = `${firstInitial}${lastInitial}`;

  const [isOpen, setIsOpen] = useState(false);
  const [leagueRank, setLeagueRank] = useState("-");
  const [globalRank, setGlobalRank] = useState("-");
  const [currentStreak, setCurrentStreak] = useState(0);

  const { season, currentFinalizedWeek } = useSeason();
  const { activeLeagueId, setActiveLeagueId } = useLeague();

  const isLeagueOwner = user?.leagues?.some(
    (lg) =>
      Number(lg.id) === Number(activeLeagueId) &&
      Number(lg.created_by_user_id) === Number(user?.id)
  );



  const [avatarMenuOpen, setAvatarMenuOpen] = useState(false);

  useEffect(() => {
    if (user?.leagues?.length && !activeLeagueId) {
      setActiveLeagueId(user.leagues[0].id);
    }
  }, [user?.leagues, activeLeagueId, setActiveLeagueId]);

  const fetchRanks = useCallback(
    async (season, currentFinalizedWeek) => {
      const token = localStorage.getItem("token");
      if (!token || !activeLeagueId || !season || !currentFinalizedWeek) return;

      try {
        const res = await apiFetch(
          `/api/user/ranks?league_id=${activeLeagueId}&week=${currentFinalizedWeek}&season=${season}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (!res.ok) throw new Error("Failed to fetch ranks");

        const data = await res.json();
        setLeagueRank(data.league_rank ?? "-");
        setGlobalRank(data.global_rank ?? "-");
        setCurrentStreak(data.current_streak ?? 0);
      } catch {
        setLeagueRank("-");
        setGlobalRank("-");
        setCurrentStreak(0);
      }
    },
    [activeLeagueId]
  );

  useEffect(() => {
    if (
      season &&
      currentFinalizedWeek &&
      activeLeagueId &&
      user?.email &&
      user?.leagues?.length
    ) {
      fetchRanks(season, currentFinalizedWeek);
    }
  }, [user?.email, activeLeagueId, season, currentFinalizedWeek, fetchRanks]);

  const protectedRoutes = ["/select", "/standings", "/leagues"];
  useEffect(() => {
    if (!user && protectedRoutes.includes(location.pathname)) {
      navigate("/login");
    }
  }, [user, location.pathname]);

  const handleLeagueChange = (e) => {
    const newLeagueId = Number(e.target.value);
    setActiveLeagueId(newLeagueId);
  };

  // outside click handler
  useEffect(() => {
    const handler = (e) => {
      if (!e.target.closest(".avatar-menu-wrapper")) {
        setAvatarMenuOpen(false);
      }
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, []);

  const handleSeasonChange = (e) => {
    const newSeason = Number(e.target.value);
    setSelectedSeason(newSeason);
  };

  const navLinks = [
    { to: "/", label: "Home", icon: <Home className="inline w-4 h-4 mr-2" /> },
    { to: "/leagues", label: "View Leagues", icon: <Users className="inline w-4 h-4 mr-2" />, },
    ...(user
      ? [
        { to: "/select", label: "Pick Players", icon: <UserPlus className="inline w-4 h-4 mr-2" />, },
        { to: "/standings", label: "Standings", icon: <ListOrdered className="inline w-4 h-4 mr-2" />, },
      ]
      : []),
    { to: "/rules", label: "Scoring & Rules", icon: <Info className="inline w-4 h-4 mr-2" />, },
    { to: "/playerstats", label: "Player Stats", icon: <BarChart2 className="inline w-4 h-4 mr-2" />, },
    { to: "/streak-history", label: "Streak Hub", icon: <Zap className="inline w-4 h-4 mr-2" />, },

  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="p-4 bg-gray-800 shadow-md md:flex md:justify-between md:items-center relative flex-wrap">
        {/* Left side: mobile hamburger and user info + avatar */}
        <div className="flex justify-between items-start w-full md:w-auto md:flex-1">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-white focus:outline-none mt-1 md:hidden"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {user && (
            <div className="max-w-xs w-full">
              {/* Row: Hi, FirstName + Avatar */}
              <div className="flex justify-between items-center">
                <div className="font-semibold text-sm leading-tight">Hi, {firstName}</div>

                {/* ✅ FIXED WRAPPER */}
                <div className="relative avatar-menu-wrapper">
                  <div
                    className="w-10 h-10 flex-shrink-0 flex items-center justify-center bg-green-500 text-white rounded-full font-bold cursor-pointer hover:opacity-90"
                    onClick={() => setAvatarMenuOpen((prev) => !prev)}
                  >
                    {initials}
                  </div>

                  {avatarMenuOpen && (
                    <div className="absolute right-0 mt-2 w-44 bg-gray-800 text-white rounded-md shadow-lg border border-gray-700 z-50">
                      {isLeagueOwner && (
                        <button
                          onClick={() => {
                            setAvatarMenuOpen(false);
                            navigate("/admin/league-finances");
                          }}
                          className="block w-full text-left px-4 py-2 hover:bg-gray-700"
                        >
                          Admin: League Finances
                        </button>
                      )}

                      <button
                        onClick={() => {
                          setAvatarMenuOpen(false);
                          logout();
                          navigate("/");
                        }}
                        className="block w-full text-left px-4 py-2 hover:bg-gray-700"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Below row: Streaks, ranks, leagues */}
              <div className="text-yellow-400 text-xs flex flex-col gap-1 mt-2">
                <div className="flex flex-wrap gap-x-3">
                  <span>🔥 Triple Streak: {currentStreak}</span>
                  <span>🏆 Global Rank: {globalRank}</span>
                  <span>🏅 League Rank: {leagueRank}</span>
                </div>

                {user.leagues?.length > 0 && (
                  <div className="text-green-300 mt-1">
                    <div className="flex items-center gap-2">
                      <span>
                        League:{" "}
                        {user.leagues.find((l) => l.id === activeLeagueId)?.name ?? "Unknown"}
                      </span>
                      <Link
                        to={`/leagues/${activeLeagueId}`}
                        className="text-blue-400 hover:underline text-xs"
                      >
                        View →
                      </Link>
                    </div>

                    {user.leagues.length > 1 && (
                      <div className="mt-1">
                        <label htmlFor="league-switcher" className="text-xs text-gray-400 mr-2">
                          Change Active League:
                        </label>

                        <select
                          id="league-switcher"
                          className="border rounded px-3 py-1 w-32 bg-gray-700 text-white"
                          value={activeLeagueId ?? ""}
                          onChange={handleLeagueChange}
                        >
                          {user.leagues.map((league) => (
                            <option key={league.id} value={league.id}>
                              {league.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div
          className={`${isOpen ? "block" : "hidden"} md:flex md:items-center md:space-x-6 text-base font-medium mt-4 md:mt-0 w-full md:w-auto md:flex-1 md:justify-center`}
        >
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`block mt-2 md:mt-0 hover:text-yellow-400 flex items-center ${location.pathname === link.to ? "text-yellow-400" : ""
                }`}
            >
              {link.icon}
              {link.label}
            </Link>
          ))}
        </div>

        {!user && (
          <div className="mt-4 md:mt-0 flex flex-col md:flex-row md:items-center gap-2 md:gap-4 md:ml-auto w-full md:w-auto">
            <Link
              to="/login"
              className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-center"
            >
              Log In
            </Link>
            <Link
              to="/signup"
              className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 text-white text-center"
            >
              Sign Up
            </Link>
          </div>
        )}
      </nav>

      <main className="p-4">{children}</main>

      <footer className="text-center p-4 text-sm text-gray-500">
        Have suggestions or feedback?{" "}
        <a
          href="https://discord.gg/NBEmDUAMjZ"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Join our Discord
        </a>
      </footer>
    </div>
  );
};

export default Layout;
