import React, { useEffect, useState, useMemo } from "react";
import UserWeeklyTable from "../components/UserWeeklyTable";

import { Link } from "react-router-dom";
import { useUser } from "@/context/UserContext";
import { useSeason } from "@/context/SeasonContext";
import { useLeague } from "@/context/LeagueContext";

import { getLeagueDetails, joinLeague, generateInviteLink } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Banner from "@/components/Banner";
import { toast } from "sonner";
import { Copy } from "lucide-react";
import { apiFetch } from "@/services/api";

const POSITIONS = ["QB", "RB", "WR"];

const LeaguePage = () => {
    const { user } = useUser();
    const { activeLeagueId } = useLeague();

    const token = user?.token || ""; // fix missing token

    const [league, setLeague] = useState(null);
    const [inviteUrl, setInviteUrl] = useState("");
    const [allSeasons, setAllSeasons] = useState([]);
    const { season, setSeason, currentWeek, setCurrentWeek, currentFinalizedWeek, setCurrentFinalizedWeek } = useSeason();

    const [playersByPosition, setPlayersByPosition] = useState({ QB: [], RB: [], WR: [] });
    const [playersLoaded, setPlayersLoaded] = useState(false);

    const [selectedUserEmail, setSelectedUserEmail] = useState(null);
    const [standings, setStandings] = useState([]);

    // Inside your LeaguePage component
    const [viewMode, setViewMode] = useState("USER"); // "weekly" or "users"
    const [selectedWeek, setSelectedWeek] = useState(null); // null = All Weeks

    const fetchSeasons = async () => {
        try {
            const res = await apiFetch("/api/seasons/all");
            const data = await res.json();
            setAllSeasons(data);

            const current = data.find((s) => s.is_current);
            const initialSeason = current?.year || data[0]?.year;

            // Only set season if it's not already set
            if (!season) {
                setSeason(initialSeason);
            }
        } catch (err) {
            console.error("Failed to fetch seasons", err);
        }
    };

    const fetchLeague = async () => {
        try {
            const data = await getLeagueDetails(activeLeagueId);
            setLeague(data);
        } catch {
            toast.error("Error loading league");
        }
    };

    const [allPicks, setAllPicks] = useState([]);

    const fetchAllPicks = async () => {
        if (!activeLeagueId || !season) return;

        const res = await apiFetch(
            `/api/picks/league/${activeLeagueId}/season/${season}/with-weeklyhits`
        );

        const { picks, weekly_hits } = await res.json();

        const merged = picks.map(pick => ({
            ...pick,
            ...(weekly_hits.find(
                h => h.user_email === pick.user_email && h.week === pick.week
            ) || {})
        }));

        setAllPicks(merged);
    };

    const selectedEmail = selectedUserEmail || user.email;

    const weeklyPicksByWeek = useMemo(() => {
        const result = {};
        allPicks
            .filter(p => p.user_email === selectedEmail)
            .forEach(p => {
                result[p.week] = p;
            });
        return result;
    }, [allPicks, selectedEmail]);

    const weeklyPicksByUser = useMemo(() => {
        const result = {};
        allPicks.forEach(p => {
            if (!result[p.user_email]) result[p.user_email] = {};
            result[p.user_email][p.week] = p;
        });
        return result;
    }, [allPicks]);

    // State to track selected position per user email
    const [selectedPositions, setSelectedPositions] = useState({});

    // Handler for updating selected position per user
    const handlePositionChange = (email, newPos) => {
        setSelectedPositions(prev => ({
            ...prev,
            [email]: newPos,
        }));
    };

    // Helper to get streak, weekly points, season total for position (optional to define here or inline)
    const getPositionPoints = (pick, pos) => {
        if (!pick) return { streak: 0, points: 0, seasonTotal: 0 };
        const streakKey = `${pos.toLowerCase()}_streak`;
        const pointsKey = `${pos.toLowerCase()}_points`;
        return {
            streak: pick[streakKey] || 0,
            points: pick[pointsKey] || 0,
            seasonTotal: pick.total_points || 0,
        };
    };

    useEffect(() => {
        const fetchPlayers = async () => {
            try {
                const results = await Promise.all(
                    POSITIONS.map((pos) => apiFetch(`/api/players/${pos}`).then((res) => res.json()))
                );
                const updated = {};
                results.forEach((data, i) => {
                    const pos = POSITIONS[i];
                    updated[pos] = data;
                });
                setPlayersByPosition(updated);
                setPlayersLoaded(true);
            } catch (error) {
                console.error("Failed to load players:", error);
            }
        };
        fetchPlayers();
    }, []);

    useEffect(() => {
        fetchSeasons();
    }, []);

    useEffect(() => {
        fetchLeague();
        fetchAllPicks();
    }, [activeLeagueId, season]);

    // Fetch current week when season changes
    useEffect(() => {
        if (!season) return;

        const fetchCurrentWeek = async () => {
            try {
                const res = await apiFetch(`/api/weeks/current?season=${season}`);
                const data = await res.json();
                setCurrentWeek(data.week);
                console.log("Current week set to:", data.week);
            } catch (err) {
                console.error("Failed to fetch current week", err);
            }
        };
        fetchCurrentWeek();

        const fetchCurrentFinalizedWeek = async () => {
            try {
                const res = await apiFetch(`/api/weeks/finalized?season=${season}`);
                const data = await res.json();
                setCurrentFinalizedWeek(data.week);
                console.log("Finalized week set to:", data.week);
            } catch (err) {
                console.error("Failed to fetch finalized week", err);
            }
        };
        fetchCurrentFinalizedWeek();
    }, [season]);

    // Fetch standings based on last finalized week
    useEffect(() => {
        if (!activeLeagueId || !season || !currentFinalizedWeek) return;

        apiFetch(`/api/standings?week=${currentFinalizedWeek}&league_id=${activeLeagueId}&season=${season}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then((data) => {
                //     console.log("Standings response data:", data); 
                setStandings(data);
            }).catch((err) => console.error("Failed to fetch standings:", err));
    }, [activeLeagueId, season, currentWeek, currentFinalizedWeek, token]);

    const findPlayer = (pos, playerId) =>
        playersByPosition[pos]?.find((p) => String(p.player_id) === String(playerId)) || null;

    const isMember = league?.members?.some((m) => m.user?.id === user?.id);
    const pendingInvite = league?.pending_invite;
    const showJoin = !isMember && pendingInvite;

    const getColor = (pts, threshold) =>
        pts >= threshold ? "text-green-600 font-semibold" : "text-red-500";

    return (
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
            {!league ? (
                <div>Loading...</div>
            ) : (
                <>
                    {/* Top section - blue with league name, top 3, invite and standings */}
                    <div className="bg-blue-600 text-white rounded-2xl shadow-md p-6 space-y-4">
                        {/* Banner Title & Subtitle + Invite button right aligned */}
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                            <div>
                                <h1 className="text-3xl font-bold drop-shadow-md">
                                    League Name: <span className="text-yellow-400 mr-2">{league.name}</span>
                                </h1>
                                <p className="text-blue-100 drop-shadow-sm">Members: {league.members?.length || 0}</p>
                            </div>

                            {/* Invite to League Button right aligned */}
                            {isMember && (
                                <div className="text-right">
                                    <Button
                                        onClick={() => {
                                            if (!user) {
                                                toast.error("User not logged in");
                                                return;
                                            }
                                            generateInviteLink(activeLeagueId, user)
                                                .then((res) => {
                                                    const fullUrl = `${window.location.origin}${res.invite_url || res.url || res.link}`;
                                                    setInviteUrl(fullUrl);
                                                    navigator.clipboard.writeText(fullUrl);
                                                    toast.success("Invite link copied to clipboard");
                                                })
                                                .catch(() => toast.error("Error generating invite link"));
                                        }}
                                        variant="outline"
                                        size="sm"
                                        className="bg-white text-blue-700 hover:bg-gray-100 shadow inline-flex items-center"
                                    >
                                        <Copy className="w-4 h-4 mr-1" />
                                        Invite to League
                                    </Button>

                                    {inviteUrl && (
                                        <p className="mt-2 text-blue-100 break-words max-w-xs ml-auto">
                                            Invite Link:{" "}
                                            <a href={inviteUrl} target="_blank" rel="noopener noreferrer" className="underline">
                                                {inviteUrl}
                                            </a>
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Optional Banner Image */}
                        {league.banner && (
                            <div className="w-full mt-4">
                                <img
                                    src={league.banner}
                                    alt="League Banner"
                                    className="rounded-xl w-full max-h-64 object-cover shadow-lg"
                                />
                            </div>
                        )}

                        {/* Lower box: Join button left, Top 3 users left-aligned, View Standings right-aligned */}
                        <div className="bg-blue-500/30 rounded-xl p-4 mt-4">
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                                {/* Left side vertical stack: Join button and Top 3 users horizontally */}
                                <div>
                                    {/* Join button if applicable */}
                                    {showJoin && (
                                        <Button
                                            className="bg-yellow-400 text-black hover:bg-yellow-500 shadow mb-4"
                                            onClick={() => {
                                                joinLeague(activeLeagueId)
                                                    .then(() => {
                                                        toast.success("Joined league");
                                                        fetchLeague();
                                                        fetchAllPicks();
                                                    })
                                                    .catch(() => toast.error("Error joining league"));
                                            }}
                                        >
                                            Join this League
                                        </Button>
                                    )}

                                    {/* Top 3 users horizontal list */}
                                    {league.members && league.members.length > 0 ? (
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-white w-full">
                                            {(() => {
                                                // 1. Map members to include total_points from standings
                                                const membersWithPoints = league.members.map((member) => {
                                                    const standing = standings.find((s) => s.user_name === member.user?.name);
                                                    return {
                                                        ...member,
                                                        user: {
                                                            ...member.user,
                                                            total_points: standing?.total_points ?? 0,
                                                        },
                                                    };
                                                });

                                                // 2. Sort descending by points
                                                membersWithPoints.sort((a, b) => b.user.total_points - a.user.total_points);

                                                // 3. Compute ranks with ties
                                                let lastPoints = null;
                                                let lastRank = 0;
                                                let displayed = 0;

                                                return membersWithPoints.slice(0, 3).map((member, idx) => {
                                                    const points = member.user.total_points;
                                                    let rank;

                                                    if (points === lastPoints) {
                                                        rank = lastRank; // tie with previous
                                                    } else {
                                                        rank = idx + 1;
                                                        lastRank = rank;
                                                        lastPoints = points;
                                                    }

                                                    return (
                                                        <div
                                                            key={member.id}
                                                            className="bg-blue-700 rounded-xl p-3 shadow-md text-center"
                                                            title={`${member.user?.name || member.user?.email}\n${member.user.total_points} pts`}
                                                        >
                                                            <div className="text-yellow-300 font-extrabold text-2xl mb-1">#{rank}</div>
                                                            <div className="font-semibold text-white truncate">
                                                                {member.user?.name || member.user?.email || "Unknown"}
                                                            </div>
                                                            <div className="text-yellow-400 font-bold">{member.user.total_points} pts</div>
                                                        </div>
                                                    );
                                                });
                                            })()}
                                        </div>
                                    ) : (
                                        <p className="italic text-blue-200">No members found.</p>
                                    )}


                                </div>

                                {/* Right-aligned action buttons */}
                                <div className="flex justify-end gap-2 mt-4 md:mt-0">
                                    <Link to={`/standings/`}>
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            className="bg-white text-blue-700 hover:bg-gray-100 shadow"
                                        >
                                            View Standings
                                        </Button>
                                    </Link>
                                </div>

                            </div>
                        </div>
                    </div>

                    {/* Weekly Picks Section with Toggle */}
                    <Card className="bg-gray-50">
                        <CardContent className="py-4">
                            {/* Header and Toggle */}
                            <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-4 space-y-3 md:space-y-0">
                                <h2 className="text-lg font-semibold text-gray-900">Weekly Picks</h2>
                                <div className="flex items-center space-x-2">
                                    {/* Season Selector */}
                                    <select
                                        className="border rounded px-3 py-2 text-md max-w-[100px] bg-white text-gray-900"
                                        value={season}
                                        onChange={(e) => setSeason(parseInt(e.target.value))}
                                        aria-label="Select Season"
                                    >
                                        {allSeasons.map((s) => (
                                            <option key={s.year} value={s.year}>
                                                {s.year}
                                            </option>
                                        ))}
                                    </select>

                                    {/* User Selector */}
                                    <select
                                        className="border rounded px-3 py-2 text-md bg-white text-gray-900"
                                        value={selectedUserEmail || user.email}
                                        onChange={(e) => {
                                            const email = e.target.value;
                                            setSelectedUserEmail(email === user.email ? null : email);
                                        }}
                                        aria-label="Select User"
                                    >
                                        {league.members.map((member) => (
                                            <option key={member.user?.email} value={member.user?.email}>
                                                {member.user?.name || member.user?.email}{" "}
                                                {member.user?.email === user.email ? "(You)" : ""}
                                            </option>
                                        ))}
                                    </select>

                                    {/* View Toggle */}
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-gray-700">View:</span>

                                        <button
                                            onClick={() => setViewMode("USER")}
                                            className={`px-3 py-1 rounded border text-sm font-medium
                                                ${viewMode === "USER"
                                                    ? "bg-blue-600 text-white border-blue-600"
                                                    : "bg-white text-blue-600 border-blue-600 hover:bg-blue-50"}
                                            `}
                                        >
                                            By User
                                        </button>

                                        <button
                                            onClick={() => setViewMode("ALL_USERS")}
                                            className={`px-3 py-1 rounded border text-sm font-medium
                                                ${viewMode === "ALL_USERS"
                                                    ? "bg-blue-600 text-white border-blue-600"
                                                    : "bg-white text-blue-600 border-blue-600 hover:bg-blue-50"}
                                             `}
                                        >
                                            All Users
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Weekly View Mode */}
                            {viewMode === "USER" ? (
                                <>
                                    <UserWeeklyTable
                                        weeks={Array.from({ length: 18 }, (_, i) => i + 1)}
                                        picksByWeek={weeklyPicksByWeek}
                                        playersByPosition={playersByPosition}
                                        selectedPosition={selectedPositions[selectedEmail] || "ALL"}
                                        findPlayer={findPlayer}
                                        getColor={getColor}
                                        playersLoaded={playersLoaded}
                                    />
                                </>
                            ) : (
                                // ALL_USERS view
                                <div className="space-y-6">
                                    {/* Week Selector for ALL_USERS */}
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="font-semibold text-sm">Select Week:</span>
                                        <select
                                            className="border rounded px-2 py-1 text-sm"
                                            value={selectedWeek || "ALL"}
                                            onChange={(e) =>
                                                setSelectedWeek(e.target.value === "ALL" ? null : parseInt(e.target.value))
                                            }
                                        >
                                            <option value="ALL">All Weeks</option>
                                            {Array.from({ length: 18 }, (_, i) => (
                                                <option key={i + 1} value={i + 1}>{i + 1}</option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Users Table */}
                                    <div className="overflow-x-auto relative before:content-[''] before:absolute before:top-0 before:right-0 before:w-8 before:h-full before:pointer-events-none before:bg-gradient-to-l before:from-white before:to-transparent">
                                        <table className="min-w-full table-auto border-collapse border border-gray-300 text-sm text-gray-900">
                                            <thead>
                                                <tr className="bg-gray-100">
                                                    <th className="px-2 py-1 border text-left font-semibold">Week</th>
                                                    <th className="px-2 py-1 border text-left font-semibold">User</th>
                                                    <th className="px-2 py-1 border text-left font-semibold">QB</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">QB Pts</th>
                                                    <th className="px-2 py-1 border text-left font-semibold">RB</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">RB Pts</th>
                                                    <th className="px-2 py-1 border text-left font-semibold">WR</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">WR Pts</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">Triple Bonus</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">Weekly Total</th>
                                                    <th className="px-2 py-1 border text-right font-semibold">Season Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => {
                                                    if (selectedWeek && week !== selectedWeek) return null;

                                                    return league.members.map((member) => {
                                                        const email = member.user?.email || member.email;
                                                        const picks = weeklyPicksByUser[email] || {};
                                                        const pick = picks[week] || picks[week.toString()] || {};
                                                        const firstPickWithUser = Object.values(picks).find(p => p.user && p.user.name);
                                                        const username = pick.user?.name || member.user?.name || email;
                                                        const selectedPosition = selectedPositions[email] || "ALL";

                                                        const qbPoints = pick.qb_points ?? 0;
                                                        const rbPoints = pick.rb_points ?? 0;
                                                        const wrPoints = pick.wr_points ?? 0;
                                                        const tripleBonus = pick.all_positions_bonus ?? 0;
                                                        const weeklyTotal = qbPoints + rbPoints + wrPoints + tripleBonus;
                                                        const totalPoints = pick.total_points ?? weeklyTotal;

                                                        return (
                                                            <tr key={`${week}-${email}`} className="even:bg-gray-50 border border-gray-300">
                                                                <td className="px-2 py-1 border font-medium text-gray-900">{week}</td>
                                                                <td className="px-2 py-1 border font-medium text-gray-900 truncate max-w-[150px]">{username}</td>

                                                                {(selectedPosition === "ALL" || selectedPosition === "QB") && (
                                                                    <>
                                                                        <td className={`px-2 py-1 border truncate ${getColor(qbPoints, 1)}`}>
                                                                            {playersLoaded ? findPlayer("QB", pick.qb)?.player_name || "-" : "Loading..."}
                                                                        </td>
                                                                        <td className={`px-2 py-1 border text-right ${getColor(qbPoints, 1)}`}>{qbPoints}</td>
                                                                    </>
                                                                )}

                                                                {(selectedPosition === "ALL" || selectedPosition === "RB") && (
                                                                    <>
                                                                        <td className={`px-2 py-1 border truncate ${getColor(rbPoints, 1)}`}>
                                                                            {playersLoaded ? findPlayer("RB", pick.rb)?.player_name || "-" : "-"}
                                                                        </td>
                                                                        <td className={`px-2 py-1 border text-right ${getColor(rbPoints, 1)}`}>{rbPoints}</td>
                                                                    </>
                                                                )}

                                                                {(selectedPosition === "ALL" || selectedPosition === "WR") && (
                                                                    <>
                                                                        <td className={`px-2 py-1 border truncate ${getColor(wrPoints, 1)}`}>
                                                                            {playersLoaded ? findPlayer("WR", pick.wr)?.player_name || "-" : "-"}
                                                                        </td>
                                                                        <td className={`px-2 py-1 border text-right ${getColor(wrPoints, 1)}`}>{wrPoints}</td>
                                                                    </>
                                                                )}

                                                                <td className={`px-2 py-1 border text-right font-semibold ${getColor(tripleBonus, 1)}`}>
                                                                    {tripleBonus === 0 ? "0" : `+${tripleBonus}`}
                                                                </td>
                                                                <td className="px-2 py-1 border text-right font-semibold">{weeklyTotal}</td>
                                                                <td className="px-2 py-1 border text-right font-semibold">{totalPoints}</td>
                                                            </tr>
                                                        );
                                                    });
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>




                            )}
                        </CardContent>
                    </Card>


                    {/* League Members List */}
                    <Card className="bg-gray-50">
                        <CardContent className="py-4">
                            <h2 className="text-lg font-semibold mb-2 text-gray-900">League Members</h2>
                            <ul className="list-disc list-inside space-y-1 max-h-48 overflow-y-auto text-gray-900">
                                {league.members?.length > 0 ? (
                                    league.members.map((member) => (
                                        <li key={member.id} title={member.user?.email || ""}>
                                            {member.user?.name || member.user?.email || "Unknown Member"}
                                        </li>
                                    ))
                                ) : (
                                    <li className="italic text-gray-500">No members found.</li>
                                )}
                            </ul>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
};

export default LeaguePage;