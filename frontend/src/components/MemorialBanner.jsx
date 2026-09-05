import React from "react";

/**
 * A remembrance shown on a specific league's page for a specific season.
 *
 * Deliberately kept as a small, explicit list rather than something
 * data-driven: these are personal, rare, and should be changed on purpose.
 */
const MEMORIALS = [
    {
        leagueId: 1,
        seasonYear: 2026,
        name: "Cody Nevers",
        detail: "2023 Champion and dear friend",
    },
];

const MemorialBanner = ({ leagueId, seasonYear }) => {
    const memorial = MEMORIALS.find(
        (m) => m.leagueId === Number(leagueId) && m.seasonYear === Number(seasonYear)
    );

    if (!memorial) return null;

    return (
        <div className="mt-4 rounded-xl border border-white/25 bg-black/20 px-5 py-4 text-center">
            <p className="text-blue-100 text-sm tracking-wide uppercase">In memory of</p>
            <p className="text-white text-2xl font-semibold mt-1">{memorial.name}</p>
            <p className="text-blue-100 text-sm mt-1">{memorial.detail}</p>
        </div>
    );
};

export default MemorialBanner;
