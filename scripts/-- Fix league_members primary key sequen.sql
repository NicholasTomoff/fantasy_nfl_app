-- Fix league_members primary key sequence
SELECT setval('league_members_id_seq', COALESCE((SELECT MAX(id) FROM league_members), 1), true);

-- Fix users primary key sequence
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);

-- Fix leagues primary key sequence
SELECT setval('leagues_id_seq', COALESCE((SELECT MAX(id) FROM leagues), 1), true);

-- Fix league_invite_tokens primary key sequence
SELECT setval('league_invite_tokens_id_seq', COALESCE((SELECT MAX(id) FROM league_invite_tokens), 1), true);
