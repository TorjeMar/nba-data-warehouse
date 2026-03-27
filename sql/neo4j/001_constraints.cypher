// Core constraints and indexes for the basketball warehouse graph.

CREATE CONSTRAINT team_source_id_unique IF NOT EXISTS
FOR (t:Team)
REQUIRE t.sourceTeamId IS UNIQUE;

CREATE CONSTRAINT player_source_id_unique IF NOT EXISTS
FOR (p:Player)
REQUIRE p.sourcePersonId IS UNIQUE;

CREATE CONSTRAINT game_source_id_unique IF NOT EXISTS
FOR (g:Game)
REQUIRE g.sourceGameId IS UNIQUE;

CREATE CONSTRAINT date_key_unique IF NOT EXISTS
FOR (d:Date)
REQUIRE d.dateKey IS UNIQUE;

CREATE CONSTRAINT position_code_unique IF NOT EXISTS
FOR (p:Position)
REQUIRE p.positionCode IS UNIQUE;

CREATE INDEX game_season_label IF NOT EXISTS
FOR (g:Game)
ON (g.seasonLabel);

CREATE INDEX date_full_date IF NOT EXISTS
FOR (d:Date)
ON (d.fullDate);
