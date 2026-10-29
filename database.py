import os
import sqlite3
from contextlib import contextmanager

DEFAULT_DB = os.path.join(os.path.dirname(__file__), "music_manager.db")
DATABASE_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB)

@contextmanager
def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                genre TEXT NOT NULL DEFAULT 'Other',
                duration TEXT NOT NULL DEFAULT '3:30',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (playlist_id, song_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
            );
        """)
        count = db.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        if count == 0:
            samples = [
                ("Blinding Lights", "The Weeknd", "Pop", "3:20"),
                ("Levitating", "Dua Lipa", "Pop", "3:23"),
                ("Starboy", "The Weeknd", "R&B", "3:50"),
                ("Heat Waves", "Glass Animals", "Indie", "3:58"),
                ("Night Changes", "One Direction", "Pop", "3:46"),
                ("Sunflower", "Post Malone, Swae Lee", "Hip-Hop", "2:38"),
                ("Perfect", "Ed Sheeran", "Acoustic", "4:23"),
                ("Do I Wanna Know?", "Arctic Monkeys", "Alternative", "4:32"),
            ]
            db.executemany(
                "INSERT INTO songs (title, artist, genre, duration) VALUES (?, ?, ?, ?)",
                samples
            )
        playlist_count = db.execute("SELECT COUNT(*) FROM playlists").fetchone()[0]
        if playlist_count == 0:
            db.execute(
                "INSERT INTO playlists (name, description) VALUES (?, ?)",
                ("Late Night Vibes", "Songs for the after-hours.")
            )
            playlist_id = db.execute("SELECT id FROM playlists WHERE name = ?", ("Late Night Vibes",)).fetchone()[0]
            song_ids = db.execute("SELECT id FROM songs ORDER BY id LIMIT 4").fetchall()
            db.executemany(
                "INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                [(playlist_id, row["id"]) for row in song_ids]
            )
