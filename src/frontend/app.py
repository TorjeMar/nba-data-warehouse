"""Umbrella frontend for the Basketball Data Warehouse."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from flask import Flask, render_template, abort

# Ensure project root is on the path so we can import src.clients
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

app = Flask(__name__)

VALID_DBS = {"mysql", "mongodb", "neo4j"}


# ---------------------------------------------------------------------------
# Query functions — fill in your own queries here
# ---------------------------------------------------------------------------

def mysql_team_query():
    """Return (columns, rows) for MySQL team statistics."""
    from src.clients.mysql_client import connect_mysql

    conn = connect_mysql()
    cursor = conn.cursor()

    # TODO: write your MySQL team query here
    # Example:
    # cursor.execute("SELECT ... FROM ... WHERE ...")
    # columns = [desc[0] for desc in cursor.description]
    # rows = cursor.fetchall()

    columns, rows = [], []

    cursor.close()
    conn.close()
    return columns, rows


def mysql_year_query():
    """Return (columns, rows) for MySQL year statistics."""
    from src.clients.mysql_client import connect_mysql

    conn = connect_mysql()
    cursor = conn.cursor()

    # TODO: write your MySQL year query here

    columns, rows = [], []

    cursor.close()
    conn.close()
    return columns, rows


def mongodb_team_query():
    """Return (columns, rows) for MongoDB team statistics."""
    from src.clients.mongodb_client import connect_mongodb

    db = connect_mongodb()

    # TODO: write your MongoDB team aggregation pipeline here
    # Example:
    # pipeline = [ {"$group": {...}}, {"$sort": {...}} ]
    # results = list(db.player_game_stats.aggregate(pipeline))
    # columns = [...]
    # rows = [[doc[c] for c in columns] for doc in results]

    columns, rows = [], []

    return columns, rows


def mongodb_year_query():
    """Return (columns, rows) for MongoDB year statistics."""
    from src.clients.mongodb_client import connect_mongodb

    db = connect_mongodb()

    # TODO: write your MongoDB year aggregation pipeline here

    columns, rows = [], []

    return columns, rows


def neo4j_team_query():
    """Return (columns, rows) for Neo4j team statistics."""
    from src.clients.neo4j_client import connect_neo4j

    driver = connect_neo4j()

    # TODO: write your Neo4j team Cypher query here
    # Example:
    # with driver.session() as session:
    #     result = session.run("MATCH ... RETURN ...")
    #     columns = result.keys()
    #     rows = [record.values() for record in result]

    columns, rows = [], []

    driver.close()
    return columns, rows


def neo4j_year_query():
    """Return (columns, rows) for Neo4j year statistics."""
    from src.clients.neo4j_client import connect_neo4j

    driver = connect_neo4j()

    # TODO: write your Neo4j year Cypher query here

    columns, rows = [], []

    driver.close()
    return columns, rows


# Dispatch table mapping (db, category) -> query function
QUERY_DISPATCH = {
    ("mysql", "team"): mysql_team_query,
    ("mysql", "year"): mysql_year_query,
    ("mongodb", "team"): mongodb_team_query,
    ("mongodb", "year"): mongodb_year_query,
    ("neo4j", "team"): neo4j_team_query,
    ("neo4j", "year"): neo4j_year_query,
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<db>")
def database(db):
    if db not in VALID_DBS:
        abort(404)
    return render_template("database.html", db=db)


@app.route("/<db>/team")
def team(db):
    if db not in VALID_DBS:
        abort(404)
    query_fn = QUERY_DISPATCH[(db, "team")]
    columns, rows = query_fn()
    return render_template("team.html", db=db, columns=columns, rows=rows)


@app.route("/<db>/year")
def year(db):
    if db not in VALID_DBS:
        abort(404)
    query_fn = QUERY_DISPATCH[(db, "year")]
    columns, rows = query_fn()
    return render_template("year.html", db=db, columns=columns, rows=rows)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
