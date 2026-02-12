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


TEMPLATE_FILEREAD_MIX = [
    (
        "What is the {field1} of job {jobid} in the file reading event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "According to 'file reading', FileRead data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'file reading', EVENT = 'FileRead' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_FileRead",
        "execute_sql"
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "The EVENT type is not specified. Therefore, all available event types and their data structures should be checked.\n",
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileRead'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_All",
        "execute_sql"
    ),
    (
        "For job {jobid}, what is the {field1} during reading task?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileRead' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        # think1 (conservative trigger)
        "Let's think step by step.\n"
        "According to 'reading task', the EVENT type may be FileRead but is not certain.\n"
        "Therefore, all available event types and their data structures should be checked.\n",

        # think2 (commit after structure check; tool1res comes as next-turn input)
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileRead'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_All",
        "execute_sql",
    )
]


TEMPLATE_FILEWRITE_MIX = [
    (
        "What is the {field1} of job {jobid} in the file writing event?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "According to 'file writing', FileWrite data structure should be checked.\n",
        "Let's think step by step.\n"
        "According to 'file writing', EVENT = 'FileWrite' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_FileWrite",
        "execute_sql"
    ),
    (
        "What is the {field1} of job {jobid}?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",
        "Let's think step by step.\n"
        "The EVENT type is not specified. Therefore, all available event types and their data structures should be checked.\n",
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileWrite'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",
        "check_All",
        "execute_sql"
    ),
    (
        "For job {jobid}, what is the {field1} during writing task?",
        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} FROM EVENTS "
        "WHERE EVENT = 'FileWrite' "
        "AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        # think1 (conservative trigger)
        "Let's think step by step.\n"
        "According to 'writing task', the EVENT type may be FileWrite but is not certain.\n"
        "Therefore, all available event types and their data structures should be checked.\n",

        # think2 (commit after structure check; tool1res comes as next-turn input)
        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'FileWrite'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_All",
        "execute_sql",
    )
]

TEMPLATE_JOBEXECUTION_MIX = [
    (
        "For job {jobid}, what is the {field1} in the JobExecution record?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        "Let's think step by step.\n"
        "According to 'JobExecution', JobExecution data structure should be checked.\n",

        "Let's think step by step.\n"
        "According to 'JobExecution', EVENT = 'JobExecution' may be used.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_JobExecution",
        "execute_sql"
    ),
    (
        "For job {jobid}, what is the recorded {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        "Let's think step by step.\n"
        "The EVENT type is not specified. Therefore, all available event types and their data structures should be checked.\n",

        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'JobExecution'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_All",
        "execute_sql"
    ),
    (
        "During execution of job {jobid}, what is the {field1}?",

        "SELECT DISTINCT json_extract(METADATA, '$.{field2}') AS {field2} "
        "FROM EVENTS WHERE EVENT = 'JobExecution' AND JOB_ID = {jobid} "
        "AND json_extract(METADATA, '$.{field2}') IS NOT NULL;",

        "Let's think step by step.\n"
        "According to 'execution', the EVENT type may be JobExecution but is not certain.\n"
        "Therefore, all available event types and their data structures should be checked.\n",

        "Let's think step by step.\n"
        "According to checked data structure, '{field1}' may be related to '{field2}' in EVENT = 'JobExecution'.\n"
        "According to '{jobid}', JOB_ID may be used for filtering.\n"
        "According to '{field1}', use json_extract(METADATA, '$.{field2}') to retrieve the value.\n",

        "check_All",
        "execute_sql"
    )
]