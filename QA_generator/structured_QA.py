import sqlite3
import json
from pathlib import Path
import random
import sys
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
import QA_Templates as tp

tool_dir = current_dir.parent / "Tools"
sys.path.append(str(tool_dir))
import DBTool as dbt

db_path = current_dir.parent / "resources" / "CGsimSite.db"
output = current_dir.parent / "resources" / "structured_QA.jsonl"

def randQA_joballocation_jobid(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT json_extract(METADATA, '$.site') AS site FROM EVENTS WHERE EVENT = 'JobAllocation';
    """
    cursor.execute(cmd)
    sites = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_JOBALLOCATION_JOBID)
        site = random.choice(sites)
        temp_Q = temp_Q.format(site = site)
        temp_A = temp_A.format(site = site)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(site = site, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


resource_field_allocation = [
    {"grid_cpu_util":["grid cpu utilization", "grid cpu usage", "grid cpu status", "grid_cpu_util", "grid cpu resource"]},
    {"grid_storage_util": ["grid space utilization", "grid space usage", "grid space status", "grid_storage", "grid storage"]},
    {"site_cpu_util":["site cpu utilization", "site cpu usage", "site cpu status", "site_cpu_util", "site cpu resource"]},
    {"site_storage_util": ["site space utilization", "site space usage", "site space status", "site_storage", "site storage"]},
    {"site": ["site name", "site"]},
    {"host": ["host name", "host"]}
]
def randQA_joballocation_resource_extraction(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION)
        item_field = random.choice(resource_field_allocation)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(field1 = field1, field2 = field2, jobid = jid, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


resource_field_transfer = [
    {"duration":["transferring time", "transfer time", "time for file transfer", "file transfer duration"]},
    {"bandwidth": ["bandwidth", "band width", "bands width"]},
    {"destination_site": ["destination site", "target site", "receiving site", "ending site", "destination_site"]},
    {"source_site": ["source site", "start site", "source_site", "sending site"]},
    {"latency": ["latency", "latacy", "latent time"]}
]
def randQA_filetransfer_mix(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'FileTransfer';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_FILETRANSFER_MIX)
        item_field = random.choice(resource_field_transfer)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(field1 = field1, field2 = field2, jobid = jid, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


resource_field_read = [
    {"duration":["file reading time", "read time", "time for file reading", "file read duration"]},
    {"disk": ["disk name", "file disk"]},
    {"disk_read_bw": ["read band width", "file read bandwidth", "disk reading band width", "disk read bandwidth"]}
]
def randQA_fileread_mix(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'FileRead';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_FILEREAD_MIX)
        item_field = random.choice(resource_field_read)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(field1 = field1, field2 = field2, jobid = jid, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return


resource_field_write = [
    {"duration":["file writing time", "write time", "time for file writing", "file write duration"]},
    {"disk": ["disk name", "file disk"]},
    {"disk_write_bw": ["write bandwidth", "file write bandwidth", "disk writing band width", "disk write bandwidth"]}
]
def randQA_filewrite_mix(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'FileWrite';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_FILEWRITE_MIX)
        item_field = random.choice(resource_field_write)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(field1 = field1, field2 = field2, jobid = jid, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return

resource_field_execution = [
    {"duration":["execution time", "run time", "duration"]},
    {"total_queue_time": ["queue time", "total queue time"]},
    {"speed": ["speed", "cpu speed"]},
    {"flops": ["flops", "compute flops"]}
]
def randQA_jobexecution_mix(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobExecution';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2, ans = random.choice(tp.TEMPLATE_JOBEXECUTION_MIX)
        item_field = random.choice(resource_field_execution)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        row = dbt.execute_sql(cursor, temp_A)[0][0]
        ans = ans.format(field1 = field1, field2 = field2, jobid = jid, ans = row)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2, "answer": ans})

    with open(str(output), "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return

def check_allsql(cursor: sqlite3.Cursor, output: Path):
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

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    randQA_joballocation_jobid(100, cursor)
    randQA_joballocation_resource_extraction(100, cursor)
    randQA_filetransfer_mix(100, cursor)
    randQA_fileread_mix(100, cursor)
    randQA_jobexecution_mix(100, cursor)
    check_allsql(cursor, output)

    # result = dbt.check_All(cursor)
    # for _ in result:
    #     print(_)

    cursor.close()
    conn.close()
    return

if __name__ == "__main__":
    main()
