SELECT 
    s.player_id,
    s.team_id        AS gamestats_team_id,
    p.team_id        AS player_team_id,
    p.player_name,
    g.season,
    g.week,
    g.date           AS game_date,
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
    p.id             AS player_table_pk
FROM player_game_stats s
LEFT JOIN players p
    ON s.player_id = p.player_id
JOIN nfl_games g
    ON s.game_id = g.id
WHERE g.season = 2025
  AND s.position IN ('QB','RB','WR')
  AND (
        p.id IS NULL 
        OR NOT EXISTS (
            SELECT 1 
            FROM players p2 
            WHERE p2.player_id = s.player_id 
              AND p2.team_id = s.team_id 
              AND p2.active = true
        )
      )
ORDER BY g.season DESC, g.date DESC;
