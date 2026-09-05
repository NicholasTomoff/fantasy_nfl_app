-- Reset all primary key sequences to max(id) + 1 or 1 if empty
DO $$
DECLARE
    tbl TEXT;
    seq TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'users', 'leagues', 'league_members', 'league_invite_tokens',
        'players', 'teams', 'nfl_games', 'player_game_stats',
        'weekly_scores', 'picks', 'position_streaks', 'all_position_streaks'
    ]
    LOOP
        seq := tbl || '_id_seq';
        EXECUTE format('
            SELECT setval(pg_get_serial_sequence(%L, %L),
            COALESCE((SELECT MAX(id)+1 FROM %I), 1), false)',
            tbl, 'id', tbl);
    END LOOP;
END$$;
