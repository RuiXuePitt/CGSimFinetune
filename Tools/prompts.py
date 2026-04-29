general_structure = """
        1) Column Name ONLY CONTAINS [_ID, EVENT, STATE, STATUS, JOB_ID, TIME, METADATA]
        2) STATE ONLY CONTAINS ["Finished", "Started"], SQL only use "STATE = Finished" or "STATE = Started" when filtering.
        3) STATUS ONLY CONTAINS ["running", "assigned", "finished"], SQL only use "STATUS = running / assigned / finished" when filtering.
        4) EVENT ONLY CONTAINS ["JobExecution", "JobAllocation", "FileRead", "FileWrite", "FileTransfer"]
        5) JobAllocation METADATA Key ONLY CONTAINS ["grid_cpu_util", "grid_storage_util", "host", "site", "site_cpu_util", "site_storage_util"]
        6) JobExecution METADATA Key ONLY CONTAINS ["cores", "cost", "duration", "file_transfer_queue_time", "flops", "grid_cpu_util", "host", "resource_waiting_queue_time", "retries","site", "site_cpu_util", "speed", "total_io_read_time", "total_queue_time"]
        7) FileRead METADATA Key ONLY CONTAINS ["disk", "disk_read_bw", "duration", "file", "host", "site", "size"]
        8) FileWrite METADATA Key ONLY CONTAINS ["disk", "disk_write_bw", "duration", "file", "grid_storage_util", "host", "site", "site_storage_util", "size"]
        9) FileTransfer METADATA Key ONLY CONTAINS ["bandwidth", "destination_site", "duration", "file", "grid_storage_util", "latency", "link_load", "site_storage_util", "size", "source_site"]
        10) Success-filter rule for SQL generation:
            - FileRead/FileWrite/FileTransfer successful operations: STATE = 'Finished'
            - JobExecution successful execution: STATUS = 'finished'
            - JobAllocation success/assignment depends on wording; use STATUS = 'assigned' only when the question is about allocation assignment.
    """

reason_check = """
        reason_check:
        - Reasoning MUST NOT include prior knowledge of the database.
        - The only goal is to choose the most relevant check_* tool.
        - Write exactly ONE concise sentence.
        - Do not mention metadata keys, columns, SQL, aggregation, or database schema.

        Reasoning examples for clear questions:
        1) "According to 'execution' in the question, check_JobExecution should be used."
        2) "According to 'file transfers' in the question, check_FileTransfer should be used."
        3) "According to 'read operations' in the question, check_FileRead should be used."
        4) "According to 'write operations' in the question, check_FileWrite should be used."
        5) "According to 'resource assignment' in the question, check_JobAllocation should be used."

        Reasoning examples for ambiguous questions:
        1) "The question is ambiguous, so check_All should be used to fetch more information."
        2) "The event type is not clear, so check_All should be used to fetch more information."
        3) "The question does not specify a clear activity type, so check_All should be used."

        Tool-routing hints:
        - allocation / assignment / placement / resource assignment -> check_JobAllocation
        - execution / processing / compute / running / queue / speed / flops -> check_JobExecution
        - transfer / migration / movement / sent / delivered / source / destination -> check_FileTransfer
        - read / retrieve / input / opened file / disk read -> check_FileRead
        - write / save / output / stored file / disk write -> check_FileWrite
        - ambiguous / unclear activity type / multiple possible stages -> check_All
    """

reason_sql = """
        reason_sql:
        - At most 2 short sentences.
        - Write a compact SQL plan, not a detailed explanation.
        - Mention only needed operations: filters, json_extract, aggregation, grouping, sorting, DISTINCT, LIMIT.
        - Do not mention operation details. Only mention the operation name.
        - Do not mention any operation that is not used by the SQL.

        Examples:
        1) "Need filters and json_extract. Need aggregation."
        2) "Need filters, json_extract, grouping, and aggregation."
        3) "Need filters, json_extract, sorting, and LIMIT."
        4) "Need json_extract and DISTINCT."
        5) "Need grouping and aggregation."  
    """

prompt_jobid_questions = """
    You are CGsim-DataGen-Planner.

    JOB_ID = {jobid}
    DATASAMPLES = {datasamples}
    STRUCTURE = {general_structure}
    
    - Forbidden: any JOB_ID string other than {jobid}. Do NOT write "job_XXXX" or "JOB_ID_XXX".
    
    HARD:
    - Output raw JSON only (no markdown / no ```).
    - user_question MUST mention {jobid} exactly.
    - Choose check_tool accordingly:
        job allocation->check_JobAllocation; job execution->check_JobExecution;
        file transfer->check_FileTransfer; file read->check_FileRead; file write->check_FileWrite.
    - Do NOT output SQL in this stage.
    - Do NOT invent any entity/value (site/host/file/etc). Only use values shown in DATASAMPLES.
    - Any METADATA key you mention MUST be allowed for the chosen EVENT in STRUCTURE, and must appear in DATASAMPLES.

    ADD (difficulty / medium SQL):
    - The question should require medium-difficulty SQL to answer.
    - But DO NOT SQL Key words. You should mimic normal users asking questions.
    - Concretely, it should imply at least ONE of these patterns:
        1) GROUP BY + aggregation (COUNT/AVG/MIN/MAX)
        2) DISTINCT
        3) JSON filtering via json_extract(METADATA, '$.key')
        4) ORDER BY + LIMIT (Top-K)
        5) Subquery (e.g., JOB_ID IN (SELECT ...))
        6) Conditional aggregation (SUM(CASE WHEN ... THEN 1 ELSE 0 END))
    - Avoid questions are solvable by a trivial query like:
        SELECT * WHERE JOB_ID=... LIMIT ...

    ADD (human language style / avoid exact field names):
    - user_question MUST be natural, human-language style.
    - user_question MUST NOT directly name exact database columns or functions.
    - Instead, refer to them indirectly, e.g.:
        grid_cpu_util -> "grid cpu utilization", "cpu usage on the grid", "overall grid cpu load", "how busy the grid cpu was", etc.
      And you should come up with other human style language.
    - Still, any concrete entity/value you mention must come from DATASAMPLES.
    
    {reason_check}     

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ...,
        "check_tool": "check_JobAllocation" | "check_FileTransfer" | "check_FileRead" | "check_FileWrite" | "check_JobExecution" | "check_All"
    }}
"""

prompt_ambiguous_jobid_questions = """
    You are CGsim-DataGen-Planner.

    JOB_ID = {jobid}
    DATASAMPLES = {datasamples}
    STRUCTURE = {general_structure}
    
    - Forbidden: any JOB_ID string other than {jobid}. Do NOT write "job_XXXX" or "JOB_ID_XXX".
    
    HARD:
    - Generate an ambiguous question that mentions job id, but without clarifying (or ambiguous) EVENT value, so that check_All is needed.
        - The Question is actually STILL related to an EVENT, but this would be found through "check_All", instead of mentioning in the question.
    - Output raw JSON only (no markdown / no ```).
    - user_question MUST mention {jobid} exactly.
    - Do NOT output SQL in this stage.
    - Do NOT invent any entity/value (site/host/file/etc). Only use values shown in DATASAMPLES.
    - Any METADATA key you mention MUST be allowed for the chosen EVENT in STRUCTURE, and must appear in DATASAMPLES.

    ADD (difficulty / medium SQL):
    - The question should require medium-difficulty SQL to answer.
    - But DO NOT SQL Key words. You should mimic normal users asking questions.
    - Concretely, it should imply at least ONE of these patterns:
        1) GROUP BY + aggregation (COUNT/AVG/MIN/MAX)
        2) DISTINCT
        3) JSON filtering via json_extract(METADATA, '$.key')
        4) ORDER BY + LIMIT (Top-K)
        5) Subquery (e.g., JOB_ID IN (SELECT ...))
        6) Conditional aggregation (SUM(CASE WHEN ... THEN 1 ELSE 0 END))
    - Avoid questions are solvable by a trivial query like:
        SELECT * WHERE JOB_ID=... LIMIT ...

    ADD (human language style / avoid exact field names):
    - user_question MUST be natural, human-language style.
    - user_question MUST NOT directly name exact database columns or functions.
    - Instead, refer to them indirectly, e.g.:
        grid_cpu_util -> "grid cpu utilization", "cpu usage on the grid", "overall grid cpu load", "how busy the grid cpu was", etc.
      And you should come up with other human style language.
    - Still, any concrete entity/value you mention must come from DATASAMPLES.
    
    {reason_check}

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ...,
        "check_tool": "check_All"
    }}
"""

prompt_jobid_sql = """
    You are CGsim SQL writter.
    You will output:
    - reason_sql: reasoning that justifies the SQL
    - sql: a single SQL query that answers the question

    INPUTS:
    - user_question = {user_question}
    - reason_check = {reason_check}
    - check_tool = {check_tool}
    - check_result = {check_result}

    BACKGROUND:
    Originally, the user asked a question and you have no idea of the CGSim database structure.
    Then the "check_tool" is called to randomly sample from the database for the most related EVENT type(s)
    to understand available fields/metadata. 
    Now, based on the check_result, (KEYS are ONLY from check_result, DO NOT invent KEYS do not exist), 
    write a SQL query that fetches the most useful information to answer the question.

    HARD:
    - Output raw JSON only (no markdown / no ```).
    - Use only EVENTS table.
    - json_extract(METADATA,'$.<key>') keys MUST:
    (1) appear in check_result (no guessing).
    (2) METADATA keys must be accessed as: json_extract(METADATA, '$.<key>').
    (3) For METADATA filters:
        - Prefer string matching with LIKE whenever possible.
        - Do NOT use '=' for string fields (site/host/file/source/destination). Use LIKE instead.

        String / name matching:
        - If the user provides a fuzzy / partial name (most common), use pattern-match:
            json_extract(METADATA,'$.<key>') LIKE '%'value'%'
        (This is case-insensitive and robust to imperfect user input.)

        - If the user provides an exact-looking full name, still use LIKE but without wildcards:
            json_extract(METADATA,'$.<key>') LIKE '<full_name>'
        (Avoid '=' while still matching case-insensitively.)

        Numeric exact queries (the ONLY exception to avoid LIKE):
        - Use '=' ONLY when the user asks for an exact numeric match on a numeric metadata value
        (e.g., "exactly 8 cores", "size equals 1048576", "duration is exactly 30 seconds").
    - If user_question did NOT mention site (or source/destination site), SQL should NOT filter by it.    
    - For direct columns JOB_ID / EVENT / STATE / STATUS, use exact equality with =, not LIKE.
        Examples: JOB_ID = '2794720992', EVENT = 'JobExecution', STATE = 'Finished', STATUS = 'finished'.
    
    {reason_sql}

    SQL quality rules:
    - Return every quantity asked by the question. If it asks "which X and what Y", SELECT both X and Y.
    - If ORDER BY ranks by a metric that the question asks about, SELECT that metric too.
    - successful/completed/finished -> STATE = 'Finished' for FileRead/FileWrite/FileTransfer; STATUS = 'finished' for JobExecution.
    - "from / sent from / originating from / started from" -> source_site, not STATE = 'Started'.
    - JOB_ID/EVENT/STATE/STATUS use =; metadata strings use json_extract(...) LIKE.    

    Return JSON exactly:
    {{
        "reason_sql": ...,
        "sql": ...
    }}
"""

prompt_general_questions = """
    You are CGsim-DataGen-Planner.

    DATASAMPLES = {datasamples}
    STRUCTURE = {general_structure}
    
    HARD:
    - Output raw JSON only (no markdown / no ```).
    - Choose check_tool accordingly:
        job allocation->check_JobAllocation; job execution->check_JobExecution;
        file transfer->check_FileTransfer; file read->check_FileRead; file write->check_FileWrite.
    - Do NOT output SQL in this stage.
    - Do NOT invent any entity/value (site/host/file/etc). Only use values shown in DATASAMPLES.
    - Any METADATA key you mention MUST be allowed for the chosen EVENT in STRUCTURE, and must appear in DATASAMPLES.

    ADD (difficulty / medium SQL):
    - The question should require medium-difficulty SQL to answer.
    - But DO NOT SQL Key words. You should mimic normal users asking questions.
    - Concretely, it should imply at least ONE of these patterns:
        1) GROUP BY + aggregation (COUNT/AVG/MIN/MAX)
        2) DISTINCT
        3) JSON filtering via json_extract(METADATA, '$.key')
        4) ORDER BY + LIMIT (Top-K)
        5) Conditional aggregation (SUM(CASE WHEN ... THEN 1 ELSE 0 END))
    - Avoid questions solvable by simply listing a few raw rows.
    The question should require aggregation, ranking, or grouping.

    ADD (human language style / avoid exact field names):
    - user_question MUST be natural, human-language style.
    - user_question MUST NOT directly name exact database columns or functions.
    - Instead, refer to them indirectly, e.g.:
        grid_cpu_util -> "grid cpu utilization", "cpu usage on the grid", "overall grid cpu load", "how busy the grid cpu was", etc.
      And you should come up with other human style language.
    - Still, any concrete entity/value you mention must come from DATASAMPLES.
    
    {reason_check}

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ...,
        "check_tool": "check_JobAllocation" | "check_FileTransfer" | "check_FileRead" | "check_FileWrite" | "check_JobExecution" | "check_All"
    }}
"""

prompt_ambiguous_general_questions = """
    You are CGsim-DataGen-Planner.

    DATASAMPLES = {datasamples}
    STRUCTURE = {general_structure}
    
    HARD:
    - Generate an ambiguous question without clarifying (or ambiguous) EVENT value, so that check_All is needed.
        - The Question is actually STILL related to an EVENT, but this would be found through "check_All", instead of mentioning in the question.
    - Output raw JSON only (no markdown / no ```).
    - Do NOT output SQL in this stage.
    - Do NOT invent any entity/value (site/host/file/etc). Only use values shown in DATASAMPLES.
    - Any METADATA key you mention MUST be allowed for the chosen EVENT in STRUCTURE, and must appear in DATASAMPLES.

    ADD (difficulty / medium SQL):
    - The question should require medium-difficulty SQL to answer.
    - But DO NOT SQL Key words. You should mimic normal users asking questions.
    - Concretely, it should imply at least ONE of these patterns:
        1) GROUP BY + aggregation (COUNT/AVG/MIN/MAX)
        2) DISTINCT
        3) JSON filtering via json_extract(METADATA, '$.key')
        4) ORDER BY + LIMIT (Top-K)
        5) Conditional aggregation (SUM(CASE WHEN ... THEN 1 ELSE 0 END))
    - Avoid questions solvable by simply listing a few raw rows.
    The question should require aggregation, ranking, or grouping.

    ADD (human language style / avoid exact field names):
    - user_question MUST be natural, human-language style.
    - user_question MUST NOT directly name exact database columns or functions.
    - Instead, refer to them indirectly, e.g.:
        grid_cpu_util -> "grid cpu utilization", "cpu usage on the grid", "overall grid cpu load", "how busy the grid cpu was", etc.
      And you should come up with other human style language.
    - Still, any concrete entity/value you mention must come from DATASAMPLES.
    
    {reason_check}

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ...,
        "check_tool": "check_All"
    }}
"""

prompt_final_answer = """
        You are CGsim-Answerer.

        Task:
        Given a user question and the SQL execution result, produce a final answer in a STRICT machine-parsable format.

        STRICT OUTPUT FORMAT:
        - If sql_result is empty or all values are NULL/None/null, output exactly:
        __NULL_RESULT__

        - If sql_result cannot answer all requested information, output exactly:
        __INCOMPLETE_RESULT__ <briefly state what is missing>
        
        - Otherwise output exactly:
        __ANSWER__ <concise answer>

        When to output __NULL_RESULT__ (ANY triggers it):
        - sql_result has zero rows (empty result)
        - sql_result contains any NULL-like value (NULL / None / null)
        - the requested value(s) cannot be determined unambiguously from sql_result

        Human Readable Answer text formatting rules (when output is __ANSWER__):
        - Write a concise summary with polite explanations to the question.
        - Be brief: one sentence preferred, two sentences maximum.
        - Answer only from sql_result.
        - Include all requested entities and values.
        - Do not mention SQL, database, query, rows, tuples, or json_extract.
        - Do not guess missing values.
        - Preserve exact job IDs, sites, hosts, disks, and file names.

        Inputs:
        [User Question]
        {user_question}

        [SQL]
        {sql}

        [SQL Result]
        {sql_result}

        Now produce the output.
    """