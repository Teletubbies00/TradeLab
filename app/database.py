import os
import sqlite3
from pathlib import Path


DB_PATH = Path(
    os.environ.get("TRADELAB_DB_PATH", "data/tradelab.db")
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL
                    CHECK (side IN ('LONG', 'SHORT')),
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                net_pnl REAL NOT NULL,
                notes TEXT DEFAULT ''
            )
        """)

    print(f"資料庫初始化成功：{DB_PATH}")


if __name__ == "__main__":
    initialize_database()
