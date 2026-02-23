import json
from pathlib import Path
from typing import List, Dict
import sqlite3
import sys

currdir = Path(__file__).parent
tool_dir = currdir.parent / "Tools"
sys.path.append(str(tool_dir))
import DBTool as dbt

resourcedir = currdir.parent / "resources"
db_path = currdir.parent / "resources" / "CGsimSite.db"
dbt.set_db_path(str(db_path))

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_JobAllocation",
            "description": "Sample JobAllocation events from the CGsim `EVENTS` table to inspect the job allocation data structure (columns and example rows).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_FileTransfer",
            "description": "Sample FileTransfer events from the CGsim `EVENTS` table to inspect the file transfer data structure (columns and example rows).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_FileRead",
            "description": "Sample FileRead events from the CGsim `EVENTS` table to inspect the file read data structure (columns and example rows).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_FileWrite",
            "description": "Sample FileWrite events from the CGsim `EVENTS` table to inspect the file write data structure (columns and example rows).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_JobExecution",
            "description": "Sample JobExecution events from the CGsim `EVENTS` table to inspect the job execution data structure (columns and example rows).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_All",
            "description": "Sample a small set of rows for each known event type in the CGsim `EVENTS` table (JobAllocation, FileTransfer, FileRead, FileWrite, JobExecution) to quickly inspect schemas when the relevant event type is unclear.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Execute a SQLite SQL query against the CGsim `EVENTS` database and return all resulting rows. Prefer read-only SELECT queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute (SQLite dialect) against the CGsim `EVENTS` database."
                    }
                },
                "required": ["sql"],
                "additionalProperties": False
            }
        }
    }
]

system_prompt = "You are a CGsim agent. Answer questions related to grid simulation related questions. Use tools when needed."


def load() -> List[Dict]:
    records = [] 
    with open(str(resourcedir / "test_sql.jsonl"), "r") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records

def converter(records: List[Dict]) -> List:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    training_dataset = []
    for r in records:
        messages = []
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": r["question"]})
        messages.append({"role": "assistant", "content": r["think1"], "tool_calls": [{"type": "function", "function": {"name": r["tool1"], "arguments": {}}}]})
        messages.append({"role": "tool", "content": json.dumps(getattr(dbt, r["tool1"])(cursor), ensure_ascii=False)})
        messages.append({"role": "assistant", "content": r["think2"], "tool_calls": [{"type": "function", "function": {"name": r["tool2"], "arguments": {"sql": r["sql"]}}}]})
        messages.append({"role": "tool", "content": json.dumps(getattr(dbt, r["tool2"])(cursor, r["sql"]), ensure_ascii=False)})
        messages.append({"role": "assistant", "content": r["answer"]})

        training_dataset.append({"tools": tools, "messages": messages})

    cursor.close()
    conn.close()
    return training_dataset

def write(training_dataset: List) -> None:
    with open(str(resourcedir / "testdata.jsonl"), "w") as f:
        for d in training_dataset:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return

if __name__ == "__main__":
    records = load()
    training_dataset = converter(records)
    write(training_dataset)