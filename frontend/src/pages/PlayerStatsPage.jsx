import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { apiFetch } from "@/services/api";
import { useSeason } from "@/context/SeasonContext";

const PlayerStatsPage = () => {
  const [position, setPosition] = useState("QB");
  const [players, setPlayers] = useState([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState(null);
  const [playerStats, setPlayerStats] = useState([]);
  const [seasonFilter, setSeasonFilter] = useState([]);
  const [allSeasons, setAllSeasons] = useState([]);
  const { season } = useSeason();



  const [visibleLines, setVisibleLines] = useState({
    passing_yards: true,
    rushing_yards: true,
    receiving_yards: true,
    passing_tds: true,
    rushing_tds: true,
    receiving_tds: true,
  });

  const chartColors = {
    passing_yards: "#8884d8",
    rushing_yards: "#82ca9d",
    receiving_yards: "#ffc658",
    passing_tds: "#ff7300",
    rushing_tds: "#0088fe",
    receiving_tds: "#ff0000",
  };

  const handleLegendClick = (e) => {
    const key = e.dataKey;
    setVisibleLines((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Fetch all seasons once on mount and set filter
  useEffect(() => {
    const fetchSeasons = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await apiFetch("/api/seasons/all", {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        const data = await res.json();
        const years = data.map((s) => s.year).sort((a, b) => b - a);
        setAllSeasons(years);
        setSeasonFilter([season]); // Initialize filter to current season
      } catch (err) {
        console.error("Error fetching all seasons:", err);
      }
    };
    fetchSeasons();
  }, []);

  // Fetch players whenever position changes
  useEffect(() => {
    if (seasonFilter.length === 0) return;

    async function fetchPlayers() {
      try {
        const params = new URLSearchParams();
        seasonFilter.forEach((s) => params.append("seasons", s));

        const res = await apiFetch(
          `/api/players/${position}/with-stats?${params.toString()}`
        );
        const playersWithStats = await res.json();

        setPlayers(playersWithStats);
        setSelectedPlayerId(
          playersWithStats.length > 0 ? playersWithStats[0].player_id : null
        );

        if (playersWithStats.length === 0) {
          setPlayerStats([]);
        }
      } catch (error) {
        console.error("Failed to fetch players", error);
        setPlayers([]);
      }
    }

    fetchPlayers();
  }, [position, seasonFilter]);


  // Fetch stats when selected player changes
  useEffect(() => {
    if (!selectedPlayerId) return;
    async function fetchPlayerStats() {
      try {
        const res = await apiFetch(`/api/players/${Number(selectedPlayerId)}/stats`);
        const statsData = await res.json();
        setPlayerStats(statsData);
      } catch (error) {
        console.error("Failed to fetch player stats", error);
        setPlayerStats([]);
      }
    }
    fetchPlayerStats();
  }, [selectedPlayerId]);




  // Filter stats by selected seasons for chart
  const filteredStats = playerStats.filter((stat) =>
    seasonFilter.includes(stat.game?.season)
  );

  const parseWeek = (weekStr) => {
    if (typeof weekStr === "string") {
      const match = weekStr.match(/\d+/);
      return match ? Number(match[0]) : 0;
    }
    if (typeof weekStr === "number") return weekStr;
    return 0;
  };

  const dataByWeek = filteredStats.map((stat) => ({
    week: parseWeek(stat.week ?? (stat.game?.week ?? 0)),
    season: stat.season,
    passing_yards: stat.passing_yards || 0,
    rushing_yards: stat.rushing_yards || 0,
    receiving_yards: stat.receiving_yards || 0,
    passing_tds: stat.passing_tds || 0,
    rushing_tds: stat.rushing_tds || 0,
    receiving_tds: stat.receiving_tds || 0,
    receptions: stat.receptions || 0,
  }));

  dataByWeek.sort((a, b) => {
    if (a.season !== b.season) return a.season - b.season;
    return a.week - b.week;
  });

  return (
    <div className="p-4 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Player Stats</h1>

      <div className="mb-4">
        <label className="mr-2 font-semibold">Position:</label>
        <select
          value={position}
          onChange={(e) => setPosition(e.target.value)}
          className="border rounded p-1"
        >
          <option value="QB">QB</option>
          <option value="RB">RB</option>
          <option value="WR">WR</option>
        </select>
      </div>

      <div className="mb-4">
        <label className="mr-2 font-semibold">Player:</label>
        <select
          value={selectedPlayerId || ""}
          onChange={(e) => setSelectedPlayerId(Number(e.target.value))}
          className="border rounded p-1"
        >
          {players.map((player) => {
            const yards = player.total_yards; // 👈 comes directly from backend

            return (
              <option
                key={`${player.player_id}-${player.team?.name || "NoTeam"}`}
                value={player.player_id}
              >
                {player.player_name} ({player.team?.name || "No Team"})
                {yards !== undefined
                  ? ` - (Pass + Rush + Rec): ${yards} yards`
                  : ""}
              </option>
            );
          })}
        </select>
      </div>


      <div className="mb-4">
        <label className="mr-2 font-semibold">Seasons:</label>
        {allSeasons.map((season) => (
          <label
            key={season}
            className="mr-3 inline-flex items-center space-x-1 cursor-pointer select-none"
          >
            <input
              type="checkbox"
              checked={seasonFilter.includes(season)}
              onChange={() => {
                if (seasonFilter.includes(season)) {
                  setSeasonFilter(seasonFilter.filter((s) => s !== season));
                } else {
                  setSeasonFilter([...seasonFilter, season]);
                }
              }}
              className="form-checkbox h-5 w-5 text-blue-600"
            />
            <span>{season}</span>
          </label>
        ))}
      </div>

      <div>
        <h2 className="text-2xl font-semibold mb-2">Weekly Stats</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={dataByWeek}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Legend
              onClick={handleLegendClick}
              payload={Object.entries(visibleLines).map(([key, visible]) => ({
                value: key.replace("_", " ").toUpperCase(),
                type: "line",
                id: key,
                color: chartColors[key],
                dataKey: key,
                inactive: !visible,
              }))}
            />
            {Object.entries(chartColors).map(([key, color]) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                name={key.replace("_", " ").toUpperCase()}
                strokeWidth={2}
                dot={{ r: 3 }}
                hide={!visibleLines[key]}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PlayerStatsPage;
