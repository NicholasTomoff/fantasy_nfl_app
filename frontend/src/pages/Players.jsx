import React, { useEffect, useState } from "react";
import axios from "axios";
import { apiFetch } from "@/services/api";

const positions = ["QB", "RB", "WR"];

const Players = () => {
  const [players, setPlayers] = useState([]);
  const [position, setPosition] = useState("QB");

  useEffect(() => {
    apiFetch(`/api/players/${position}`)
      .then(res => setPlayers(res.data.players))
      .catch(err => console.error(err));
  }, [position]);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">NFL Players - {position}</h1>

      <div className="flex space-x-4 mb-6">
        {positions.map(pos => (
          <button
            key={pos}
            onClick={() => setPosition(pos)}
            className={`px-4 py-2 rounded-lg ${position === pos ? "bg-blue-500 text-white" : "bg-gray-200"}`}
          >
            {pos}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {players.map(player => (
          <div key={player.player_id} className="p-4 bg-white shadow rounded-lg">
            <h2 className="text-xl font-semibold">{player.player_name}</h2>
            <p className="text-gray-600">{player.position}</p>
            <p className="text-sm text-gray-500">{player.team_name}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Players;
