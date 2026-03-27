# MongoDB Warehouse Design

This design keeps a fact-like `player_game_stats` collection as the main analytical source.

Why this shape:
- it preserves the same grain as the MySQL fact table
- it embeds player, team, and stat attributes together for read-heavy analytical queries
- it still leaves room for optional reference collections when you want cleaner master-data management

Files:
- `001_document_model.js` creates the main collections and validator
- `002_indexes.js` adds unique and analytical indexes
- `003_aggregations.js` shows materialized summary pipelines
