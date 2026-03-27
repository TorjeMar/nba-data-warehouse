# Data Description

Describe the data maintained by the system.

## Notes Seeded From Current Work

- Main source file: `data/box_scores.jsonl`
- Example source payload: `data.example/entry.json`
- Field list: `notes/data.md`
- Source structure: one line per game payload, with player rows encoded as indexed columns
- Main entities visible in the source:
  - games
  - teams
  - players
  - player performance statistics

Core measures already identified:
- points
- assists
- rebounds
- steals
- blocks
- turnovers
- field goal stats
- three-point stats
- free-throw stats
- plus/minus
- minutes played
