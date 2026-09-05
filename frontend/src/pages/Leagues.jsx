import React, { useEffect, useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";
import { useSeason } from "@/context/SeasonContext";
import { useLeague } from "@/context/LeagueContext";

// Dummy leagues for public display
const dummyLeagues = [
    {
        id: 100,
        name: "Gridiron Warriors",
        leader: {
            name: "SpeedySam",
            points: 210,
            avatar: "https://ui-avatars.com/api/?name=Speedy+Sam&background=4CAF50&color=fff&size=64",
            status: "2024 Season Winner",
        },
        top3: [
            { name: "SpeedySam", points: 210, medal: "🥇" },
            { name: "AceAlex", points: 198, medal: "🥈" },
            { name: "BronzeBen", points: 185, medal: "🥉" },
        ],
        membersCount: 10,
        minPlayers: 4,
        banner: "https://images.pexels.com/photos/7005488/pexels-photo-7005488.jpeg",
        members: [], // Important: members is an array of member objects, empty here
    },
    {
        id: 200,
        name: "Sunday Showstoppers",
        leader: {
            name: "FlashFinn",
            points: 195,
            avatar: "https://ui-avatars.com/api/?name=Flash+Finn&background=1E40AF&color=fff&size=64",
            status: "2024 Season Winner",
        },
        top3: [
            { name: "FlashFinn", points: 195, medal: "🥇" },
            { name: "QuickQuinn", points: 179, medal: "🥈" },
            { name: "SneakySue", points: 171, medal: "🥉" },
        ],
        membersCount: 8,
        minPlayers: 4,
        banner: "https://images.pexels.com/photos/7005503/pexels-photo-7005503.jpeg",
        members: [],
    },
    {
        id: 300,
        name: "Pigskin Power",
        leader: {
            name: "RocketRon",
            points: 160,
            avatar: "https://ui-avatars.com/api/?name=Rocket+Ron&background=F97316&color=fff&size=64",
            status: "2024 Season Winner",
        },
        top3: [
            { name: "RocketRon", points: 160, medal: "🥇" },
            { name: "BlazeBeth", points: 150, medal: "🥈" },
            { name: "HustleHank", points: 140, medal: "🥉" },
        ],
        membersCount: 6,
        minPlayers: 4,
        banner: "https://images.pexels.com/photos/923191/pexels-photo-923191.jpeg",
        members: [],
    },
];

const DEFAULT_BANNERS = [
    "https://images.pexels.com/photos/7005488/pexels-photo-7005488.jpeg",
    "https://images.pexels.com/photos/7005503/pexels-photo-7005503.jpeg",
    "https://images.pexels.com/photos/923191/pexels-photo-923191.jpeg",
];

const trophyIcons = {
    gold: "https://cdn-icons-png.flaticon.com/128/11167/11167970.png",
    silver: "https://cdn-icons-png.flaticon.com/128/11167/11167972.png",
    bronze: "https://cdn-icons-png.flaticon.com/128/11167/11167976.png",
};

// Helper to generate initials from full name (e.g. "John Doe" => "J D")
const getInitials = (fullName) => {
    if (!fullName) return "UN";
    const names = fullName.trim().split(" ");
    if (names.length === 1) return names[0][0].toUpperCase();
    return (names[0][0] + " " + names[names.length - 1][0]).toUpperCase();
};

// Helper to build avatar URL from name or initials
const getAvatarUrl = (name) => {
    const initials = getInitials(name);
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&background=666&color=fff&size=64`;
};

const Leagues = () => {
    const [backendLeagues, setBackendLeagues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [joiningId, setJoiningId] = useState(null);
    const [allSeasons, setAllSeasons] = useState([]);
    const { season, setSeason, currentWeek, currentFinalizedWeek, setCurrentWeek, setCurrentFinalizedWeek } = useSeason();
    const navigate = useNavigate();
    const { user } = useUser();
    const { setActiveLeagueId } = useLeague();
    const [fetchFailed, setFetchFailed] = useState(false);


    async function fetchLeagues(season) {
        const token = localStorage.getItem("token");

        try {
            const res = await apiFetch(`/api/leagues/all`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });

            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            const data = await res.json();
            if (!Array.isArray(data)) throw new Error("Invalid data format received");

            const enriched = await Promise.all(
                data.map(async (league, index) => {
                    let membersArray = [];

                    if (Array.isArray(league.members)) {
                        membersArray = league.members;
                    } else if (Array.isArray(league.memberList)) {
                        membersArray = league.memberList.map((m) =>
                            typeof m === "object" && m.user ? m : { user: m }
                        );
                    }

                    let top3 = [];
                    let leader = null;

                    try {
                        const standingsRes = await apiFetch(
                            `/api/standings?week=${currentFinalizedWeek}&league_id=${league.id}&season=${season}`,
                            {
                                headers: token ? { Authorization: `Bearer ${token}` } : {},
                            }
                        );

                        if (standingsRes.ok) {
                            const standings = await standingsRes.json();
                            standings.sort((a, b) => b.total_points - a.total_points);

                            top3 = standings.slice(0, 3).map((user, idx) => ({
                                name: user.user_name,
                                points: user.total_points,
                                medal: idx === 0 ? "🥇" : idx === 1 ? "🥈" : "🥉",
                            }));

                            if (standings.length > 0) {
                                const topUser = standings[0];
                                leader = {
                                    name: topUser.user_name,
                                    points: topUser.total_points,
                                    avatar:
                                        topUser.avatar || getAvatarUrl(topUser.user_name),
                                    status: `${season} Season Leader`,
                                };
                            }
                        }
                    } catch (e) {
                        console.warn("Could not fetch standings for league", league.id, e);
                    }

                    return {
                        ...league,
                        banner:
                            league.banner ||
                            DEFAULT_BANNERS[index % DEFAULT_BANNERS.length],
                        leader: leader || {
                            name: "TBD",
                            points: 0,
                            avatar:
                                "https://ui-avatars.com/api/?name=TBD&background=666&color=fff&size=64",
                            status: "",
                        },
                        top3,
                        membersCount: membersArray.length,
                        members: membersArray,
                        minPlayers: league.minPlayers ?? 4,
                    };
                })
            );

            setBackendLeagues(enriched);
            setFetchFailed(false); // ✅ Success
            setError("");
        } catch (err) {
            console.error("Failed to fetch backend leagues:", err);
            setError("Could not load real leagues. Showing only demo leagues.");
            setBackendLeagues([]); // ✅ So we don’t merge with stale values
            setFetchFailed(true); // ✅ Trigger fallback rendering
        } finally {
            setLoading(false);
        }
    }


    // ⬇️ Fetch seasons and set default
    useEffect(() => {
        const fetchSeasons = async () => {
            try {
                const res = await apiFetch("/api/seasons/all");
                const data = await res.json();
                setAllSeasons(data);

                const current = data.find((s) => s.is_current);
                const initialSeason = current?.year || data[0]?.year;

                // ✅ Only set season if it's not already set
                if (!season) {
                    setSeason(initialSeason);
                }
            } catch (err) {
                console.error("Failed to fetch seasons", err);
            }
        };
        fetchSeasons();
    }, []);


    //     ⬇️ Fetch week and set current
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
    }, [season]);


    // ⬇️ Fetch leagues only when both season and currentWeek are ready
    useEffect(() => {
        console.log("Effect triggered with currentWeek =", currentWeek, "season =", season);

        if (season != null && currentWeek != null) {
            console.log("✅ Calling fetchLeagues()");
            fetchLeagues(season);
        } else {
            console.log("⛔ Skipping fetchLeagues — missing season or currentWeek");
        }
    }, [season, currentWeek]);



    const enrichedDummyLeagues = useMemo(() => {
        if (!currentWeek || !season) return [];

        return dummyLeagues.map((league, index) => ({
            ...league,
            banner: league.banner || DEFAULT_BANNERS[index % DEFAULT_BANNERS.length],
            season,
            currentWeek,
        }));
    }, [currentWeek, season]);

    const combinedLeagues = useMemo(() => {
        if (fetchFailed) return enrichedDummyLeagues;

        return [
            ...backendLeagues,
            ...enrichedDummyLeagues.filter(
                (d) => !backendLeagues.some((b) => b.id === d.id)
            ),
        ];
    }, [backendLeagues, enrichedDummyLeagues, fetchFailed]);



    const isUserInLeague = (league) => {
        if (!user?.id || !Array.isArray(league.members)) return false;
        return league.members.some(
            (member) => String(member?.user?.id) === String(user.id)
        );
    };

    const handleJoinLeague = async (leagueId) => {
        if (!user) {
            navigate("/login");
            return;
        }
        const token = localStorage.getItem("token");
        if (!token) return;
        try {
            setJoiningId(leagueId);
            const res = await apiFetch(`/api/leagues/${leagueId}/join`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer  ${token}`,
                },
                body: JSON.stringify({ user_id: user.id }),
            });
            if (!res.ok) {
                const errData = await res.json();
                alert("❌ Failed to join: " + errData.detail);
            } else {
                alert("🎉 Successfully joined the league!");
                setLoading(true);
                setBackendLeagues([]);
                await fetchLeagues(season);
            }
        } catch (err) {
            console.error(err);
            alert("Something went wrong. Please try again.");
        } finally {
            setJoiningId(null);
        }
    };

    return (
        <div className="max-w-6xl mx-auto py-6 px-4">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-2">
                <h1 className="text-3xl font-bold text-yellow-400">🏈 View Available Leagues</h1>

                <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                    <Link to="/create-league">
                        <Button className="bg-green-600 hover:bg-green-700 text-white">
                            + Create League
                        </Button>
                    </Link>
                </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">

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

            <p className="text-center text-gray-500 mb-4">As of Week {currentWeek}</p>

            {loading && <p className="text-center text-gray-400">Loading leagues...</p>}
            {error && <p className="text-center text-red-600 mb-4 font-semibold">{error}</p>}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {combinedLeagues.length === 0 && !loading ? (
                    <p className="text-center text-gray-400">No leagues found.</p>
                ) : (
                    combinedLeagues.map((league) => (
                        <div
                            key={league.id}
                            className="bg-gray-800 rounded-2xl shadow-lg overflow-hidden hover:scale-[1.02] transition-transform"
                        >
                            <img
                                src={league.banner}
                                alt={`${league.name} banner`}
                                className="w-full h-32 object-cover"
                                loading="lazy"
                                onError={(e) => {
                                    e.target.onerror = null;
                                    e.target.src =
                                        "https://via.placeholder.com/800x200.png?text=League+Banner";
                                }}
                            />
                            <div className="p-4">
                                <h2 className="text-xl font-bold text-white">{league.name}</h2>
                                <div className="mt-3 flex items-center space-x-4">
                                    <img
                                        src={league.leader.avatar}
                                        alt={league.leader.name}
                                        className="w-12 h-12 rounded-full"
                                    />
                                    <div>
                                        <div className="font-semibold text-white">{league.leader.name}</div>
                                        <div className="text-yellow-400 text-xs">{league.leader.status}</div>
                                    </div>
                                    <div className="ml-auto text-green-400 font-semibold text-sm">
                                        {league.leader.points} pts
                                    </div>
                                </div>
                                {league.top3?.length > 0 ? (
                                    <div className="mt-4 space-y-2 text-sm">
                                        {league.top3.map((u, idx) => {
                                            const isYou = u.name === user?.name;

                                            return (
                                                <div key={idx} className="flex items-center space-x-3">
                                                    <img
                                                        src={
                                                            trophyIcons[
                                                            u.medal === "🥇"
                                                                ? "gold"
                                                                : u.medal === "🥈"
                                                                    ? "silver"
                                                                    : "bronze"
                                                            ]
                                                        }
                                                        alt="Medal"
                                                        className="w-6 h-6"
                                                    />
                                                    <div>
                                                        <div>
                                                            {isYou ? (
                                                                <span className="text-lg font-bold text-orange-600">
                                                                    {u.name} <span className="text-sm font-normal">(You)</span>
                                                                </span>
                                                            ) : (
                                                                <span>{u.name}</span>
                                                            )}
                                                        </div>
                                                        <div className="text-xs text-gray-400">{u.points} pts</div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <div className="text-gray-500 text-sm mt-2">No top users yet.</div>
                                )}

                                <div className="text-xs text-gray-400 mt-3">
                                    {league.membersCount} players joined • Min to start: {league.minPlayers}
                                </div>
                                {isUserInLeague(league) ? (
                                    <Button
                                        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white"
                                        onClick={() => {
                                            setActiveLeagueId(league.id);
                                            navigate(`/leagues/${league.id}?season=${season}`);
                                        }}
                                    >
                                        View League
                                    </Button>
                                ) : (

                                    <Button
                                        className="mt-4 w-full bg-yellow-500 hover:bg-yellow-600 text-black"
                                        onClick={() => handleJoinLeague(league.id)}
                                        disabled={joiningId === league.id}
                                    >
                                        {joiningId === league.id ? "Joining..." : "Join League"}
                                    </Button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default Leagues;