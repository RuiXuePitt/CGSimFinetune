import sqlite3
import json
from pathlib import Path
import random

current_dir = Path(__file__).parent
db_path = current_dir.parent / "resources" / "CGsimSite.db"
output = current_dir.parent / "resources" / "ques_sql.jsonl"

TEMPLATE_JOBALLOCATION_JOBID = [
    (
        "What is the allocation job id at {site}?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';"
    ),
    (
        "What is the job id at {site} with job allocation task?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';"
    ),
    (
        "At {site}, what is the allocated job id?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';"
    ),
    (
        "List the allocated JOB_IDs for JobAllocation events at {site}.",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';"
    ),
    (
        "Which job IDs were allocated at {site}?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';"
    )
]
def randQA_joballocation_jobid(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT json_extract(METADATA, '$.site') AS site FROM EVENTS WHERE EVENT = 'JobAllocation';
    """
    cursor.execute(cmd)
    sites = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A = random.choice(TEMPLATE_JOBALLOCATION_JOBID)
        temp_Q = temp_Q.format(site = random.choice(sites))
        temp_A = temp_A.format(site = random.choice(sites))
        samples.append({"question": temp_Q, "sql": temp_A})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


resource_field = [
    {"grid_cpu_util":["grid cpu utilization", "grid cpu usage", "grid cpu status", "grid_cpu_util", "grid cpu resource"]},
    {"grid_storage_util": ["grid space utilization", "grid space usage", "grid space status", "grid_storage", "grid storage"]},
    {"site_cpu_util":["site cpu utilization", "site cpu usage", "site cpu status", "site_cpu_util", "site cpu resource"]},
    {"site_storage_util": ["site space utilization", "site space usage", "site space status", "site_storage", "site storage"]},
    {"site": ["site name", "site"]},
    {"host": ["host name", "host"]}
]
TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION = [
    (
        "What is the {field1} with {jobid} allocated?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};"
    ),
    (
        "For job {jobid}, what is the recorded {field1}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};"
    ),
    (
        "Retrieve the {field1} value for JobAllocation records of job {jobid}.",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};"
    ),
    (
        "For the allocation of job {jobid}, show the {field1} from the metadata.",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};"
    )
]
def randQA_joballocation_resource_extraction(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A = random.choice(TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION)
        item_field = random.choice(resource_field)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        temp_Q = temp_Q.format(field1=field1, jobid=random.choice(ids))
        temp_A = temp_A.format(field2=field2, jobid=random.choice(ids))
        samples.append({"question": temp_Q, "sql": temp_A})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


def checksql(cursor: sqlite3.Cursor):
    records = []
    with open(str(output), 'r') as f:
        for line in f:
            records.append(json.loads(line.strip())['sql'])
    for i, record in enumerate(records):
        cursor.execute(record)
        rows = cursor.fetchall()
        if len(rows) == 1 and rows[0][0] == 0:
            print(f"Please check {i}-th {record}")
    return

def main(cursor: sqlite3.Cursor):
    randQA_joballocation_jobid(10, cursor)
    randQA_joballocation_resource_extraction(10, cursor)
    return

if __name__ == "__main__":
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # main(cursor)
    checksql(cursor)
    cursor.close()
    conn.close()