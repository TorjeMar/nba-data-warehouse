// Basketball warehouse document model for MongoDB.
// Grain: one player stat line for one game and one team.
//
// Suggested collections:
// - player_game_stats: fact-like collection for analytics
// - teams: optional reference collection
// - players: optional reference collection
// - games: optional reference collection
// - calendar: optional reference collection

db.createCollection("player_game_stats", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["sourceGameId", "team", "player", "stats"],
      properties: {
        sourceGameId: {
          bsonType: "string",
          description: "Source game identifier"
        },
        gameType: {
          bsonType: ["string", "null"]
        },
        seasonLabel: {
          bsonType: ["string", "null"]
        },
        gameDate: {
          bsonType: ["date", "null"]
        },
        team: {
          bsonType: "object",
          required: ["sourceTeamId", "teamName", "teamTricode"],
          properties: {
            sourceTeamId: { bsonType: ["long", "int", "string"] },
            teamName: { bsonType: "string" },
            teamCity: { bsonType: "string" },
            teamTricode: { bsonType: "string" },
            teamSlug: { bsonType: "string" }
          }
        },
        player: {
          bsonType: "object",
          required: ["sourcePersonId", "displayName"],
          properties: {
            sourcePersonId: { bsonType: ["long", "int", "string"] },
            firstName: { bsonType: "string" },
            familyName: { bsonType: "string" },
            displayName: { bsonType: "string" },
            nameInitial: { bsonType: ["string", "null"] },
            playerSlug: { bsonType: ["string", "null"] },
            jerseyNumber: { bsonType: ["string", "null"] },
            position: { bsonType: ["string", "null"] }
          }
        },
        stats: {
          bsonType: "object",
          required: [
            "minutesPlayedSeconds",
            "fieldGoalsMade",
            "fieldGoalsAttempted",
            "threePointersMade",
            "threePointersAttempted",
            "freeThrowsMade",
            "freeThrowsAttempted",
            "reboundsOffensive",
            "reboundsDefensive",
            "reboundsTotal",
            "assists",
            "steals",
            "blocks",
            "turnovers",
            "foulsPersonal",
            "points",
            "plusMinusPoints"
          ],
          properties: {
            minutesPlayedSeconds: { bsonType: ["int", "long"] },
            fieldGoalsMade: { bsonType: ["int", "long"] },
            fieldGoalsAttempted: { bsonType: ["int", "long"] },
            fieldGoalsPercentage: { bsonType: ["double", "decimal", "null"] },
            threePointersMade: { bsonType: ["int", "long"] },
            threePointersAttempted: { bsonType: ["int", "long"] },
            threePointersPercentage: { bsonType: ["double", "decimal", "null"] },
            freeThrowsMade: { bsonType: ["int", "long"] },
            freeThrowsAttempted: { bsonType: ["int", "long"] },
            freeThrowsPercentage: { bsonType: ["double", "decimal", "null"] },
            reboundsOffensive: { bsonType: ["int", "long"] },
            reboundsDefensive: { bsonType: ["int", "long"] },
            reboundsTotal: { bsonType: ["int", "long"] },
            assists: { bsonType: ["int", "long"] },
            steals: { bsonType: ["int", "long"] },
            blocks: { bsonType: ["int", "long"] },
            turnovers: { bsonType: ["int", "long"] },
            foulsPersonal: { bsonType: ["int", "long"] },
            points: { bsonType: ["int", "long"] },
            plusMinusPoints: { bsonType: ["int", "long", "double"] }
          }
        },
        playerStatusComment: {
          bsonType: ["string", "null"]
        },
        sourceRowHash: {
          bsonType: ["string", "null"]
        },
        createdAt: {
          bsonType: ["date", "null"]
        },
        updatedAt: {
          bsonType: ["date", "null"]
        }
      }
    }
  }
});

db.createCollection("teams");
db.createCollection("players");
db.createCollection("games");
db.createCollection("calendar");
