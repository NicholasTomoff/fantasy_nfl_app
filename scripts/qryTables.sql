select game_id from player_game_stats group by game_id

select * from player_game_stats where player_id=449

SELECT id, COUNT(*) FROM nfl_games GROUP BY id HAVING COUNT(*) > 1;


select * from player_game_stats where game_id=13442

create table player_game_stats as select * from  player_game_stats_backup


select * from player_game_stats_backup order by game_id, player_id

