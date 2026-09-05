-- Option A: OR-match (either id OR name)
WITH params AS (
  SELECT
    1234::int   AS player_id,     -- set to NULL to ignore id
    'Geno Smith'::text AS player_name -- set to NULL to ignore name
),
player_filter AS (
  SELECT p.*
  FROM players p
  CROSS JOIN params
  WHERE
    (params.player_id IS NOT NULL AND p.player_id = params.player_id)
    OR
    (params.player_name IS NOT NULL AND p.player_name ILIKE '%' || params.player_name || '%')
)
SELECT
  pf.player_id,
  pf.player_name,
  pf.active,
  pf.position,
  pf.team_id,
  t.name                                   AS team_name,
  g.season,
  g.week,
  g.date                                   AS game_date,
  s.passing_yards,
  s.passing_tds,
  s.rushing_yards,
  s.rushing_tds,
  s.receiving_yards,
  s.receiving_tds,
  s.receptions
FROM player_filter pf
LEFT JOIN teams t
  ON pf.team_id = t.id
LEFT JOIN player_game_stats s
  ON pf.player_id = s.player_id
 AND pf.team_id   = s.team_id
LEFT JOIN nfl_games g
  ON s.game_id = g.id
--where 	g.season = 2025
ORDER BY pf.player_id, g.season DESC, g.date DESC ;
