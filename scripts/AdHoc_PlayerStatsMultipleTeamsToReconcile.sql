SELECT 
    s.player_id,
	p.team_id				   AS player_team_id,
    s.team_id                  AS gamestats_team_id,
    p.player_name,
    g.season,
    g.week,
    g.date                     AS game_date,
    g.home_team,
    g.away_team,
    s.position,
    s.passing_yards,
    s.passing_tds,
    s.rushing_yards,
    s.rushing_tds,
    s.receiving_yards,
    s.receiving_tds,
    s.receptions,
    p.id                       AS player_table_pk,
    p.team_id                  AS players_table_team_id
FROM player_game_stats s
LEFT JOIN players p
    ON s.player_id = p.player_id
JOIN nfl_games g
    ON s.game_id = g.id
WHERE g.season = 2025
  AND s.position IN ('QB','RB','WR')
  AND (p.id IS NULL OR p.team_id IS DISTINCT FROM s.team_id)
ORDER BY g.season DESC, g.date DESC;


select * from player_game_stats where player_id = 2005
