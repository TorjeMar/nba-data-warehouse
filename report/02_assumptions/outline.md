# Assumptions

Document all assumptions that shape the warehouse design, ETL, and report.

## Notes Seeded From Current Work

- The warehouse grain is one player stat line for one game and one team.
- The current source file does not contain reliable game date, season label, matchup label, or home/away indicators.
- Those missing attributes are modeled in the schemas but remain nullable until enriched.
- The same business grain should be preserved across MySQL, MongoDB, and Neo4j for fair comparison.
- The source dataset is treated as historical basketball box score data.
