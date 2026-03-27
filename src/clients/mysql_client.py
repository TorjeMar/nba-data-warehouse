"""MySQL connection helpers."""

from __future__ import annotations

import os

import mysql.connector
from mysql.connector import MySQLConnection


def connect_mysql() -> MySQLConnection:
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "mydatabase"),
    )
