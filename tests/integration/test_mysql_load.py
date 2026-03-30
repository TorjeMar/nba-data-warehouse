import os
import subprocess

import mysql.connector
import pytest


@pytest.mark.skipif(
    os.getenv("TEST_MYSQL_E2E") != "1",
    reason="Set TEST_MYSQL_E2E=1 to run MySQL integration tests",
)
def test_mysql_end_to_end():
    subprocess.run(
        [
            "python",
            "-m",
            "src.pipelines.load_box_scores",
            "--backend",
            "mysql",
            "--limit",
            "100",
        ],
        check=True,
    )

    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "mydatabase"),
    )

    cursor = conn.cursor()

    def count(table_name: str) -> int:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

    dim_team = count("dim_team")
    dim_player = count("dim_player")
    dim_game = count("dim_game")
    fact = count("fact_player_game_stats")

    cursor.close()
    conn.close()

    assert dim_team > 0
    assert dim_player > 0
    assert dim_game > 0
    assert fact > 0


@pytest.mark.skipif(
    os.getenv("TEST_MYSQL_E2E") != "1",
    reason="Set TEST_MYSQL_E2E=1 to run MySQL integration tests",
)
def test_mysql_idempotent_load():
    subprocess.run(
        [
            "python",
            "-m",
            "src.pipelines.load_box_scores",
            "--backend",
            "mysql",
            "--limit",
            "100",
        ],
        check=True,
    )
    subprocess.run(
        [
            "python",
            "-m",
            "src.pipelines.load_box_scores",
            "--backend",
            "mysql",
            "--limit",
            "100",
        ],
        check=True,
    )

    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "mydatabase"),
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_player_game_stats")
    fact_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    assert fact_count > 0
