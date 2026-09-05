import { useEffect, useState } from "react";
import { fetchPlayersByPosition } from "../services/api";
import PlayerCard from "./PlayerCard";

const PlayerList = ({ position }) => {
  const [players, setPlayers] = useState([]);

  useEffect(() => {
    fetchPlayersByPosition(position).then(setPlayers);
  }, [position]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.isArray(players) && players.map((p) => (
      <PlayerCard key={`${p.player_id}-${p.team_id}`} player={p} />
    ))}
    </div>
  );
};

export default PlayerList;
