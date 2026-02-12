import sqlite3
from pathlib import Path
from typing import Any, Tuple, List, Dict, Optional

DB_PATH: Optional[str] = None

def set_db_path(db_path: str):
    global DB_PATH
    DB_PATH = str(Path(db_path).resolve())

# def connect() -> sqlite3.Cursor:
#     global DB_PATH
#     conn = sqlite3.connect(DB_PATH)
#     return conn, conn.cursor()

# def close(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
#     conn.close()
#     cursor.close()
#     return None

def _get_table_columns(cursor: sqlite3.Cursor, table: str = "EVENTS") -> List[str]:
    cursor.execute(f"PRAGMA table_info({table});")
    return [row[1] for row in cursor.fetchall()]

def check_JobAllocation(cursor: sqlite3.Cursor, n: int = 5) -> Dict[str, Any]:
    cursor.execute("""
        SELECT *
        FROM EVENTS
        WHERE EVENT = 'JobAllocation'
        ORDER BY RANDOM()
        LIMIT ?;
    """, (n,))
    rows = cursor.fetchall()

    return {
        "Field": "JobAllocation",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": rows,
    }

def check_FileTransfer(cursor: sqlite3.Cursor, n: int = 5) -> Dict[str, Any]:
    cursor.execute("""
        SELECT *
        FROM EVENTS
        WHERE EVENT = 'FileTransfer'
        ORDER BY RANDOM()
        LIMIT ?;
    """, (n,))
    rows = cursor.fetchall()
    
    return {
        "Field": "FileTransfer",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": rows,
    }

def check_FileRead(cursor: sqlite3.Cursor, n: int = 5) -> Dict[str, Any]:
    cursor.execute("""
        SELECT *
        FROM EVENTS
        WHERE EVENT = 'FileRead'
        ORDER BY RANDOM()
        LIMIT ?;
    """, (n,))
    rows = cursor.fetchall()

    return {
        "Field": "FileRead",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": rows,
    }

def check_FileWrite(cursor: sqlite3.Cursor, n: int = 5) -> Dict[str, Any]:
    cursor.execute("""
        SELECT *
        FROM EVENTS
        WHERE EVENT = 'FileWrite'
        ORDER BY RANDOM()
        LIMIT ?;
    """, (n,))
    rows = cursor.fetchall()

    return {
        "Field": "FileWrite",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": rows,
    }

def check_JobExecution(cursor: sqlite3.Cursor, n: int = 5) -> Dict[str, Any]:
    cursor.execute("""
        SELECT *
        FROM EVENTS
        WHERE EVENT = 'JobExecution'
        ORDER BY RANDOM()
        LIMIT ?;
    """, (n,))
    rows = cursor.fetchall()

    return {
        "Field": "JobExecution",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": rows,
    }

def check_All(cursor: sqlite3.Cursor, n: int = 5) -> List[Dict[str, Any]]:
    res = []
    res.append(check_FileRead(cursor, n))
    res.append(check_FileTransfer(cursor, n))
    res.append(check_FileWrite(cursor, n))
    res.append(check_JobAllocation(cursor, n))
    res.append(check_JobExecution(cursor, n))
    return res

def execute_sql(cursor: sqlite3.Cursor, sql: str) -> List[Tuple[Any, ...]]:
    cursor.execute(sql)
    return cursor.fetchall()
