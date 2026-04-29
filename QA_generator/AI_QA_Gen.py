import os
import sys
from pathlib import Path
import json
import sqlite3
import random
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

currdir = Path(__file__).parent
dbpath = currdir.parent / "resources" / "CGsimSite.db"
sys.path.append(str(currdir.parent/"Tools"))
import DBTool as dbt
import prompts as ppts
from structured_QA import check_allsql

output_Q = currdir.parent / "resources" / "train_AI_Q_Gen_v1.jsonl"
# output_QA = currdir.parent / "resources" / "test_AI_QA_Gen_v0.jsonl"
output_QA_ready = currdir.parent / "resources" / "train_AI_QA_Gen_v1_ready.jsonl"
output_QA_sqlerror = currdir.parent / "resources" / "train_AI_QA_Gen_v1_SQLerror.jsonl"
output_QA_null = currdir.parent / "resources" / "train_AI_QA_Gen_v1_NULLanswer.jsonl"
output_QA_incomplete = currdir.parent / "resources" / "train_AI_QA_Gen_v1_INCOMPLETEanswer.jsonl"

def write_jsonl(path: Path, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key = GEMINI_API_KEY)

gemini_model = genai.GenerativeModel("models/gemini-3-flash-preview")
cfg = GenerationConfig(
    temperature=0.8,
    top_p=0.9,
    top_k=40,
    # max_output_tokens=4096,
)

# m = genai.get_model("models/gemini-3-flash-preview")
# print("default temperature:", m.temperature)
# print("default top_p:", m.top_p)
# print("default top_k:", m.top_k)
# print("output_token_limit:", m.output_token_limit)

def llm_general_questions(datasamples, vague = False):
    if vague:
        prompt = ppts.prompt_ambiguous_general_questions
    else:
        prompt = ppts.prompt_general_questions
    prompt = prompt.format(datasamples = datasamples, general_structure = ppts.general_structure,
                           reason_check = ppts.reason_check)
    response = gemini_model.generate_content(prompt)
    try:
        response_text = json.loads(response.text)
        assert isinstance(response_text, dict)
        keys = ["user_question", "reason_check", "check_tool"]
        for k in keys:
            if k not in response_text:
                print("Response is not complete, skip this.")
                return None
        return response_text
        
    except Exception:
        print("Response is  problematic, skip this.")
        print(response_text, "\n")
        return None

def llm_jobid_questions(datasamples, vague = False):
    if vague:
        prompt = ppts.prompt_ambiguous_jobid_questions
    else:
        prompt = ppts.prompt_jobid_questions
    prompt = prompt.format(jobid = datasamples["JOB_ID"], datasamples = datasamples["CONTENTS"], general_structure = ppts.general_structure,
                           reason_check = ppts.reason_check)
    response = gemini_model.generate_content(prompt)
    try:
        response_text = json.loads(response.text)
        assert isinstance(response_text, dict)
        keys = ["user_question", "reason_check", "check_tool"]
        for k in keys:
            if k not in response_text:
                print("Response is not complete, skip this.")
                return None
        return response_text
        
    except Exception:
        print("Response is problematic, skip this.")
        print(response_text, "\n")
        return None

def llm_sql(question, reason_check, check_tool, check_result):
    prompt = ppts.prompt_jobid_sql.format(user_question = question, reason_check = reason_check, check_tool = check_tool, check_result = check_result,
                                          reason_sql = ppts.reason_sql)
    print("SQL Prompt Length: ", len(prompt))
    response = gemini_model.generate_content(prompt, generation_config=cfg)
    try:
        response_text = json.loads(response.text)
        assert isinstance(response_text, dict)
        keys = ["reason_sql", "sql"]
        for k in keys:
            if k not in response_text:
                print("Response is not complete, skip this.")
                return None
        print("User Question: ", question)
        print("Reason Check: ", reason_check)
        print("Check Tool: ", check_tool)
        print("Reason SQL: ", response_text["reason_sql"])
        print("SQL: ", response_text["sql"])
        return response_text
    except Exception:
        print("Response is problematic, skip this.")
        print(response_text, "\n")
        return None


# def llm_generate_answers(datasamples, cursor):
#     prompt = ppts.prompt_final_answer
#     sql_result = dbt.execute_sql(cursor, datasamples["sql"])
#     prompt = prompt.format(user_question = datasamples["user_question"], sql = datasamples["sql"], sql_result = sql_result)
#     response_text = gemini_model.generate_content(prompt, generation_config=cfg).text
#     return response_text
def llm_generate_answers(datasamples, cursor):
    prompt = ppts.prompt_final_answer

    try:
        sql_result = dbt.execute_sql(cursor, datasamples["sql"])
    except Exception as e:
        err_obj = {
            **datasamples,
            "sql_error": str(e),
        }
        write_jsonl(output_QA_sqlerror, err_obj)

        print("SQL EXECUTION ERROR. Skip this answer.")
        print("User Question:", datasamples.get("user_question"))
        print("SQL:", datasamples.get("sql"))
        print("SQL Error:", str(e))
        return "__SQL_ERROR__"

    prompt = prompt.format(
        user_question=datasamples["user_question"],
        sql=datasamples["sql"],
        sql_result=sql_result,
    )

    try:
        response_text = gemini_model.generate_content(
            prompt,
            generation_config=cfg,
        ).text
    except Exception as e:
        err_obj = {
            **datasamples,
            "answer_error": str(e),
        }
        write_jsonl(output_QA_sqlerror, err_obj)

        print("ANSWER GENERATION ERROR. Skip this answer.")
        print("User Question:", datasamples.get("user_question"))
        print("Answer Error:", str(e))
        return "__SQL_ERROR__"

    return response_text

def random_pick(cursor: sqlite3.Cursor):
    event = ["allocation", "execution", "read", "write", "transfer", "all"]
    e = random.choices(event, k=1)
    n = random.randint(1,3)
    m = random.randint(1,3)
    if e == "allocation":
        datasamples = dbt.check_JobAllocation(cursor,n)
    elif e == "execution":
        datasamples = dbt.check_JobExecution(cursor,n)
    elif e == "read":
        datasamples = dbt.check_FileRead(cursor,n)
    elif e == "write":
        datasamples = dbt.check_FileWrite(cursor,n)
    elif e == "transfer":
        datasamples = dbt.check_FileTransfer(cursor,n)
    else:
        datasamples = dbt.check_All(cursor, m)
    return datasamples

def checksql(cursor: sqlite3.Cursor, sql: str) -> bool:
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        # 1) no rows at all
        if len(rows) == 0:
            print("Empty result set. Skip.")
            return False

        # 2) single scalar count(*) = 0
        if len(rows) == 1 and len(rows[0]) == 1 and rows[0][0] == 0:
            print("Count is zero. Skip.")
            return False

        # 3) rows exist but all values are NULL
        if all(all(v is None for v in row) for row in rows):
            print("All results are NULL. Skip.")
            return False

    except Exception:
        print("This SQL is invalid. Skip.")
        return False

    return True

def Check():
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    check_allsql(cursor, output_Q)

    cursor.close()
    conn.close()
    return

def site_ques_gen(rounds: int = 50, vague: float = 0.1):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    f = open(output_Q, 'a', encoding="utf-8")
    for i in range(rounds):
        print("GENERATING #", i)
        datasamples = random_pick(cursor)
        roll = random.random()
        if roll > vague:
            response_text = llm_general_questions(datasamples)
        else:
            response_text = llm_general_questions(datasamples, vague=True)
        check_result = getattr(dbt, response_text["check_tool"])(cursor)
        response_text2 = llm_sql(response_text["user_question"], response_text["reason_check"], response_text["check_tool"], check_result)
        
        if response_text and response_text2 and checksql(cursor, response_text2["sql"]):
            f.write(json.dumps({**response_text, **response_text2}) + "\n")
        else:
            print("SQL PROBLEMATIC, SKIPPING THIS DATA")
        print("")
    f.close()

    cursor.close()
    conn.close()


def jobid_ques_gen(rounds: int = 50, vague: float = 0.1):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    f = open(output_Q, 'a', encoding="utf-8")
    for i in range(rounds):
        print("GENERATING JOB ID QA #", i)
        datasamples = dbt.random_JobID(cursor)
        roll = random.random()
        if roll>vague:
            response_text = llm_jobid_questions(datasamples)
        else:
            response_text = llm_jobid_questions(datasamples, vague=True)
        check_result = getattr(dbt, response_text["check_tool"])(cursor)
        response_text2 = llm_sql(response_text["user_question"], response_text["reason_check"], response_text["check_tool"], check_result)
        
        if response_text and response_text2 and checksql(cursor, response_text2["sql"]):
            f.write(json.dumps({**response_text, **response_text2}) + "\n")
        else:
            print("SQL PROBLEMATIC, SKIPPING THIS DATA")
        print("")
    f.close()

    cursor.close()
    conn.close()

# def sql_ans_gen():
#     conn = sqlite3.connect(dbpath)
#     cursor = conn.cursor()

#     f1 = open(output_Q, 'r', encoding="utf-8")
#     f2 = open(output_QA, "a", encoding="utf-8")

#     for i, line in enumerate(f1):
#         print(f"Generating Answer #{i}")
#         datasamples = json.loads(line.strip())

#         ans = llm_generate_answers(datasamples, cursor)
#         if ans.startswith("__ANSWER__"):
#             datasamples["answer"] = ans.split("__ANSWER__")[1].strip()
#         elif ans.startswith("__NULL_RESULT__"):
#             print("Problematic SQL Execution")
#             datasamples["answer"] = "__NULL_RESULT__"
#         else:
#             print("Problematic AI API Calling")
#             datasamples["answer"] = "__NULL_RESULT__"
#         f2.write(json.dumps(datasamples) + "\n")

#     cursor.close()
#     conn.close()

def sql_ans_gen(start_row: int = 1):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    f1 = open(output_Q, "r", encoding="utf-8")

    for i, line in enumerate(f1):
        if (i < start_row-1):
            continue
        print(f"Generating Answer #{i}")

        datasamples = json.loads(line.strip())
        ans = llm_generate_answers(datasamples, cursor)

        if ans == "__SQL_ERROR__":
            print("Already written to SQLerror file.\n")
            continue

        if ans.startswith("__ANSWER__"):
            datasamples["answer"] = ans.split("__ANSWER__", 1)[1].strip()
            write_jsonl(output_QA_ready, datasamples)

            print("READY DATA WRITTEN.")
            print("User Question:", datasamples.get("user_question"))
            print("Answer:", datasamples["answer"])
            print("")
            continue

        if ans.startswith("__NULL_RESULT__"):
            datasamples["answer"] = "__NULL_RESULT__"
            write_jsonl(output_QA_null, datasamples)

            print("NULL RESULT. Written to NULLanswer file.")
            print("User Question:", datasamples.get("user_question"))
            print("")
            continue

        if ans.startswith("__INCOMPLETE_RESULT__"):
            datasamples["answer"] = ans.strip()
            write_jsonl(output_QA_incomplete, datasamples)

            print("INCOMPLETE RESULT. Written to INCOMPLETEanswer file.")
            print("User Question:", datasamples.get("user_question"))
            print("Answer:", datasamples["answer"])
            print("")
            continue

        datasamples["answer"] = "__INCOMPLETE_RESULT__ Answer format is not recognized."
        datasamples["raw_answer_output"] = ans
        write_jsonl(output_QA_incomplete, datasamples)

        print("UNRECOGNIZED ANSWER FORMAT. Written to INCOMPLETEanswer file.")
        print("User Question:", datasamples.get("user_question"))
        print("Raw Answer:", ans)
        print("")

    f1.close()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    jobid_ques_gen(400, 0.1)
    site_ques_gen(100, 0.1)
    sql_ans_gen(499)