const PlayerCard = ({ player }) => {
  if (!player) return null;

  // Prefer nested team.name if exists, else fallback to team_name string.
  const teamName = player.team?.name || player.team_name || "N/A";

  return (
    <div className="border p-4 rounded-lg shadow-md bg-gray-800 text-white">
      <h2 className="text-lg font-semibold truncate">{player.player_name}</h2>
      <p className="text-sm text-yellow-400">{player.position}</p>
      <p className="text-sm text-gray-300">
        Team: {player.team?.name || "N/A"}
      </p>
    </div>
  );
};

export default PlayerCard;
