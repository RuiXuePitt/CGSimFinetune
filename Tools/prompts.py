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
        10) If Question appears "successful", that means something is FINISHED!!!
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
    
    reason_check:
    - Must start with "Let's think step by step."
    - check_* tools are just used for sampling the data related to the EVENT type ["JobAllocation", "FileTransfer", "FileRead", "FileWrite", "JobExecution"],
    - So be CONCISE, and just explain why the question is likely related to the specific EVENT type.
        KEY words: mentioned "allocation", "transfer", "read", "write", "execution", or other synonyms indicate the EVENT types.
        KEY words DO NOT include field names in the question, since the real model has no knowledge of data.
        Reasoning format should be "According to [KEY word likely related to EVENT type], [EVENT type] should be checked"
    - If there is no key word related to ["JobAllocation", "FileTransfer", "FileRead", "FileWrite", "JobExecution"],
        Reaoning should be concise, explain you cannot make sure, so "check_All" is needed.

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ... (starts with "Let's think step by step."),
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
    
    reason_check:
    - Must start with "Let's think step by step."
    - check_All tool is used for sampling the data when question does not specify the exact EVENT type.
    - So be CONCISE, and just say the question is ambiguous so check_All is necessary to specify the field.
        Reaoning should be concise, explain you cannot make sure (like, the EVENT type is not specified), so "check_All" is needed.
        Do not mention any other information related to DATASAMPLES.

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ... (starts with "Let's think step by step."),
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
    - For JOB_ID / EVENT / STATE / STATUS:
        * Use LIKE ONLY without wildcards (no '%' and no '_'), i.e. LIKE 'ExactValue'.
        * Never use pattern matching for these fields.
    
    reason_sql:
    - Must start with "Let's think step by step."
    - You may say "According to check_*, ..." to justify which STRUCTURE keys you chose,
        but do not treat check_result as a restriction on values.  
    - Explain SQL operations CONCISELY (filtering, grouping, aggregation, sorting, etc.).
  
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
    
    reason_check:
    - Must start with "Let's think step by step."
    - check_* tools are just used for sampling the data related to the EVENT type ["JobAllocation", "FileTransfer", "FileRead", "FileWrite", "JobExecution"],
    - So be CONCISE, and just explain why the question is likely related to the specific EVENT type.
        KEY words: mentioned "allocation", "transfer", "read", "write", "execution", or other synonyms indicate the EVENT types.
        KEY words DO NOT include field names in the question, since the real model has no knowledge of data.
        Reasoning format should be "According to [KEY word likely related to EVENT type], [EVENT type] should be checked"
    - If there is no key word related to ["JobAllocation", "FileTransfer", "FileRead", "FileWrite", "JobExecution"],
        Reaoning should be concise, explain you cannot make sure, so "check_All" is needed.

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ... (starts with "Let's think step by step."),
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
    
    reason_check:
    - Must start with "Let's think step by step."
    - check_All tool is used for sampling the data when question does not specify the exact EVENT type.
    - So be CONCISE, and just say the question is ambiguous so check_All is necessary to specify the field.
        Reaoning should be concise, explain you cannot make sure (like, the EVENT type is not specified), so "check_All" is needed.
        Do not mention any other information related to DATASAMPLES.

    Return JSON exactly:
    {{
        "user_question": ...,
        "reason_check": ... (starts with "Let's think step by step."),
        "check_tool": "check_All"
    }}
"""

prompt_final_answer = """
        You are CGsim-Answerer.

        Task:
        Given a user question and the SQL execution result, produce a final answer in a STRICT machine-parsable format.

        STRICT OUTPUT FORMAT:
        - If there is NO usable answer, output exactly:
        __NULL_RESULT__
        (no other characters, no punctuation, no extra text, no whitespace lines)

        - Otherwise output exactly one line starting with:
        __ANSWER__ 
        followed by the answer text.

        When to output __NULL_RESULT__ (ANY triggers it):
        - sql_result has zero rows (empty result)
        - sql_result contains any NULL-like value (NULL / None / null)
        - the requested value(s) cannot be determined unambiguously from sql_result

        Human Readable Answer text formatting rules (when output is __ANSWER__):
        - Write a concise summary with polite explanations to the question.

        Inputs:
        [User Question]
        {user_question}

        [SQL]
        {sql}

        [SQL Result]
        {sql_result}

        Now produce the output.
    """