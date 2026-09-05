SELECT p.*, t.name AS team_name
FROM players p
JOIN teams t ON p.team_id = t.id
WHERE p.player_name IN (
    SELECT player_name
    FROM public.players
    GROUP BY player_name, active
    HAVING COUNT(*) > 1
)
AND p.position IN ('QB', 'RB', 'WR')
and active = true
ORDER BY p.player_name;


update players set active = false where player_name in (
	select player_name from players where active = true 
	and team_name is not null
)
and team_name is null


select * from players where player_name = 'Davante Adams'

select * from players where player_name = 'Lamar Jackson'

update players set active = true, team_name = 'Baltimore Ravens' where player_name = 'Lamar Jackson' and team_id = 5



SELECT p.*, t.name AS team_name
FROM players p
JOIN teams t ON p.team_id = t.id
WHERE p.player_name IN (
    SELECT player_name
    FROM players
    GROUP BY player_name
    HAVING COUNT(DISTINCT player_id) > 1
)
ORDER BY p.player_name;


