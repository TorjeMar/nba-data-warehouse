1. uv run -m _v2.normalizers.boxscores.boxscores
1. uv run -m _v2.processors.dimensions.team
2. uv run -m _v2.processors.dimensions.game
3. uv run -m _v2.processors.dimensions.tricode_mapping
4. uv run -m _v2.processors.dimensions.prospects
5. uv run -m _v2.processors.dimensions.draft_summary

## The Processing Pipeline

### Step 1 : Initializing the Team Dimension
Step 1 uses the leauge hiearchy to initiatialze the team dimension, by simply extracting and casting datatypes, and replacing empty strings with NULL values

The leauge hiearchy consist of two conferences, each conference contains 3 divisions, and each division contains 5 teams, yielding a total of 30 NBA teams, a detailed DDL statement of this table can be found under the appendix

In our data warehouse, the leauge hiearchy serves as the ground truth for the answering question of which teams belong to the NBA and which teams are only involved for shorter tournamenets, practice games etc, which is typically common during the pre-season for instance.

### Step 2 : Initializing the Game Dimension
Step 2 uses a dataset consisting of game dates, team ids, game ids, and additional information. This table acts as the relationship table, connecting two teams, and from this table we can answer which teams has played against each other, on which dates and on which arenas.

The preparing of this data involved converting certain string values to key value pairs for easier query, injecting additional metadata, casting types and replacing empty strings with NULL values

### Step 3 : Initializing the Tricode Mapping
Step 3 takes as input the Team and Game dimension, where the Team dimension defines the regular NBA teams, and the Game dimension contains all matchups across all seasons for the period between 2000 and 2025. 

The mapping is done by first collecting a tuple, of the form (team_id, tricode, game_date), where a tricode is a 3-letter abbrevation, such as LAL for LA Lakers. The next step is to group the collection of tuples by team_id, and perform a few operations
the first operation is to select the tricode with the most recent game_date as the current tricode for that particular team, 
and the second operation is collect all associated tricodes for a particular team 
we know have the latest recorded tricode per team, and a collection of various, historical, tricodes per team, 

we then perform some additional operations on the same collection to extract some descriptive metadata per tricode such as first_seen, last_seen, etc, and perfrom operations to flatten the structure into regular table, the result of the process is a tricode_current map and a tricode_history map, lastly we use the Team Dimension and the team_id's which it contains, to stamp a entry in the newly created mapping tables as belonging to an NBA team or not.


