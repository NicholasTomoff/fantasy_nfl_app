import React, { useEffect, useState } from "react";
import { FaCheck, FaTimes } from "react-icons/fa";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";
import { useSeason } from "@/context/SeasonContext";
import { useLeague } from "@/context/LeagueContext";

// force rebuild for tie logic display
const renderStreakIcons = (count) => {
  if (count === 0) {
    return (
      <span className="text-red-400 font-bold inline-flex flex-nowrap items-center justify-center gap-0.5 whitespace-nowrap">
        <FaTimes /> 0
      </span>
    );
  }
  return (
    <span className="text-green-600 font-bold inline-flex flex-nowrap items-center justify-center gap-0.5 whitespace-nowrap">
      {Array.from({ length: count }, (_, i) => (
        <FaCheck key={i} />
      ))}
      {count}
    </span>
  );
};

const renderTripleStreakIcons = (points) => {
  const count = Math.floor(points / 5);
  if (count === 0) {
    return (
      <span className="text-red-400 font-bold inline-flex flex-nowrap items-center justify-center gap-0.5 whitespace-nowrap">
        <FaTimes /> 0
      </span>
    );
  }
  return (
    <span className="text-green-600 font-bold inline-flex flex-nowrap items-center justify-center gap-0.5 whitespace-nowrap">
      {Array.from({ length: count }, (_, i) => (
        <FaCheck key={i} />
      ))}
      {count}
    </span>
  );
};

// Rank 1-3 use the same medal colours as the Streak Hub podium, so "who is
// winning" reads identically across the app.
const RANK_STYLES = {
  1: { row: "bg-yellow-400/[0.18]", accent: "border-l-4 border-l-yellow-400",
       badge: "bg-yellow-400 text-yellow-950 ring-2 ring-yellow-200/50", sticky: "bg-[#464631]" },
  2: { row: "bg-slate-300/[0.15]", accent: "border-l-4 border-l-slate-300",
       badge: "bg-slate-300 text-slate-900 ring-2 ring-slate-100/50", sticky: "bg-[#394351]" },
  3: { row: "bg-orange-400/[0.15]", accent: "border-l-4 border-l-orange-400",
       badge: "bg-orange-400 text-orange-950 ring-2 ring-orange-200/50", sticky: "bg-[#403938]" },
};

// Everyone else gets a quiet chip so the column still reads as a column.
const DEFAULT_BADGE = "bg-gray-700 text-gray-200";

const Standings = () => {
  const { user } = useUser();
  const [standings, setStandings] = useState([]);
  const [allSeasons, setAllSeasons] = useState([]);
  const { season, setSeason, currentWeek, setCurrentWeek } = useSeason();
  const { activeLeagueId, selectedSeason } = useLeague();
  const [leagueName, setLeagueName] = useState("");
  const [currentFinalizedWeek, setCurrentFinalizedWeek] = useState(null);


  // Fetch all seasons once
  useEffect(() => {
    const fetchSeasons = async () => {
      try {
        const res = await apiFetch("/api/seasons/all");
        const data = await res.json();
        setAllSeasons(data);

        const current = data.find((s) => s.is_current);
        const initialSeason = current?.year || data[0]?.year;
        if (!season) {
          setSeason(initialSeason);
        }
      } catch (err) {
        console.error("Failed to fetch seasons", err);
      }
    };
    fetchSeasons();
  }, [season, setSeason]);

  // Fetch league name
  useEffect(() => {
    if (!activeLeagueId) return;

    const fetchLeagueName = async () => {
      try {
        const res = await apiFetch(`/api/leagues/${activeLeagueId}`);
        const data = await res.json();
        setLeagueName(data.name);
      } catch (err) {
        console.error("Failed to fetch league name:", err);
      }
    };
    fetchLeagueName();
  }, [activeLeagueId]);

  // Fetch current week
  useEffect(() => {
    if (!season) return;

    const fetchCurrentWeek = async () => {
      try {
        const res = await apiFetch(`/api/weeks/current?season=${season}`);
        const data = await res.json();
        setCurrentWeek(data.week);
      } catch (err) {
        console.error("Failed to fetch current week", err);
      }
    };
    fetchCurrentWeek();
  }, [season]);

  // Fetch current finalized week
  useEffect(() => {
    if (!season) return;

    const fetchCurrentFinalizedWeek = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await apiFetch(
          `/api/weeks/finalized?season=${season}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          }
        );
        const data = await res.json();
        setCurrentFinalizedWeek(data.week);
      } catch (err) {
        console.error("Failed to fetch current finalized week", err);
      }
    };
    fetchCurrentFinalizedWeek();
  }, [season]);

  const [maxPointsByUser, setMaxPointsByUser] = useState({});

  // Fetch max points possible
  useEffect(() => {
    if (!activeLeagueId || !season || currentFinalizedWeek === null) return;

    const token = localStorage.getItem("token");

    const fetchProjectedPoints = async () => {
      try {
        const res = await apiFetch(
          `/league/${activeLeagueId}/projected-max-points?season=${season}&currentFinalizedWeek=${currentFinalizedWeek}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          }
        );

        if (!res.ok) throw new Error(`HTTP error: ${res.status}`);

        const data = await res.json();

        // data.members is the array we want
        if (data.members && Array.isArray(data.members)) {
          const userMap = {};
          data.members.forEach((member) => {
            userMap[member.user_email] = member.projected_final_total;
          });
          setMaxPointsByUser(userMap);
        } else {
          console.warn("No members array found in projected points data");
        }
      } catch (err) {
        console.error("Failed to fetch projected max points:", err);
      }
    };

    fetchProjectedPoints();
  }, [activeLeagueId, season, currentFinalizedWeek]);



  // Fetch standings
  useEffect(() => {
    if (!activeLeagueId || !season || !currentWeek || currentFinalizedWeek === null) return;

    const token = localStorage.getItem("token");

    // Determine which week to use for picks display:
    // If currentWeek is 1 (season start), finalizedWeek should be 0 (no finalized picks yet)
    // If currentWeek > 1 and the first game of the current week hasn't started yet, show finalized week picks
    // Otherwise show currentWeek picks

    // For simplicity here we use currentWeek to fetch standings
    // But picks will switch in the backend or here before rendering

    apiFetch(
      `/api/standings?week=${currentFinalizedWeek}&league_id=${activeLeagueId}&season=${season}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        // Adjust picks based on game start times here if needed
        setStandings(data);
      })
      .catch((err) => console.error("Failed to load standings:", err));
  }, [activeLeagueId, season, currentWeek, currentFinalizedWeek]);

  if (!activeLeagueId) {
    return (
      <p className="text-center p-6">
        Please select a league to view standings.
      </p>
    );
  }

  // Compute ranks before rendering
  // Same person, whether the row came back keyed by email or name.
  const isMe = (entry) =>
    !!user?.email && entry.user_email?.toLowerCase() === user.email.toLowerCase();

  const standingsWithRanks = (() => {
    let lastPoints = null;
    let lastRank = 0;
    let skip = 1;

    return standings
      .sort((a, b) => b.total_points - a.total_points)
      .map((entry) => {
        const pts = entry.total_points ?? 0;
        let rank;
        if (pts === lastPoints) {
          rank = lastRank; // tie, same rank as previous
        } else {
          rank = skip;
          lastRank = rank;
        }
        lastPoints = pts;
        skip += 1;
        return { ...entry, rank };
      });
  })();


  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
        <h2 className="text-2xl sm:text-3xl font-bold text-center sm:text-left">
          Standings{leagueName ? `: ${leagueName}` : ""}
        </h2>

        <div className="flex items-center gap-2">
          <label htmlFor="season" className="text-sm font-medium text-gray-300">
            Season:
          </label>
          <select
            value={season ?? ""}
            onChange={(e) => setSeason(parseInt(e.target.value))}
            className="bg-gray-700 text-white px-3 py-1 rounded border"
          >
            {allSeasons.map((s) => (
              <option key={s.year} value={s.year}>
                {s.year} Season
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex justify-between items-center text-gray-400 mb-4 px-2">
        <p className="text-sm">
          Finalized Through: <span className="font-medium">Week {currentFinalizedWeek !== null ? currentFinalizedWeek : "..."}</span>
        </p>
        <p className="text-sm">
          Current Week: <span className="font-medium">Week {currentWeek !== null ? currentWeek : "..."}</span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[900px] sm:min-w-full border-collapse text-xs sm:text-sm table-auto rounded-lg overflow-hidden">
          <thead className="bg-blue-700 text-white select-none border-b-2 border-blue-400">
            <tr>
              <th className="px-3 py-2.5 whitespace-nowrap">Rank</th>
              <th className="px-3 py-2.5 sticky left-0 bg-blue-700 z-10 w-40 text-left">
                Player Name
              </th>
              <th className="px-3 py-2.5 text-center text-yellow-300 text-base font-extrabold">
                Total Points
              </th>
              <th className="px-3 py-2.5 text-center">Triple Streak</th>
              <th className="px-3 py-2.5 text-center">Weekly Points</th>
              <th className="px-3 py-2.5 text-center">QB Streak</th>
              <th className="px-3 py-2.5 text-center">RB Streak</th>
              <th className="px-3 py-2.5 text-center">WR Streak</th>
              <th className="px-3 py-2.5" colSpan={3}>Finalized Picks for Standings</th>
              <th className="px-3 py-2.5 text-center text-green-400 font-bold">
                Max Total Points Possible
              </th>
            </tr>
            <tr className="bg-blue-700 text-blue-200 text-[11px] uppercase tracking-wide">
              <th colSpan={8}></th>
              <th className="px-3 py-2.5 w-32 text-left">QB</th>
              <th className="px-3 py-2.5 w-32 text-left">RB</th>
              <th className="px-3 py-2.5 w-32 text-left">WR</th>
              <th colSpan={1}></th>
            </tr>
          </thead>
          <tbody>
            {standingsWithRanks.map((entry, index) => (
              <tr
                key={index}
                className={[
                  "text-center group transition-colors border-b border-white/10",
                  "hover:bg-slate-700/70",
                  RANK_STYLES[entry.rank]?.row ?? (index % 2 ? "bg-white/[0.05]" : ""),
                  isMe(entry) ? "ring-2 ring-inset ring-blue-400 bg-blue-500/20" : "",
                ].join(" ")}
              >
                <td className={`px-3 py-2.5 ${RANK_STYLES[entry.rank]?.accent ?? "border-l-4 border-l-transparent"}`}>
                  <span
                    className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-extrabold ${
                      RANK_STYLES[entry.rank]?.badge ?? DEFAULT_BADGE
                    }`}
                  >
                    {entry.rank}
                  </span>
                </td>
                <td className={`px-3 py-2.5 font-semibold text-left text-white sticky left-0 z-[5] ${isMe(entry) ? "bg-blue-900" : RANK_STYLES[entry.rank]?.sticky ?? "bg-gray-800"}`}>
                  {entry.user_name}
                </td>
                <td className="px-3 py-2.5 text-center text-yellow-300 text-lg font-extrabold">
                  {entry.total_points}
                </td>
                <td className="px-3 py-2.5">
                  {renderTripleStreakIcons(entry.triple_streak)}
                </td>
                <td className="px-3 py-2.5 text-center">
                  {entry.weekly_points}
                </td>
                <td className="px-3 py-2.5">
                  {renderStreakIcons(entry.streaks.QB)}
                </td>
                <td className="px-3 py-2.5">
                  {renderStreakIcons(entry.streaks.RB)}
                </td>
                <td className="px-3 py-2.5">
                  {renderStreakIcons(entry.streaks.WR)}
                </td>
                <td className="px-3 py-2.5 text-left">
                  {entry.picks.QB}
                </td>
                <td className="px-3 py-2.5 text-left">
                  {entry.picks.RB}
                </td>
                <td className="px-3 py-2.5 text-left">
                  {entry.picks.WR}
                </td>
                <td className="px-3 py-2.5 text-center text-green-400 font-bold">
                  {maxPointsByUser[entry.user_email] ?? "-"}
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Standings;
