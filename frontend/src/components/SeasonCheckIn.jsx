import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  getSeasonRoster,
  setMySeasonStatus,
  setMemberSeasonStatus,
  openSeason,
} from "@/services/api";

const STATUS_LABEL = { in: "In", out: "Sitting out", pending: "No answer yet" };
const STATUS_STYLE = {
  in: "bg-green-500/20 text-green-100 border-green-400/40",
  out: "bg-gray-500/20 text-gray-200 border-gray-400/40",
  pending: "bg-yellow-500/20 text-yellow-100 border-yellow-400/40",
};

/**
 * Per-season "are you in?" check-in.
 *
 * Members who sit a season out keep every pick, score and podium finish from
 * previous years -- they are simply not scored or ranked for this one.
 */
const SeasonCheckIn = ({ leagueId, seasonYear }) => {
  const [roster, setRoster] = useState(null);
  const [busy, setBusy] = useState(false);
  // Members whose status control the commissioner has explicitly revealed.
  const [editing, setEditing] = useState(() => new Set());

  const load = async () => {
    if (!leagueId || !seasonYear) return;
    try {
      setRoster(await getSeasonRoster(leagueId, seasonYear));
    } catch (err) {
      console.error("season roster error:", err);
      toast.error("Could not load the season roster");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leagueId, seasonYear]);

  const answer = async (status) => {
    setBusy(true);
    try {
      setRoster(await setMySeasonStatus(leagueId, seasonYear, status));
      toast.success(status === "in" ? `You're in for ${seasonYear}` : `Marked as sitting out ${seasonYear}`);
    } catch (err) {
      console.error(err);
      toast.error("Could not save your answer");
    } finally {
      setBusy(false);
    }
  };

  const setFor = async (userId, status) => {
    setBusy(true);
    try {
      setRoster(await setMemberSeasonStatus(leagueId, seasonYear, userId, status));
      setEditing((prev) => {
        const next = new Set(prev);
        next.delete(userId);
        return next;
      });
      toast.success("Updated");
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.detail || "Could not update that member");
    } finally {
      setBusy(false);
    }
  };

  const open = async () => {
    setBusy(true);
    try {
      setRoster(await openSeason(leagueId, seasonYear));
      toast.success(`${seasonYear} season opened for check-in`);
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.detail || "Could not open the season");
    } finally {
      setBusy(false);
    }
  };

  if (!roster) return null;

  const { my_status, is_commissioner, counts = {}, members = [] } = roster;
  const unanswered = counts.pending || 0;

  return (
    <div className="bg-blue-500/30 rounded-xl p-4 mt-4 space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h3 className="text-xl font-bold text-white">{seasonYear} Season</h3>
          <p className="text-blue-100 text-sm">
            {counts.in || 0} in · {counts.out || 0} out
            {unanswered > 0 && ` · ${unanswered} yet to answer`}
          </p>
        </div>

        {my_status === "pending" ? (
          <div className="flex items-center gap-2">
            <span className="text-white mr-1">Are you playing this season?</span>
            <Button
              disabled={busy}
              onClick={() => answer("in")}
              className="bg-green-500 text-white hover:bg-green-600 shadow"
            >
              I'm In
            </Button>
            <Button
              disabled={busy}
              onClick={() => answer("out")}
              className="bg-white text-blue-700 hover:bg-gray-100 shadow"
            >
              Sitting Out
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full border text-sm ${STATUS_STYLE[my_status]}`}>
              You: {STATUS_LABEL[my_status]}
            </span>
            <button
              disabled={busy}
              onClick={() => answer(my_status === "in" ? "out" : "in")}
              className="text-blue-100 underline text-sm hover:text-white"
            >
              Change
            </button>
          </div>
        )}
      </div>

      {is_commissioner && (
        <div className="border-t border-blue-300/30 pt-3 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-blue-100 text-sm font-semibold">Commissioner view</p>
            {members.every((m) => m.status === "pending") && (
              <Button
                disabled={busy}
                onClick={open}
                className="bg-yellow-400 text-black hover:bg-yellow-500 shadow"
              >
                Open {seasonYear} for check-in
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {members.map((m) => (
              <div key={m.user_id} className="bg-blue-700 rounded-xl p-3 shadow-md">
                {/* Name gets the full width of the card on its own line. Sharing
                    a flex row with the select squeezed it to one letter. */}
                <p className="text-white font-medium leading-snug">
                  {m.user_name || m.user_email}
                </p>

                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className={`px-2 py-0.5 rounded-full border text-xs whitespace-nowrap ${STATUS_STYLE[m.status]}`}>
                    {STATUS_LABEL[m.status]}
                    {m.set_by_commissioner && " · set by you"}
                  </span>

                  {/* Answered members just show their status. The control only
                      appears for people still to answer, or on demand. */}
                  {m.status === "pending" || editing.has(m.user_id) ? (
                    <select
                      disabled={busy}
                      value={m.status}
                      onChange={(e) => setFor(m.user_id, e.target.value)}
                      className="w-[76px] bg-blue-800 text-white text-xs rounded-md px-1 py-0.5 border border-blue-400/40"
                    >
                      <option value="in">In</option>
                      <option value="out">Out</option>
                      <option value="pending">—</option>
                    </select>
                  ) : (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => setEditing((prev) => new Set(prev).add(m.user_id))}
                      className="text-blue-200 underline text-xs hover:text-white"
                    >
                      Change
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <p className="text-blue-200 text-xs">
            Marking someone out removes them from {seasonYear} scoring and standings only. Their
            past picks, scores and finishes stay on record.
          </p>
        </div>
      )}
    </div>
  );
};

export default SeasonCheckIn;
