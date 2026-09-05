// components/UserWeeklyTable.jsx
import React from "react";

const getColor = (pts, threshold) =>
    pts >= threshold ? "text-green-600 font-semibold" : "text-red-500";

const UserWeeklyTable = ({
    weeks = Array.from({ length: 18 }, (_, i) => i + 1),
    picksByWeek = {},
    playersByPosition = { QB: [], RB: [], WR: [] },
    selectedPosition = "ALL",
    findPlayer = () => null,
    playersLoaded = false,
}) => {
    return (
        <div className="space-y-4">
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto rounded-md border border-gray-300">
                <table className="min-w-full text-sm bg-white text-gray-900">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-2 py-1 border w-[8%] text-left">Week</th>
                            {(selectedPosition === "ALL" || selectedPosition === "QB") && (
                                <>
                                    <th className="px-2 py-1 border w-[14%] text-left">QB</th>
                                    <th className="px-2 py-1 border w-[8%] text-right">QB Pts</th>
                                </>
                            )}
                            {(selectedPosition === "ALL" || selectedPosition === "RB") && (
                                <>
                                    <th className="px-2 py-1 border w-[14%] text-left">RB</th>
                                    <th className="px-2 py-1 border w-[8%] text-right">RB Pts</th>
                                </>
                            )}
                            {(selectedPosition === "ALL" || selectedPosition === "WR") && (
                                <>
                                    <th className="px-2 py-1 border w-[14%] text-left">WR</th>
                                    <th className="px-2 py-1 border w-[8%] text-right">WR Pts</th>
                                </>
                            )}
                            <th className="px-2 py-1 border w-[10%] text-right font-semibold">Triple Bonus</th>
                            <th className="px-2 py-1 border w-[8%] text-right font-semibold">Weekly Total</th>
                            <th className="px-2 py-1 border w-[10%] text-right font-semibold">Season Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {weeks.map((week) => {
                            const pick = picksByWeek[week] || picksByWeek[week.toString()];
                            if (!pick) return null;

                            const qbPoints = pick.qb_points ?? 0;
                            const rbPoints = pick.rb_points ?? 0;
                            const wrPoints = pick.wr_points ?? 0;
                            const tripleBonus = pick.all_positions_bonus ?? 0;
                            const weeklyTotal = qbPoints + rbPoints + wrPoints + tripleBonus;
                            const totalPoints = pick.total_points ?? weeklyTotal;

                            return (
                                <tr key={week} className="even:bg-gray-50">
                                    <td className="px-2 py-1 border font-medium">{week}</td>

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
                                                {playersLoaded ? findPlayer("RB", pick.rb)?.player_name || "-" : "Loading..."}
                                            </td>
                                            <td className={`px-2 py-1 border text-right ${getColor(rbPoints, 1)}`}>{rbPoints}</td>
                                        </>
                                    )}

                                    {(selectedPosition === "ALL" || selectedPosition === "WR") && (
                                        <>
                                            <td className={`px-2 py-1 border truncate ${getColor(wrPoints, 1)}`}>
                                                {playersLoaded ? findPlayer("WR", pick.wr)?.player_name || "-" : "Loading..."}
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
                        })}
                    </tbody>
                </table>
            </div>

            {/* Mobile Card View */}
            <div className="block md:hidden space-y-4">
                {weeks.map((week) => {
                    const pick = picksByWeek[week] || picksByWeek[week.toString()];
                    if (!pick) return null;

                    const qbPoints = pick.qb_points ?? 0;
                    const rbPoints = pick.rb_points ?? 0;
                    const wrPoints = pick.wr_points ?? 0;
                    const tripleBonus = pick.all_positions_bonus ?? 0;
                    const weeklyTotal = qbPoints + rbPoints + wrPoints + tripleBonus;
                    const totalPoints = pick.total_points ?? weeklyTotal;

                    return (
                        <div key={week} className="border border-gray-300 rounded-md p-4 bg-white shadow-sm">
                            <div className="text-lg font-semibold text-gray-800 mb-2">Week {week}</div>
                            <div className="space-y-1 text-sm text-gray-700">
                                {(selectedPosition === "ALL" || selectedPosition === "QB") && (
                                    <div>
                                        <span className="font-medium">QB:</span>{" "}
                                        {playersLoaded ? findPlayer("QB", pick.qb)?.player_name || "-" : "Loading..."}{" "}
                                        <span className={`float-right font-semibold ${getColor(qbPoints, 1)}`}>{qbPoints}</span>
                                    </div>
                                )}
                                {(selectedPosition === "ALL" || selectedPosition === "RB") && (
                                    <div>
                                        <span className="font-medium">RB:</span>{" "}
                                        {playersLoaded ? findPlayer("RB", pick.rb)?.player_name || "-" : "Loading..."}{" "}
                                        <span className={`float-right font-semibold ${getColor(rbPoints, 1)}`}>{rbPoints}</span>
                                    </div>
                                )}
                                {(selectedPosition === "ALL" || selectedPosition === "WR") && (
                                    <div>
                                        <span className="font-medium">WR:</span>{" "}
                                        {playersLoaded ? findPlayer("WR", pick.wr)?.player_name || "-" : "Loading..."}{" "}
                                        <span className={`float-right font-semibold ${getColor(wrPoints, 1)}`}>{wrPoints}</span>
                                    </div>
                                )}
                                <div>
                                    <span className="font-medium">Triple Bonus:</span>{" "}
                                    <span className={`float-right font-semibold ${tripleBonus === 0 ? "text-red-500" : "text-green-600"}`}>
                                        {tripleBonus === 0 ? "0" : `+${tripleBonus}`}
                                    </span>
                                </div>
                                <div className="pt-2 border-t mt-2">
                                    <span className="font-semibold">Weekly Total:</span>{" "}
                                    <span className="float-right font-semibold">{weeklyTotal}</span>
                                </div>
                                <div>
                                    <span className="font-semibold">Season Total:</span>{" "}
                                    <span className="float-right font-semibold">{totalPoints}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default UserWeeklyTable;
