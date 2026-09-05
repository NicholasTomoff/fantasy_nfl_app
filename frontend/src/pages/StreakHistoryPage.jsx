import React, { useEffect, useState, useMemo } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
    Legend
} from "recharts";
import { apiFetch } from "@/services/api";
import "../styles/streakHistory.css";

export default function StreakHistoryPage() {
    const [viewMode, setViewMode] = useState("league");
    const [leagueId, setLeagueId] = useState(1);
    const [history, setHistory] = useState([]);
    const [leagues, setLeagues] = useState([]);

    useEffect(() => {
        apiFetch("/api/leagues/all")
            .then(res => (res.ok ? res.json() : []))
            .then(data => setLeagues(Array.isArray(data) ? data : []))
            .catch(err => console.error("Failed to load leagues:", err));
    }, []);

    useEffect(() => {
        const endpoint =
            viewMode === "league"
                ? `/api/streak-history/league/${leagueId}`
                : `/api/streak-history/global`;

        // apiFetch prepends VITE_API_BASE_URL. A bare fetch() would hit the static
        // host, whose SPA rewrite returns index.html with a 200 -- res.json() then
        // throws on the HTML and the page silently renders nothing.
        apiFetch(endpoint)
            .then(res => {
                if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
                return res.json();
            })
            .then(data => setHistory(Array.isArray(data) ? data : []))
            .catch(err => {
                console.error("Failed to load streak history:", err);
                setHistory([]);
            });
    }, [leagueId, viewMode]);

    // 🔥 Compute Top Records Dynamically
    const records = useMemo(() => {
        if (!history.length) return null;

        const maxBy = (key) =>
            history.reduce((a, b) => (a[key] > b[key] ? a : b));

        const minBy = (key) =>
            history.reduce((a, b) =>
                a[key] && b[key]
                    ? a[key] < b[key]
                        ? a
                        : b
                    : a
            );

        return {
            longestTriple: maxBy("longest_triple_streak"),
            qb: maxBy("longest_qb_streak"),
            rb: maxBy("longest_rb_streak"),
            wr: maxBy("longest_wr_streak"),
            mostTriples: maxBy("most_triples_in_season"),
            earliestClinch: minBy("clinched_week")
        };
    }, [history]);

    return (
        <div className="page-container">
            <h1 className="page-title">Streak Hub</h1>

            {/* VIEW TOGGLE */}
            <div className="view-toggle">
                <button
                    className={viewMode === "league" ? "active" : ""}
                    onClick={() => setViewMode("league")}
                >
                    League View
                </button>
                <button
                    className={viewMode === "global" ? "active" : ""}
                    onClick={() => setViewMode("global")}
                >
                    Global View
                </button>
            </div>

            {viewMode === "league" && (
                <div className="league-select">
                    <select
                        value={leagueId}
                        onChange={(e) => setLeagueId(Number(e.target.value))}
                    >
                        {leagues.length === 0 && <option value={leagueId}>Loading…</option>}
                        {leagues.map(l => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                    </select>
                </div>
            )}

            {/* 🔥 RECORD HIGHLIGHT ROW */}
            {records && (
                <div className="record-grid">
                    <RecordCard
                        title="Longest Triple Streak"
                        value={records.longestTriple.longest_triple_streak}
                        season={records.longestTriple.season}
                        holder={records.longestTriple.longest_triple_name}
                    />
                    <RecordCard
                        title="Longest QB Streak"
                        value={records.qb.longest_qb_streak}
                        season={records.qb.season}
                        holder={records.qb.longest_qb_name}
                    />
                    <RecordCard
                        title="Longest RB Streak"
                        value={records.rb.longest_rb_streak}
                        season={records.rb.season}
                        holder={records.rb.longest_rb_name}
                    />
                    <RecordCard
                        title="Longest WR Streak"
                        value={records.wr.longest_wr_streak}
                        season={records.wr.season}
                        holder={records.wr.longest_wr_name}
                    />
                    <RecordCard
                        title="Most Triple Streaks"
                        value={records.mostTriples.most_triples_in_season}
                        season={records.mostTriples.season}
                        holder={records.mostTriples.most_triples_name}
                    />
                    <RecordCard
                        title="Earliest Clinch"
                        value={
                            records.earliestClinch?.clinched_week
                                ? `Week ${records.earliestClinch.clinched_week}`
                                : records.earliestClinch?.clinched_note ?? "—"
                        }
                        season={records.earliestClinch?.season}
                    />
                </div>
            )}

            {/* TREND CHART */}
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={history}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="season" />
                        <YAxis />
                        <Tooltip content={<HistoryTooltip />} />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="longest_triple_streak"
                            stroke="#4f46e5"
                            strokeWidth={3}
                        />
                        <Line
                            type="monotone"
                            dataKey="best_triple_start"
                            stroke="#22c55e"
                            strokeWidth={2}
                        />
                        <Line
                            type="monotone"
                            dataKey="most_triples_in_season"
                            stroke="#f97316"
                            strokeWidth={2}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* SEASON CARDS */}
            <div className="stat-card-grid">
                {history.map(season => (
                    <div key={season.season} className="season-card">
                        <h3>{season.season}</h3>
                        <p><strong>Champion:</strong> {season.champion_name}</p>
                        <p><strong>Runner-Up:</strong> {season.runner_up_name}</p>
                        <p><strong>Third:</strong> {season.third_place_name}</p>
                        <p><strong>Members:</strong> {season.member_count}</p>
                        <p>
                            <strong>Best Start:</strong> {season.best_triple_start}
                            {season.best_triple_start_name && ` (${season.best_triple_start_name})`}
                        </p>
                        <p>
                            <strong>Longest Triple:</strong> {season.longest_triple_streak}
                            {season.longest_triple_name && ` (${season.longest_triple_name})`}
                        </p>
                        <p>
                            <strong>QB / RB / WR:</strong>{" "}
                            {season.longest_qb_streak}{season.longest_qb_name && ` (${season.longest_qb_name})`} /{" "}
                            {season.longest_rb_streak}{season.longest_rb_name && ` (${season.longest_rb_name})`} /{" "}
                            {season.longest_wr_streak}{season.longest_wr_name && ` (${season.longest_wr_name})`}
                        </p>
                        <p>
                            <strong>Most Triples:</strong> {season.most_triples_in_season}
                            {season.most_triples_name && ` (${season.most_triples_name})`}
                        </p>
                        <p>
                            <strong>Clinched:</strong>{" "}
                            {season.clinched_week
                                ? `Week ${season.clinched_week}`
                                : season.clinched_note ?? "—"}
                        </p>
                        {season.winner_score != null && (
                            <p><strong>Winning Score:</strong> {season.winner_score}</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

// Recharts hands the tooltip the whole row, so the holder names travel with
// the plotted values and can be shown alongside them.
function HistoryTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;
    const HOLDER = {
        longest_triple_streak: row.longest_triple_name,
        best_triple_start: row.best_triple_start_name,
        most_triples_in_season: row.most_triples_name,
    };
    return (
        <div className="chart-tooltip">
            <div className="chart-tooltip-season">{label}</div>
            {row.champion_name && (
                <div className="chart-tooltip-champ">🏆 {row.champion_name}</div>
            )}
            {payload.map(p => (
                <div key={p.dataKey} style={{ color: p.stroke }}>
                    {p.name}: <strong>{p.value}</strong>
                    {HOLDER[p.dataKey] ? ` — ${HOLDER[p.dataKey]}` : ""}
                </div>
            ))}
        </div>
    );
}

function RecordCard({ title, value, season, holder }) {
    return (
        <div className="record-card">
            <h4>{title}</h4>
            <div className="record-value">{value}</div>
            {holder && <div className="record-holder">{holder}</div>}
            <div className="record-season">Season {season}</div>
        </div>
    );
}
