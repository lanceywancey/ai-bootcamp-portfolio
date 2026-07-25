import sqlite3
from datetime import datetime

import config


def init_db():
    """Create the summaries table if it does not exist."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            summary TEXT,
            rating INTEGER,
            category TEXT,
            created_at DATETIME
        )
    """)

    conn.commit()
    conn.close()


def save_summary(filename, summary, rating, category):
    """Save a completed review analysis."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO summaries
        (filename, summary, rating, category, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            filename,
            summary,
            rating,
            category,
            datetime.now(),
        ),
    )

    conn.commit()
    conn.close()


def get_summaries_by_category(category):
    """Return saved summaries belonging to one category."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, filename, created_at
        FROM summaries
        WHERE category = ?
        ORDER BY created_at DESC
        """,
        (category,),
    )

    results = cursor.fetchall()
    conn.close()

    return results


def get_summary_by_id(summary_id):
    """Return one complete saved analysis."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT filename, summary, rating, category, created_at
        FROM summaries
        WHERE id = ?
        """,
        (summary_id,),
    )

    result = cursor.fetchone()
    conn.close()

    return result