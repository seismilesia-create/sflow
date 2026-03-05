import sqlite3
from config import DB_PATH


class TranscriptionDB:
    def __init__(self):
        self.db_path = str(DB_PATH)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                language TEXT,
                duration_seconds REAL,
                model TEXT DEFAULT 'whisper-large-v3-turbo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at
            ON transcriptions(created_at)
        """)
        conn.commit()
        conn.close()

    def insert(self, text: str, duration_seconds: float = 0.0, language: str = None):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO transcriptions (text, language, duration_seconds) VALUES (?, ?, ?)",
            (text, language, duration_seconds),
        )
        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM transcriptions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search(self, query: str, limit: int = 50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM transcriptions WHERE text LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count(self):
        conn = self._get_conn()
        result = conn.execute("SELECT COUNT(*) FROM transcriptions").fetchone()
        conn.close()
        return result[0]
