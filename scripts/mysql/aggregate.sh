#!/bin/bash
set -e
source .env

: "${DB_NAME:?DB_NAME is not set}"

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;"

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  "$DB_NAME" \
  < ./sql/mysql/004_populate_agg_player_season_totals.sql

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  "$DB_NAME" \
  < ./sql/mysql/003_populate_agg_team_game_totals.sql
