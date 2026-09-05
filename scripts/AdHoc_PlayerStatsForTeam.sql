SELECT 
    s.player_id,
	p.team_id as playerTeamID,
    s.team_id,
    p.player_name,
    p.position           AS player_position,
    g.season,
    g.week,
    g.date               AS game_date,
    g.home_team,
    g.away_team,
    s.passing_yards,
    s.passing_tds,
    s.rushing_yards,
    s.rushing_tds,
    s.receiving_yards,
    s.receiving_tds,
    s.receptions
FROM player_game_stats s
LEFT JOIN players p
    ON s.player_id = p.player_id
  -- AND s.team_id   = p.team_id
JOIN nfl_games g
    ON s.game_id = g.id
WHERE g.season = 2025
  AND s.team_id = 31   -- <-- replace with the team_id you want
    AND p.position IN ('QB','RB','WR')

ORDER BY g.week ASC, g.date ASC;
