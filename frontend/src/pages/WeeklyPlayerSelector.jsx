import React, { useState, useEffect } from "react";
import PlayerCard from "../components/PlayerCard";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";
import { useSeason } from "@/context/SeasonContext";
import { useLeague } from "../context/LeagueContext";

const POSITIONS = ["QB", "RB", "WR"];

const WeeklyPlayerSelector = () => {
  const { user } = useUser();
  const { activeLeagueId } = useLeague();
  const { season, currentWeek } = useSeason();
  const [selectedWeek, setSelectedWeek] = useState(null);

  const [teamsMap, setTeamsMap] = useState({});
  const [playersByPosition, setPlayersByPosition] = useState({ QB: [], RB: [], WR: [] });
  const [searchTerms, setSearchTerms] = useState({ QB: "", RB: "", WR: "" });
  const [selectedPlayers, setSelectedPlayers] = useState({ QB: null, RB: null, WR: null });
  const [filteredPlayersMap, setFilteredPlayersMap] = useState({ QB: [], RB: [], WR: [] });
  const [playersLoaded, setPlayersLoaded] = useState(false);
  const [restrictedPlayers, setRestrictedPlayers] = useState({ QB: [], RB: [], WR: [] });
  const [lockedPlayers, setLockedPlayers] = useState({ QB: [], RB: [], WR: [] });

  // --- Helper to safely set selected player respecting locked players ---
  const safeSetSelectedPlayer = (pos, player) => {
    if (player && lockedPlayers[pos]?.includes(String(player.player_id))) {
      console.log(`Cannot change ${pos}, player is locked:`, player.player_name);
      return;
    }
    setSelectedPlayers((prev) => ({ ...prev, [pos]: player }));
  };

  const findPlayer = (pos, playerId) =>
    playersByPosition[pos]?.find((p) => String(p.player_id) === String(playerId)) || null;


  // --- Fetch current week ---
  useEffect(() => {
    if (currentWeek != null) {
      setSelectedWeek(currentWeek);
    }
  }, [currentWeek]);

  // --- Fetch teams ---
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const res = await apiFetch("/api/teams");
        const teamsData = await res.json();
        const map = {};
        teamsData.forEach((team) => {
          map[team.id] = team.name;
        });
        setTeamsMap(map);
      } catch (err) {
        console.error("Failed to fetch teams:", err);
      }
    };
    fetchTeams();
  }, []);

  // --- Fetch players ---
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const adjustedSeason = currentWeek === 1 ? season - 1 : season;

        const results = await Promise.all(
          POSITIONS.map((pos) =>
            apiFetch(`/api/top_players/${pos}?season=${adjustedSeason}`).then((res) => res.json())
          )
        );

        const updated = {};
        results.forEach((data, i) => {
          const pos = POSITIONS[i];
          const fullPlayers = data.map((p) => ({
            ...p,
            player_id: String(p.player_id), // normalize
            team: {
              name: teamsMap[p.team_id] || "Unknown",
              team_id: String(p.team_id), // normalize
            },
          }));

          const unique = Array.from(
            new Map(fullPlayers.map((p) => [`${p.player_id}_${p.team_id}`, p])).values()
          );
          updated[pos] = unique;
        });

        setPlayersByPosition(updated);
        setFilteredPlayersMap(updated);
        setPlayersLoaded(true);
      } catch (err) {
        console.error("Error loading players:", err);
      }
    };
    if (teamsMap && Object.keys(teamsMap).length > 0) fetchPlayers();
  }, [season, currentWeek, teamsMap]);

  // --- Fetch restricted players ---
  useEffect(() => {
    if (!user?.email || !activeLeagueId || currentWeek === null || season === null) return;

    const url = `/api/restricted_players/${user.email}?week=${currentWeek}&league_id=${activeLeagueId}&season=${season}`;
    apiFetch(url)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data) => {
        setRestrictedPlayers({
          QB: (data.qb || []).map(String),
          RB: (data.rb || []).map(String),
          WR: (data.wr || []).map(String),
        });
      })
      .catch(() => setRestrictedPlayers({ QB: [], RB: [], WR: [] }));
  }, [user?.email, currentWeek, season, activeLeagueId]);

  // --- Fetch locked players ---
  useEffect(() => {
    if (!user?.email || !activeLeagueId || !selectedWeek || !season) return;

    const url = `/api/locked_players?week=${selectedWeek}&season=${season}&league_id=${activeLeagueId}`;
    console.log("[LOCKED_FETCH] Fetching locked players from:", url);

    apiFetch(url)
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`[LOCKED_FETCH] HTTP ${res.status} - ${text}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("[LOCKED_FETCH] Locked players received:", data);
        setLockedPlayers({
          QB: Array.isArray(data.QB) ? data.QB.map(String) : [],
          RB: Array.isArray(data.RB) ? data.RB.map(String) : [],
          WR: Array.isArray(data.WR) ? data.WR.map(String) : [],
        });
      })
      .catch((err) => {
        console.error("[LOCKED_FETCH] Failed to fetch locked players:", err);
        setLockedPlayers({ QB: [], RB: [], WR: [] });
      });
  }, [user?.email, selectedWeek, season, activeLeagueId]);

  // --- Load user's picks for the selected week ---
  useEffect(() => {
    if (!playersLoaded || !user?.email || !activeLeagueId) return;

    apiFetch(`/api/picks/email/${encodeURIComponent(user.email)}/week/${selectedWeek}/league/${activeLeagueId}/season/${season}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.length > 0) {
          const userPick = data[0];
          setSelectedPlayers({
            QB: findPlayer("QB", userPick.qb),
            RB: findPlayer("RB", userPick.rb),
            WR: findPlayer("WR", userPick.wr),
          });
        } else {
          setSelectedPlayers({ QB: null, RB: null, WR: null });
        }
      })
      .catch(() => setSelectedPlayers({ QB: null, RB: null, WR: null }));
  }, [playersLoaded, selectedWeek, user?.email, activeLeagueId, season, lockedPlayers]);

  // --- Search filter ---
  useEffect(() => {
    const updatedMap = {};
    POSITIONS.forEach((pos) => {
      const term = searchTerms[pos]?.toLowerCase().trim();
      const all = playersByPosition[pos] || [];
      updatedMap[pos] = !term ? all : all.filter((p) => p.player_name.toLowerCase().includes(term));
    });
    setFilteredPlayersMap(updatedMap);
  }, [searchTerms, playersByPosition]);

  const handleSearchChange = (pos, value) => setSearchTerms((prev) => ({ ...prev, [pos]: value }));

  const handleSelect = (pos, compoundId) => {
    if (!compoundId) {
      safeSetSelectedPlayer(pos, null);
      return;
    }
    const [playerId, teamId] = compoundId.split("_");
    const player = playersByPosition[pos].find(
      (p) => String(p.player_id) === playerId && String(p.team.team_id) === teamId
    );
    safeSetSelectedPlayer(pos, player);
  };


  const handleSubmit = async () => {
    if (!user?.email || !activeLeagueId || !selectedPlayers.QB || !selectedPlayers.RB || !selectedPlayers.WR) {
      alert("Please select all positions and a league before submitting.");
      return;
    }

    const payload = {
      week: selectedWeek,
      user_email: user.email,
      qb: selectedPlayers.QB.player_id, // already string
      rb: selectedPlayers.RB.player_id,
      wr: selectedPlayers.WR.player_id,
      timestamp: new Date().toISOString(),
      league_id: activeLeagueId,
      season,
    };

    try {
      const response = await apiFetch("/api/picks/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(await response.text());
      alert(`Week ${selectedWeek} picks submitted! Good luck hitting a streak.`);
    } catch (err) {
      console.error("Submission error:", err);
      alert("Something went wrong while submitting your picks. Please try again.");
    }
  };

  // --- Reset selections on week change ---
  useEffect(() => {
    setSelectedPlayers({ QB: null, RB: null, WR: null });
  }, [selectedWeek]);

  const isDropdownLocked = (pos) => {
    const selected = selectedPlayers[pos];
    if (!selected) return false;
    return lockedPlayers[pos]?.includes(String(selected.player_id));
  };

  if (!user?.email) return <div>Loading user info...</div>;
  if (!activeLeagueId) return <div>Please select a league to pick players.</div>;
  if (!season || !currentWeek) return <div className="text-center mt-10 text-lg">Loading current season and week...</div>;


  return (
    <div className="p-4 sm:p-6 max-w-screen-lg mx-auto overflow-x-hidden">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-center">TripleStreak – Week {selectedWeek}</h1>

      <div className="mb-4 flex justify-center">
        <span className="text-lg font-semibold">Current Season: {season ?? "Loading..."}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-10">
        {POSITIONS.map((pos) => (
          <div key={pos}>
            <h2 className="text-lg sm:text-xl font-semibold mb-2">{pos}</h2>
            <input
              type="text"
              className="w-full p-3 border rounded mb-2 text-base"
              placeholder={`Search ${pos}...`}
              value={searchTerms[pos]}
              onChange={(e) => handleSearchChange(pos, e.target.value)}
            />
            {searchTerms[pos] && filteredPlayersMap[pos].length === 0 && (
              <p className="text-sm text-red-500 mb-2">No players found for “{searchTerms[pos]}”</p>
            )}
            <select
              className="w-full p-3 border rounded mb-2 text-base"
              value={
                selectedPlayers[pos]?.player_id && selectedPlayers[pos]?.team.team_id
                  ? `${selectedPlayers[pos].player_id}_${selectedPlayers[pos].team.team_id}`
                  : ""
              }
              onChange={(e) => handleSelect(pos, e.target.value)}
              disabled={isDropdownLocked(pos)} // <-- lock entire dropdown if user's pick is locked

            >
              <option value="">Select a {pos}</option>
              {filteredPlayersMap[pos].map((p) => {
                const isRestricted = restrictedPlayers[pos]?.includes(String(p.player_id));
                const isLocked = lockedPlayers[pos]?.includes(String(p.player_id));


                if (isRestricted || isLocked) {
                  console.log(`[LOCKED_UI] ${pos} locked: ${p.player_name} (${p.player_id})`);
                }

                return (
                  <option
                    key={`${p.player_id}_${p.team.team_id}`}
                    value={`${p.player_id}_${p.team.team_id}`}
                    disabled={isRestricted || isLocked}
                    className={isRestricted || isLocked ? "text-gray-400 bg-gray-100" : ""}
                  >
                    {p.player_name} {isRestricted || isLocked ? "🔒" : ""}
                  </option>
                );
              })}
            </select>

            {selectedPlayers[pos] && <div className="mt-2"><PlayerCard player={selectedPlayers[pos]} /></div>}
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-4 mb-8">
        <label className="text-base font-medium">Week:</label>
        <select
          className="p-3 border rounded text-base"
          value={selectedWeek}
          onChange={(e) => setSelectedWeek(Number(e.target.value))}
        >
          {Array.from({ length: 18 }, (_, i) => (
            <option key={i + 1} value={i + 1}>{i + 1}</option>
          ))}
        </select>
        <button
          className="w-full sm:w-auto bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700 text-lg"
          onClick={handleSubmit}
        >
          Submit Picks
        </button>
      </div>
    </div>
  );
};

export default WeeklyPlayerSelector;
