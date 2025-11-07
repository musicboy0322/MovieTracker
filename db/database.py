# db/database.py
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_name: str = "movie_tracker_bot.db"):
        self.db_path = Path(__file__).resolve().parent / db_name
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        c = self.conn.cursor()
        # user table
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            region TEXT,
            created_at TEXT
        )
        """)
        # user tracking table
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_movies (
            chat_id INTEGER,
            movie_id INTEGER,
            title TEXT,
            release_date TEXT,
            genres TEXT,
            poster TEXT,
            added_at TEXT,
            PRIMARY KEY (chat_id, movie_id),
            FOREIGN KEY (chat_id) REFERENCES users(chat_id)
        )
        """)
        self.conn.commit()

    # user table logic
    def add_user(self, chat_id: int, region: str):
        c = self.conn.cursor()
        c.execute("""
        INSERT INTO users (chat_id, region, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET region=excluded.region
        """, (chat_id, region, datetime.now().isoformat()))
        self.conn.commit()

    def get_user_region(self, chat_id: int) -> Optional[str]:
        c = self.conn.cursor()
        c.execute("SELECT region FROM users WHERE chat_id=?", (chat_id,))
        row = c.fetchone()
        return row["region"] if row else None

    # user tracking table logic
    def add_tracked_movie(self, chat_id: int, movie_id: int, title: str, release_date: str, genres: str, poster: str):
        c = self.conn.cursor()
        c.execute("""
        INSERT OR IGNORE INTO user_movies (chat_id, movie_id, title, release_date, genres, poster, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, movie_id, title, release_date, genres, poster, datetime.now().isoformat()))
        self.conn.commit()

    def remove_tracked_movie(self, chat_id: int, movie_id: int):
        c = self.conn.cursor()
        c.execute("DELETE FROM user_movies WHERE chat_id=? AND movie_id=?", (chat_id, movie_id))
        self.conn.commit()

    def get_user_tracked_movies(self, chat_id: int) -> List[sqlite3.Row]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM user_movies WHERE chat_id=?", (chat_id,))
        return c.fetchall()

    def get_all_user_movies(self) -> dict[int, list[sqlite3.Row]]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM user_movies ORDER BY chat_id")
        rows = c.fetchall()
        
        user_movies = {}
        for r in rows:
            chat_id = r["chat_id"]
            if chat_id not in user_movies:
                user_movies[chat_id] = []
            user_movies[chat_id].append(r)
        return user_movies

    def close(self):
        self.conn.close()