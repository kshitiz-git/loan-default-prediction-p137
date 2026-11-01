"""Prediction log in SQLite: one row per scored application (inputs, score, decision, time)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
import pandas as pd
from src.config import LOG_DB

DB_PATH = LOG_DB                              # tests point this at a temporary file

SCHEMA = {
    "application_id": "TEXT PRIMARY KEY", "created_at": "TEXT NOT NULL", "model_version": "TEXT NOT NULL",
    "person_age": "INTEGER", "person_income": "REAL", "person_home_ownership": "TEXT",
    "person_emp_length": "REAL", "loan_intent": "TEXT", "loan_grade": "TEXT", "loan_amnt": "REAL",
    "loan_int_rate": "REAL", "loan_percent_income": "REAL", "cb_person_default_on_file": "TEXT",
    "cb_person_cred_hist_length": "INTEGER",
    "pd": "REAL NOT NULL", "decision": "TEXT NOT NULL", "latency_ms": "REAL",
}
COLUMNS = list(SCHEMA)


@contextmanager
def _connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        with con:                 # commits on success, rolls back on error
            yield con
    finally:
        con.close()               # sqlite3's own "with" does NOT close; an open handle locks the file on Windows


def init_db() -> None:
    columns = ", ".join(f"{name} {kind}" for name, kind in SCHEMA.items())
    with _connection() as con:
        con.execute(f"CREATE TABLE IF NOT EXISTS predictions ({columns})")
        con.execute("CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions (created_at)")


def log_prediction(row: dict) -> None:
    row = {**row, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with _connection() as con:
        con.execute(f"INSERT INTO predictions ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
                    [row[c] for c in COLUMNS])


def recent(n: int = 500) -> pd.DataFrame:
    with _connection() as con:
        return pd.read_sql_query("SELECT * FROM predictions ORDER BY created_at DESC, rowid DESC LIMIT ?",
                                 con, params=(n,))
