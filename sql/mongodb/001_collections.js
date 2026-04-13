db.createCollection("raw_game_dates", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "GAME_ID", 
        "GAME_DATE", 
        "TEAM_ID",
        "TEAM_ABBREVIATION",
        "MATCHUP",
        "SEASON_TYPE",
        "SEASON_LABEL"
      ],
      properties: {
        GAME_ID: { bsonType: "string" },
        GAME_DATE: { bsonType: "string" },
        TEAM_ID: { bsonType: "long" },
        TEAM_ABBREVIATION: { bsonType: "string" },
        MATCHUP: { bsonType: "string" },
        SEASON_TYPE: { bsonType: "string" },
        SEASON_LABEL: { bsonType: "string" },
      }
    }
  }
});

db.createCollection("raw_box_scores", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "gameId",
        "teamId",
        "teamCity",
        "teamName",
        "teamTricode",
        "teamSlug",
        "personId",
        "firstName",
        "familyName",
        "nameI",
        "playerSlug",
        "position",
        "comment",
        "jerseyNum",
        "minutes",
        "fieldGoalsMade",
        "fieldGoalsAttempted",
        "fieldGoalsPercentage",
        "threePointersMade",
        "threePointersAttempted",
        "threePointersPercentage",
        "freeThrowsMade",
        "freeThrowsPercentage",
        "freeThrowsAttempted",
        "reboundsDefensive",
        "reboundsOffensive",
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
        gameId: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        teamId: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        teamCity: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        teamName: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        teamTricode: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        teamSlug: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        personId: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        firstName: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        familyName: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        nameI: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        playerSlug: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        position: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        comment: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        jerseyNum: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        minutes: {
          bsonType: "object",
          additionalProperties: { bsonType: "string" }
        },
        fieldGoalsMade: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        fieldGoalsAttempted: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        fieldGoalsPercentage: {
          bsonType: "object",
          additionalProperties: { bsonType: "double" }
        },
        threePointersMade: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        threePointersAttempted: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        threePointersPercentage: {
          bsonType: "object",
          additionalProperties: { bsonType: "double" }
        },
        freeThrowsMade: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        freeThrowsAttempted: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        freeThrowsPercentage: {
          bsonType: "object",
          additionalProperties: { bsonType: "double" }
        },
        reboundsOffensive: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        reboundsDefensive: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        reboundsTotal: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        assists: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        steals: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        blocks: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        turnovers: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        foulsPersonal: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        points: {
          bsonType: "object",
          additionalProperties: { bsonType: ["double", "int", "long"] }
        },
        plusMinusPoints: {
          bsonType: "object",
          additionalProperties: { bsonType: "double" }
        }
      }
    }
  }
});

