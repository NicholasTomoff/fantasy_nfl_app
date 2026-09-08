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
import { useUser } from "@/context/UserContext";
import { useLeague } from "@/context/LeagueContext";
import "../styles/streakHistory.css";

export default function StreakHistoryPage() {
    const { user } = useUser();
    const { activeLeagueId } = useLeague();

    const [viewMode, setViewMode] = useState("league");
    // Follow whichever league you are actually in. This used to be hardcoded to
    // 1, so every league showed the OGs' history.
    const [leagueId, setLeagueId] = useState(activeLeagueId ?? null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    // Only your own leagues -- /api/leagues/all lists every league on the site.
    const leagues = Array.isArray(user?.leagues) ? user.leagues : [];

    useEffect(() => {
        if (activeLeagueId && leagueId == null) setLeagueId(activeLeagueId);
    }, [activeLeagueId, leagueId]);

    // Fall back to the first league you belong to if nothing is active yet.
    useEffect(() => {
        if (leagueId == null && leagues.length > 0) setLeagueId(leagues[0].id);
    }, [leagues, leagueId]);

    useEffect(() => {
        if (viewMode === "league" && leagueId == null) {
            setHistory([]);
            setLoading(false);
            return;
        }
        setLoading(true);
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
            })
            .finally(() => setLoading(false));
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
                        value={leagueId ?? ""}
                        onChange={(e) => setLeagueId(e.target.value ? Number(e.target.value) : null)}
                    >
                        {leagues.length === 0 && (
                            <option value="">
                                {user ? "You're not in any leagues yet" : "Sign in to pick a league"}
                            </option>
                        )}
                        {leagues.map(l => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                    </select>
                </div>
            )}

            {!loading && history.length === 0 && (
                <div className="empty-state">
                    <h3>No history yet</h3>
                    <p>
                        {viewMode === "league"
                            ? (leagues.find(l => l.id === leagueId)?.name
                                ? `${leagues.find(l => l.id === leagueId).name} hasn't finished a season yet.`
                                : "This league hasn't finished a season yet.")
                            : "No completed seasons on record yet."}
                    </p>
                    <p className="empty-hint">
                        Records and the trend chart appear here once a season wraps up.
                    </p>
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

            {history.length > 0 && (
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
            )}

            {/* SEASON CARDS */}
            <div className="stat-card-grid">
                {/* Newest season first. The chart stays chronological so the
                    trend lines still read left-to-right. */}
                {[...history].reverse().map(season => (
                    <div key={season.season} className="season-card">
                        <h3>{season.season}</h3>

                        <div className="card-group">
                            <CardRow label="Champion" value={season.champion_name} tone="gold" />
                            <CardRow label="Runner-Up" value={season.runner_up_name} tone="silver" />
                            <CardRow label="Third" value={season.third_place_name} tone="bronze" />
                        </div>

                        <div className="card-group">
                            <CardRow
                                label="Best Start"
                                value={season.best_triple_start}
                                holder={season.best_triple_start_name}
                                tone="green"
                            />
                            <CardRow
                                label="Longest Triple"
                                value={season.longest_triple_streak}
                                holder={season.longest_triple_name}
                                tone="indigo"
                            />
                            <CardRow
                                label="Most Triples"
                                value={season.most_triples_in_season}
                                holder={season.most_triples_name}
                                tone="orange"
                            />
                        </div>

                        <div className="card-group">
                            <CardRow label="QB" value={season.longest_qb_streak} holder={season.longest_qb_name} tone="qb" />
                            <CardRow label="RB" value={season.longest_rb_streak} holder={season.longest_rb_name} tone="rb" />
                            <CardRow label="WR" value={season.longest_wr_streak} holder={season.longest_wr_name} tone="wr" />
                        </div>

                        <div className="card-group">
                            <CardRow label="Players" value={season.member_count} />
                            <CardRow
                                label="Clinched"
                                value={season.clinched_week ? `Week ${season.clinched_week}` : season.clinched_note ?? "—"}
                            />
                            {season.winner_score != null && (
                                <CardRow label="Winning Score" value={season.winner_score} />
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// One label/value line on a season card. `tone` tints the value so the eye can
// pick out a section without reading every label.
function CardRow({ label, value, holder, tone }) {
    if (value === null || value === undefined || value === "") return null;
    return (
        <p className="card-row">
            <span className="card-label">{label}</span>
            <span className={`card-value${tone ? ` tone-${tone}` : ""}`}>{value}</span>
            {holder && <span className="card-holder">{holder}</span>}
        </p>
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
