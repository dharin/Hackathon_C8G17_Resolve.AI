import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config.settings import ANALYSES_DB_PATH
from models.upload_analysis import UploadAnalysisResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    result_json TEXT NOT NULL
);
"""


@contextmanager
def _connect():
    path: Path = ANALYSES_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_analysis(result: UploadAnalysisResult) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO analyses (analysis_id, result_json) VALUES (?, ?)",
            (result.analysis_id, result.model_dump_json()),
        )


def load_analysis(analysis_id: str) -> UploadAnalysisResult | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
    if row is None:
        return None
    return UploadAnalysisResult.model_validate_json(row[0])
