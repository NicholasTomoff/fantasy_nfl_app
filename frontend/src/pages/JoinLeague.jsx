import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useContext, useState } from "react";
import UserContext from "../context/UserContext";
import { apiFetch } from "@/services/api";

export default function JoinLeague() {
    const { token: inviteToken } = useParams(); // from the URL
    const { user } = useContext(UserContext);
    const navigate = useNavigate();

    const [message, setMessage] = useState("Processing league invite...");
    const [error, setError] = useState(null);

    useEffect(() => {
        // Get token from param or from localStorage pending invite token
        const tokenToUse = inviteToken || localStorage.getItem("pending_invite_token");
        if (!tokenToUse) return; // no invite token anywhere, nothing to do

        const processInvite = async () => {
            if (!user) {
                // Not logged in yet, save the token if from URL (pending token)
                if (inviteToken) {
                    localStorage.setItem("pending_invite_token", inviteToken);
                }
                setMessage(null); // Clear any old message
                setError(null);
                return;
            }

            const authToken = localStorage.getItem("token");
            if (!authToken) {
                console.warn("No auth token found in localStorage");
                return;
            }

            try {
                // Optional: check if already in the league
                let inviteInfo;
                if (user.leagues && user.leagues.length > 0) {
                    const res = await apiFetch(`/api/invites/${tokenToUse}`);
                    if (!res.ok) throw new Error("Invalid invite token");
                    inviteInfo = await res.json();

                    const alreadyInLeague = user.leagues.some(
                        (l) => l.id === inviteInfo.league_id
                    );
                    if (alreadyInLeague) {
                        setMessage("You're already a member of this league. Redirecting...");
                        localStorage.removeItem("pending_invite_token");
                        setTimeout(() => {
                            navigate(`/leagues/${inviteInfo.league_id}`);
                        }, 1500);
                        return;
                    }
                }

                // Join league
                const joinRes = await apiFetch(`/api/invites/join-league/${tokenToUse}`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${authToken}` },
                });

                if (!joinRes.ok) throw new Error("Failed to join league");

                const data = await joinRes.json();
                console.log("Join league response data:", data); // Add this line

                localStorage.removeItem("pending_invite_token");

                const leagueId = data.league_id || data.id;

                if (leagueId) {
                    setMessage("Successfully joined the league! Redirecting...");
                    setActiveLeagueId(leagueId);  // <-- this line MUST be here     
                    setTimeout(() => {
                        navigate(`/leagues/${leagueId}`);
                    }, 1500);
                } else {
                    setError("Unexpected response from server.");
                }

            } catch (err) {
                console.error("Error processing invite:", err);
                setError("Invite invalid or expired.");
            }
        };

        processInvite();
    }, [inviteToken, user, navigate]);

    return (
        <div className="p-6 text-center">
            <h2 className="text-2xl font-bold mb-4">Join League</h2>
            {error ? (
                <p className="text-red-500">{error}</p>
            ) : message ? (
                <p className="text-red-500">{message}</p> // make message red too
            ) : (
                !user && <p className="text-red-500">Please log in or sign up to continue.</p>
            )}
        </div>
    );
}
