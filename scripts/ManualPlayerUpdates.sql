
select * from players where player_name = 'Davante Adams'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (10, 'Davante Adams', 'WR', 31, NULL, true);
update players set active = false where player_id = 10 and team_id <> 31

/**************************************************************************************/

select * from players where player_name = 'Adam Thielen'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (2325, 'Adam Thielen', 'WR', 32, NULL, true);
update players set active = false where player_id = 2325 and team_id <> 32

/**************************************************************************************/

select * from players where player_name = 'DeAndre Hopkins'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (766, 'DeAndre Hopkins', 'WR', 5, NULL, true);
update players set active = false where player_id = 766 and team_id <> 5


/**************************************************************************************/

select * from players where player_name = 'Cooper Kupp'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (2239, 'Cooper Kupp', 'WR', 23, NULL, true);
update players set active = false where player_id = 2239 and team_id <> 23

/**************************************************************************************/

select * from players where player_name = 'Brian Robinson Jr.'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1265, 'Brian Robinson Jr.', 'WR', 14, NULL, true);
update players set active = false where player_id = 1265 and team_id <> 14
update players set position = 'RB' where id = 3831
/**************************************************************************************/

select * from players where player_name = 'Skyy Moore'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1207, 'Skyy Moore', 'WR', 14, NULL, true);
update players set active = false where player_id = 1207 and team_id <> 14

/**************************************************************************************/

select * from players where player_name = 'Josh Reynolds'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (463, 'Josh Reynolds', 'WR', 13, NULL, true);
update players set active = false where player_id = 463 and team_id <> 13

/**************************************************************************************/

select * from players where player_name = 'Joe Flacco'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (902, 'Joe Flacco', 'QB', 9, NULL, true);
update players set active = false where player_id = 902 and team_id <> 9

/**************************************************************************************/

select * from players where player_name = 'DeAndre Carter'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (2161, 'DeAndre Carter', 'WR', 9, NULL, true);
update players set active = false where player_id = 2161 and team_id <> 9

/**************************************************************************************/

select * from players where player_name = 'Stefon Diggs'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1426, 'Stefon Diggs', 'WR', 3, NULL, true);
update players set active = false where player_id = 1426 and team_id <> 3

/**************************************************************************************/

select * from players where player_name = 'Devaughn Vele'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (15000, 'Devaughn Vele', 'WR', 27, NULL, true);
update players set active = false where player_id = 15000 and team_id <> 27

/**************************************************************************************/

select * from players where player_name = 'Aaron Rodgers'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1050, 'Aaron Rodgers', 'QB', 22, NULL, true);
update players set active = false where player_id = 1050 and team_id <> 22

/**************************************************************************************/

select * from players where player_name = 'DK Metcalf'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1645, 'DK Metcalf', 'WR', 22, NULL, true);
update players set active = false where player_id = 1645 and team_id <> 22

/**************************************************************************************/

select * from players where player_name = 'Keenan Allen'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (2159, 'Keenan Allen', 'WR', 30, NULL, true);
update players set active = false where player_id = 2159 and team_id <> 30


/**************************************************************************************/

select * from players where player_name = 'Najee Harris'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1565, 'Najee Harris', 'RB', 30, NULL, true);
update players set active = false where player_id = 1565 and team_id <> 30


/**************************************************************************************/

select * from players where player_name = 'John Metchie III'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1865, 'John Metchie III', 'WR', 12, NULL, true);
update players set active = false where player_id = 1865 and team_id <> 12

/**************************************************************************************/

select * from players where player_name = 'George Pickens'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1577, 'George Pickens', 'WR', 29, NULL, true);
update players set active = false where player_id = 1577 and team_id <> 29

/**************************************************************************************/

select * from players where player_name = 'Javonte Williams'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (2005, 'Javonte Williams', 'RB', 29, NULL, true);
update players set active = false where player_id = 2005 and team_id <> 29


/**************************************************************************************/

select * from players where player_name = 'Malik Willis'
update players set active = false where player_id = 368 and team_id <> 15

/**************************************************************************************/

select * from players where player_name = 'Mike White'
update players set active = false where player_id = 904 and team_id <> 20


/**************************************************************************************/

select * from players where player_name = 'Hassan Haskins'
update players set active = false where player_id = 372 and team_id <> 30

/**************************************************************************************/

select * from players where player_name = 'Christopher Brooks'
update players set active = false where player_id = 17539 and team_id <> 15

/**************************************************************************************/

select * from players where player_name = 'Clyde Edwards-Helaire'
update players set active = false where player_id = 1199 and team_id <> 17
update players set active = true where player_id = 1199 and team_id = 17


/**************************************************************************************/

select * from players where player_name = 'Jacob Kibodi'
update players set active = false where player_id = 22871 and team_id <> 9

/**************************************************************************************/

select * from players where player_name = 'Darrynton Evans'
update players set active = false where player_id = 1124 and team_id <> 20

/**************************************************************************************/

select * from players where player_name = 'Cody Schrader'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (11499, 'Cody Schrader', 'RB', 2, NULL, true);
update players set active = false where player_id = 11499 and team_id <> 2

/**************************************************************************************/

select * from players where player_name = 'Joshua Kelley'
update players set active = false where player_id = 2154 --and team_id <> 20

/**************************************************************************************/

select * from players where player_name = 'Marquez Valdes-Scantling'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1210, 'Marquez Valdes-Scantling', 'WR', 14, NULL, true);
update players set active = false where player_id = 1210 and team_id <> 14

/**************************************************************************************/

select * from players where player_name = 'Tim Patrick'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (1210, 'Tim Patrick', 'WR', 2, NULL, true);
update players set active = false where player_id = 2010 and team_id <> 2


/**************************************************************************************/

select * from players where player_name = 'Jahan Dotson'
update players set active = false where player_id = 1268 and team_id <> 12


/**************************************************************************************/

select * from players where player_name = 'Mike Williams'
update players set active = false where player_id = 2166 --and team_id <> 12
-- practice squad

/**************************************************************************************/

select * from players where player_name = 'Jonathan Mingo'
update players set active = false where player_id = 16964 and team_id <> 29


/**************************************************************************************/

select * from players where player_name = 'Dante Pettis'
update players set active = false where player_id = 1132 and team_id <> 27
update players set active = true where player_id = 1132 and team_id = 27


/**************************************************************************************/

select * from players where player_name = 'Jalen Reagor'
update players set active = false where player_id = 2324 and team_id <> 30


/**************************************************************************************/

select * from players where player_name = 'Dee Eskridge'
update players set active = false where player_id = 1641 and team_id <> 25


/**************************************************************************************/

select * from players where player_name = 'Allen Robinson II'
update players set active = false where player_id = 2242 --and team_id <> 25

/**************************************************************************************/

select * from players where player_name = 'Dan Chisena'
update players set active = false where player_id = 2316 --and team_id <> 25


/**************************************************************************************/

select * from players where player_name = 'Tyler Huntley'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (290, 'Tyler Huntley', 'QB', 5, NULL, true);
update players set active = false where player_id = 290 and team_id <> 5

/**************************************************************************************/
select * from players where player_id = 14625
select * from players where player_name = 'Terrance Ferguson'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (14625, 'Terrance Ferguson', 'TE', 31, NULL, true);

/**************************************************************************************/
select * from players where player_id = 16948
select * from players where player_name = 'Quinshon Judkins'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (16948, 'Quinshon Judkins', 'RB', 9, NULL, true);

/**************************************************************************************/
select * from players where player_id = 14106
select * from players where player_name = 'Isaiah Bond'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (14106, 'Isaiah Bond', 'WR', 9, NULL, true);

/**************************************************************************************/
select * from players where player_id = 19667
select * from players where player_name = 'Harold Fannin Jr.'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (19667, 'Harold Fannin Jr.', 'TE', 9, NULL, true);

/**************************************************************************************/
select * from players where player_id = 31107
select * from players where player_name = 'Cameron Skattebo'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (31107, 'Cameron Skattebo', 'RB', 4, NULL, true);

/**************************************************************************************/
select * from players where player_id = 19
select * from players where player_name = 'Darren Waller'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (19, 'Darren Waller', 'TE', 25, NULL, true);

/**************************************************************************************/
select * from players where player_name = 'Joe Flacco'
INSERT INTO players (player_id, player_name, position, team_id, team_name, active)
VALUES (902, 'Joe Flacco', 'QB', 10, NULL, true);

update players set active = false where team_id = 9 and player_id = 902


































