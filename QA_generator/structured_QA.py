import sqlite3
import json
from pathlib import Path
import random

current_dir = Path(__file__).parent
db_path = current_dir.parent / "resources" / "CGsimSite.db"
output = current_dir.parent / "resources" / "ques_sql.jsonl"

# question, sql, think1, think2, tool1, tool2
TEMPLATE_JOBALLOCATION_JOBID = [
    (
        "What is the allocation job id at site {site}?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        "Let's think step by step.\n"
        "According to 'allocation', JobAllocation data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'allocation', EVENT = 'JobAllocation' may be used.\n"
        "According to 'job id', JOB_ID may be selected.\n"
        "According to 'site', json_extract(METADATA, '$.site') may be used for filtering.\n"
        "According to 'unique', DISTINCT may be used.\n",
        "check_JobAllocation",
        "execute_sql",
    ),
    (
        "At site {site}, what is the allocated job id?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        "Let's think step by step.\n"
        "According to 'allocated', JobAllocation data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'allocated', EVENT = 'JobAllocation' may be used.\n"
        "According to 'job id', JOB_ID may be selected.\n"
        "According to 'site', json_extract(METADATA, '$.site') may be used for filtering.\n"
        "According to 'unique', DISTINCT may be used.\n",
        "check_JobAllocation",
        "execute_sql",
    ),
    (
        "List the allocated JOB_IDs for JobAllocation events at site {site}.",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        "Let's think step by step.\n"
        "According to 'JobAllocation events', JobAllocation data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'JobAllocation events', EVENT = 'JobAllocation' may be used.\n"
        "According to 'JOB_IDs', JOB_ID may be selected.\n"
        "According to 'site', json_extract(METADATA, '$.site') may be used for filtering.\n"
        "According to 'unique', DISTINCT may be used.\n",
        "check_JobAllocation",
        "execute_sql",
    ),
    (
        "Which job IDs were allocated at {site} site?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        "Let's think step by step.\n"
        "According to 'allocated', JobAllocation data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'allocated', EVENT = 'JobAllocation' may be used.\n"
        "According to 'job IDs', JOB_ID may be selected.\n"
        "According to 'site', json_extract(METADATA, '$.site') may be used for filtering.\n"
        "According to 'unique', DISTINCT may be used.\n",
        "check_JobAllocation",
        "execute_sql",
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
        temp_Q, temp_A, think1, think2, tool1, tool2 = random.choice(TEMPLATE_JOBALLOCATION_JOBID)
        site = random.choice(sites)
        temp_Q = temp_Q.format(site = site)
        temp_A = temp_A.format(site = site)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2})

    with open(str(output), "a", encoding="utf-8") as f:
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
TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION = [
    (
        "For job {jobid}, what is the {field1} in the JobAllocation record?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS value "
        "FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        "Let's think step by step.\n"
        "According to 'JobAllocation', JobAllocation data structure should be checked.\n",

        "Let's think step by step.\n"
        "According to 'JobAllocation', EVENT='JobAllocation' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        
        "check_JobAllocation",
        "execute_sql"
    ),
    (
        "For job {jobid}, what is the recorded {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        "Let's think step by step.\n"
        "The EVENT type is not specified. Therefore, all available event types and their data structures should be checked.\n",

        "Let's think step by step.\n"
        "According to checked data structure, {field1} may be related to {field2} in EVENT = 'JobAllocation'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        
        "check_All",
        "execute_sql"
    ),
    (
        "For the allocation of job {jobid}, show the {field1} from the metadata.",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        "Let's think step by step.\n"
        "According to 'allocation', JobAllocation data structure should be checked.\n",

        "Let's think step by step.\n"
        "According to 'allocation', EVENT = 'JobAllocation' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_JobAllocation",
        "execute_sql"
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
        temp_Q, temp_A, think1, think2, tool1, tool2 = random.choice(TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION)
        item_field = random.choice(resource_field_allocation)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2})

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
TEMPLATE_FILETRANSFER_MIX = [
    (
        "What is the {field1} of job {jobid} in the file transfer event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "According to 'file transfer', FileTransfer data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'file transfer', EVENT = 'FileTransfer' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_FileTransfer",
        "execute_sql"
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "The EVENT type is not specified. Therefore, all available event types and their data structures should be checked.\n",
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileTransfer'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_All",
        "execute_sql"
    ),
    (
        "For job {jobid}, what is the {field1} during transfer?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        # think1 (conservative trigger)
        "Let's think step by step.\n"
        "According to 'transfer', the EVENT type may be FileTransfer but is not certain.\n"
        "Therefore, all available event types and their data structures should be checked.\n",

        # think2 (commit after structure check; tool1res comes as next-turn input)
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileTransfer'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_All",
        "execute_sql",
    )
]   
def randQA_filetransfer_mix(amount: int, cursor: sqlite3.Cursor):
    cmd = """
    SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation';
    """
    cursor.execute(cmd)
    ids = [it[0] for it in cursor.fetchall()]
    samples = []
    for _ in range(amount):
        temp_Q, temp_A, think1, think2, tool1, tool2 = random.choice(TEMPLATE_FILETRANSFER_MIX)
        item_field = random.choice(resource_field_transfer)
        field2 = list(item_field.keys())[0]
        field1 = random.choice(item_field[field2])
        jid = random.choice(ids)
        temp_Q = temp_Q.format(field1=field1, jobid=jid)
        temp_A = temp_A.format(field2=field2, jobid=jid)
        think1 = think1.format(field1=field1, field2=field2)
        think2 = think2.format(field1=field1, field2=field2, jobid=jid)
        samples.append({"question": temp_Q, "sql": temp_A, "think1": think1, "think2": think2, "tool1": tool1, "tool2": tool2})

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
    randQA_filetransfer_mix(10, cursor)
    return

if __name__ == "__main__":
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    main(cursor)
    # checksql(cursor)
    cursor.close()
    conn.close()