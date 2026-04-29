# question, sql, think1, think2, tool1, tool2
RC_ALLOC = "According to 'allocation' in the question, check_JobAllocation should be used.\n"
RC_TRANSFER = "According to 'transfer' in the question, check_FileTransfer should be used.\n"
RC_READ = "According to 'read' in the question, check_FileRead should be used.\n"
RC_WRITE = "According to 'write' in the question, check_FileWrite should be used.\n"
RC_EXEC = "According to 'execution' in the question, check_JobExecution should be used.\n"
RC_AMBIG = "The event type is not clear, so check_All should be used.\n"

RS_DISTINCT = "Need filters, json_extract, and DISTINCT.\n"
RS_FILTER_JSON = "Need filters and json_extract.\n"

TEMPLATE_JOBALLOCATION_JOBID = [
    (
        "What is the allocation job id at site {site}?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        RC_ALLOC,
        "Need filters, json_extract, and DISTINCT.\n",
        "check_JobAllocation",
        "execute_sql",
        "At site '{site}', the allocated job id is '{ans}'."
    ),
    (
        "At site {site}, what is the allocated job id?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        RC_ALLOC,
        "Need filters, json_extract, and DISTINCT.\n",
        "check_JobAllocation",
        "execute_sql",
        "At site '{site}', the allocated job id is '{ans}'."
    ),
    (
        "List the allocated JOB_IDs for JobAllocation events at site {site}.",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        RC_ALLOC,
        "Need filters, json_extract, and DISTINCT.\n",
        "check_JobAllocation",
        "execute_sql",
        "At site '{site}', the allocated job id is '{ans}'."
    ),
    (
        "Which job IDs were allocated at {site} site?",
        "SELECT DISTINCT JOB_ID FROM EVENTS WHERE EVENT = 'JobAllocation' AND json_extract(METADATA, '$.site') = '{site}';",
        RC_ALLOC,
        "Need filters, json_extract, and DISTINCT.\n",
        "check_JobAllocation",
        "execute_sql",
        "At site '{site}', the allocated job id is '{ans}'."
    )
]


TEMPLATE_JOBALLOCATION_RESOURCE_EXTRACTION = [
    (
        "For job {jobid}, what is the {field1} in the JobAllocation record?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS value "
        "FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        RC_ALLOC,
        RS_DISTINCT,

        "check_JobAllocation",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobAllocation record, and the value is '{ans}'."
    ),
    (
        "For job {jobid}, what is the recorded {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        RC_AMBIG,
        RS_DISTINCT,

        "check_All",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobAllocation record, and the value is '{ans}'."
    ),
    (
        "For the allocation of job {jobid}, show the {field1} from the metadata.",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobAllocation' AND JOB_ID = {jobid};",

        RC_ALLOC,
        RS_DISTINCT,

        "check_JobAllocation",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobAllocation record, and the value is '{ans}'."
    )
]


TEMPLATE_FILETRANSFER_MIX = [
    (
        "What is the {field1} of job {jobid} in the file transfer event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_TRANSFER,
        RS_DISTINCT,
        "check_FileTransfer",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileTransfer record, and the value is '{ans}'."
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_AMBIG,
        RS_DISTINCT,
        "check_All",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileTransfer record, and the value is '{ans}'."
    ),
    (
        "For job {jobid}, what is the {field1} during transfer?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileTransfer' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_TRANSFER,
        RS_DISTINCT,
        "check_FileTransfer",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileTransfer record, and the value is '{ans}'."
    )
]   


TEMPLATE_FILEREAD_MIX = [
    (
        "What is the {field1} of job {jobid} in the file reading event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_READ,
        RS_DISTINCT,
        "check_FileRead",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileRead record, and the value is '{ans}'."
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_AMBIG,
        RS_DISTINCT,
        "check_All",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileRead record, and the value is '{ans}'."
    ),
    (
        "For job {jobid}, what is the {field1} during reading task?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_READ,
        RS_DISTINCT,
        "check_FileRead",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileRead record, and the value is '{ans}'."
    )
]


TEMPLATE_FILEWRITE_MIX = [
    (
        "What is the {field1} of job {jobid} in the file writing event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_WRITE,
        RS_DISTINCT,
        "check_FileWrite",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileWrite record, and the value is '{ans}'."
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_AMBIG,
        RS_DISTINCT,
        "check_All",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileWrite record, and the value is '{ans}'."
    ),
    (
        "For job {jobid}, what is the {field1} during writing task?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        RC_WRITE,
        RS_DISTINCT,
        "check_FileWrite",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the FileWrite record, and the value is '{ans}'."
    )
]

TEMPLATE_JOBEXECUTION_MIX = [
    (
        "For job {jobid}, what is the {field1} in the JobExecution record?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        RC_EXEC,
        RS_DISTINCT,

        "check_JobExecution",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobExecution record, and the value is '{ans}'."
    ),
    (
        "For job {jobid}, what is the recorded {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        RC_AMBIG,
        RS_DISTINCT,

        "check_All",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobExecution record, and the value is '{ans}'."
    ),
    (
        "During execution of job {jobid}, what is the {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        RC_EXEC,
        RS_DISTINCT,

        "check_JobExecution",
        "execute_sql",
        "For job '{jobid}', the '{field1}' is related to '{field2}' in the JobExecution record, and the value is '{ans}'."
    )
]