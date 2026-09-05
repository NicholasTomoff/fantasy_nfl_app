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
import "../styles/streakHistory.css";

export default function StreakHistoryPage() {
    const [viewMode, setViewMode] = useState("league");
    const [leagueId, setLeagueId] = useState(1);
    const [history, setHistory] = useState([]);

    useEffect(() => {
        const endpoint =
            viewMode === "league"
                ? `/api/streak-history/league/${leagueId}`
                : `/api/streak-history/global`;

        fetch(endpoint)
            .then(res => res.json())
            .then(data => setHistory(data));
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
                        onChange={(e) => setLeagueId(e.target.value)}
                    >
                        <option value={1}>League 1</option>
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
                    />
                    <RecordCard
                        title="Longest QB Streak"
                        value={records.qb.longest_qb_streak}
                        season={records.qb.season}
                    />
                    <RecordCard
                        title="Longest RB Streak"
                        value={records.rb.longest_rb_streak}
                        season={records.rb.season}
                    />
                    <RecordCard
                        title="Longest WR Streak"
                        value={records.wr.longest_wr_streak}
                        season={records.wr.season}
                    />
                    <RecordCard
                        title="Most Triple Streaks"
                        value={records.mostTriples.most_triples_in_season}
                        season={records.mostTriples.season}
                    />
                    <RecordCard
                        title="Earliest Clinch"
                        value={`Week ${records.earliestClinch?.clinched_week ?? "-"}`}
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
                        <Tooltip />
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
                        <p><strong>Best Start:</strong> {season.best_triple_start}</p>
                        <p><strong>Longest Triple:</strong> {season.longest_triple_streak}</p>
                        <p>
                            <strong>QB / RB / WR:</strong>{" "}
                            {season.longest_qb_streak} /{" "}
                            {season.longest_rb_streak} /{" "}
                            {season.longest_wr_streak}
                        </p>
                        <p><strong>Most Triples:</strong> {season.most_triples_in_season}</p>
                        <p><strong>Clinched Week:</strong> {season.clinched_week ?? "—"}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

function RecordCard({ title, value, season }) {
    return (
        <div className="record-card">
            <h4>{title}</h4>
            <div className="record-value">{value}</div>
            <div className="record-season">Season {season}</div>
        </div>
    );
}
