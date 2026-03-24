import sqlite3
import json
from typing import Any, Tuple, List, Dict

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

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[6]
        if isinstance(meta, str):
            try:
                row[6] = json.loads(meta)
            except Exception:
                pass
        cleaned_rows.append(row)

    return {
        "Field": "JobAllocation",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": cleaned_rows,
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

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[6]
        if isinstance(meta, str):
            try:
                row[6] = json.loads(meta)
            except Exception:
                pass
        cleaned_rows.append(row)

    return {
        "Field": "FileTransfer",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": cleaned_rows,
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

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[6]
        if isinstance(meta, str):
            try:
                row[6] = json.loads(meta)
            except Exception:
                pass
        cleaned_rows.append(row)

    return {
        "Field": "FileRead",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": cleaned_rows,
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

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[6]
        if isinstance(meta, str):
            try:
                row[6] = json.loads(meta)
            except Exception:
                pass
        cleaned_rows.append(row)

    return {
        "Field": "FileWrite",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": cleaned_rows,
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

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[6]
        if isinstance(meta, str):
            try:
                row[6] = json.loads(meta)
            except Exception:
                pass
        cleaned_rows.append(row)

    return {
        "Field": "JobExecution",
        "Columns": _get_table_columns(cursor, "EVENTS"),
        "Example": cleaned_rows,
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

def random_JobID(cursor: sqlite3.Cursor) -> Dict[str, Any]:

    jobid = cursor.execute("""
    SELECT DISTINCT JOB_ID FROM EVENTS ORDER BY RANDOM() LIMIT 1;
    """).fetchone()[0]
    cursor.execute(f"""
        SELECT EVENT, STATE, STATUS, JOB_ID, TIME, METADATA
        FROM EVENTS
        WHERE JOB_ID = {jobid}
        ORDER BY EVENT;
    """)
    rows = cursor.fetchall()

    cleaned_rows = []
    for row in rows:
        row = list(row)
        meta = row[5]
        if isinstance(meta, str):
            try:
                row[5] = json.loads(meta)
            except Exception:
                pass
        row[0] = f"'EVENT': {row[0]}"
        row[1] = f"'STATE': {row[1]}"
        row[2] = f"'STATUS: {row[2]}"
        row[3] = f"'JOB_ID': {row[3]}"
        row[4] = f"'TIME': {row[4]}"
        row[5] = f"'META': {row[5]}"
        cleaned_rows.append(row)

    return {
        "JOB_ID": jobid,
        "CONTENTS": cleaned_rows,
    }