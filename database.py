import json
import sqlite3
from datetime import datetime

from config import DATABASE_PATH, EFFORT_UNIT


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                input_json TEXT NOT NULL,
                summary TEXT NOT NULL,
                effort REAL NOT NULL,
                unit TEXT NOT NULL
            )
            """
        )


def save_prediction(cleaned: dict, summary_rows: list[dict], effort: float) -> int:
    created_at = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    short_summary = _short_summary(cleaned)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO predictions (created_at, input_json, summary, effort, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                created_at,
                json.dumps({"input": cleaned, "rows": summary_rows}, ensure_ascii=False),
                short_summary,
                effort,
                EFFORT_UNIT,
            ),
        )
        return int(cursor.lastrowid)


def list_predictions() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, created_at, summary, effort, unit FROM predictions ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_prediction(prediction_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM predictions WHERE id = ?",
            (prediction_id,),
        ).fetchone()
    if row is None:
        return None
    payload = json.loads(row["input_json"])
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "summary": row["summary"],
        "effort": row["effort"],
        "unit": row["unit"],
        "input": payload["input"],
        "rows": payload["rows"],
    }


def delete_prediction(prediction_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM predictions WHERE id = ?",
            (prediction_id,),
        )
        return cursor.rowcount > 0


def delete_all_predictions() -> int:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM predictions")
        return cursor.rowcount


def _short_summary(cleaned: dict) -> str:
    year = cleaned.get("year")
    year_text = str(int(year)) if isinstance(year, float) and year.is_integer() else str(year)
    size = cleaned.get("equivphyskloc")
    return (
        f"{cleaned.get('cat2')} · {cleaned.get('mode')} · "
        f"{size} KLOC · tahun {year_text}"
    )
