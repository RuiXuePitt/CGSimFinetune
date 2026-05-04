"""
Test Fine Tuned LLM Model: Base Model + LoRA Adapter
Rui XUE
"""
import os
import sys
import json
import time
import sqlite3
import requests
import numpy as np
import traceback
from pathlib import Path

# ============================================================
# Project path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

import Tools.DBTool as dbt

# ============================================================
# Hugging Face cache
# ============================================================

pscratch = os.environ["PSCRATCH"]

os.environ["HF_HOME"] = str(Path(pscratch) / ".hf")
os.environ["HF_HUB_CACHE"] = str(Path(pscratch) / ".hf" / "hub")

from transformers import AutoTokenizer

# ============================================================
# Config
# ============================================================

repo_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"
tokenizer = AutoTokenizer.from_pretrained(repo_id)

RESOURCE_DIR = Path(pscratch) / "resources"
OUTPUT_DIR = RESOURCE_DIR / "Benchmark_OnlySQL" / "Benchmark-Checkpoint-210" / "test_bench"

TESTDATA_PATH = RESOURCE_DIR / "test_AI_QA_Gen.jsonl"
DB_PATH = RESOURCE_DIR / "CGSimSite.db"

GENRES_PATH = OUTPUT_DIR / "generate_result.jsonl"
ERROR_PATH = OUTPUT_DIR / "error_msg.jsonl"
BENCHMARK_REPORT_PATH = OUTPUT_DIR / "benchmark_report.txt"

VLLM_INFO_PATH = Path(pscratch) / "FineTunedLLM_V1_vllm.env"

MAX_ROUNDS = 6
MAX_TOKENS = 1024
TEMPERATURE = 0
TOP_P = 1.0
REQUEST_TIMEOUT = 180

SYSTEM_PROMPT = "You are a CGsim agent. Answer questions related to grid simulation related questions. Use SQL queries and information got from SQL to help answer the question."

# ============================================================
# Error class
# ============================================================

class CGSimRunError(Exception):
    def __init__(self, error_type: str, message: str, **extra):
        super().__init__(message)
        self.error_type = error_type
        self.extra = extra


# ============================================================
# IO helpers
# ============================================================

def load_info_file(filepath: Path) -> dict:
    env = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def load_testcases(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)
            question = obj.get("user_question")

            if not question:
                raise ValueError(f"Cannot find question field at line {idx}: {obj}")

            yield idx, question, obj


def log_error(
    user_request: str,
    messages: list,
    last_model_output: str | None,
    error_type: str,
    error_message: str,
    step: int | None = None,
    extra: dict | None = None,
):
    ERROR_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "user_request": user_request,
        "step": step,
        "error_type": error_type,
        "error_message": error_message,
        "last_model_output": last_model_output,
        "messages": messages,
        "extra": extra or {},
    }

    with open(ERROR_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


# ============================================================
# Prompt + vLLM
# ============================================================

def get_prompt(messages: list) -> str:

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    return prompt


def poster(prompt: str) -> tuple[str, dict]:
    file_info = load_info_file(VLLM_INFO_PATH)

    url = file_info["BASE_URL"].rstrip("/") + "/completions"
    model = file_info["MODEL_NAME"]

    try:
        t0 = time.time()

        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": prompt,
                "top_p": TOP_P,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
            },
            timeout=REQUEST_TIMEOUT,
        )

        elapsed = time.time() - t0
        response.raise_for_status()

    except requests.RequestException as e:
        raise CGSimRunError(
            "HTTP_ERROR",
            str(e),
            url=url,
        )

    try:
        data = response.json()
        choice = data["choices"][0]

        text = choice.get("text", "")
        finish_reason = choice.get("finish_reason", None)

        meta = {
            "elapsed": elapsed,
            "finish_reason": finish_reason,
            "usage": data.get("usage", None),
        }

        return text, meta

    except Exception as e:
        raise CGSimRunError(
            "VLLM_RESPONSE_PARSE_ERROR",
            str(e),
            raw_response=response.text,
        )


def gen_new_text(messages: list) -> tuple[str, dict]:
    prompt = get_prompt(messages)
    return poster(prompt)


# ============================================================
# Tool call parser
# ============================================================

def clean_sql_output(text: str) -> str:
    text = text.strip()

    # remove possible special tokens
    text = text.split("<eot_id>")[0].strip()
    text = text.split("<|eot_id|>")[0].strip()

    # remove markdown fences
    if text.startswith("```"):
        lines = text.splitlines()

        # remove first ```sql or ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        # remove last ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # optional: keep only from first SELECT
    upper = text.upper()
    idx = upper.find("SELECT")
    if idx != -1:
        text = text[idx:].strip()

    return text


# ============================================================
# SQL result checks
# ============================================================

def is_empty_sql_result(result) -> bool:
    if result is None:
        return True

    if isinstance(result, str):
        return len(result.strip()) == 0

    if isinstance(result, (list, tuple, set)):
        return len(result) == 0

    if isinstance(result, dict):
        if len(result) == 0:
            return True

        for key in ["rows", "data", "result", "results"]:
            if key in result and isinstance(result[key], (list, tuple)):
                return len(result[key]) == 0

    return False


def looks_like_sql_error_result(result) -> bool:
    text = json.dumps(result, ensure_ascii=False, default=str).lower()

    error_markers = [
        "no such column",
        "no such table",
        "syntax error",
        "operationalerror",
        "sqlite error",
        "ambiguous column",
        "misuse of aggregate",
        "near ",
    ]

    return any(marker in text for marker in error_markers)


# ============================================================
# Main agent loop
# ============================================================

def test_ask_cgsim_finetuned_onlySQL(
    usr_request: str,
    cursor,
):
    print("=" * 100)
    print("USER REQUEST:")
    print(usr_request)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": usr_request,
        },
    ]

    last_model_output = None

    try:
        # ============================================================
        # Round 1: generate SQL
        # ============================================================
        sql_text, meta = gen_new_text(messages)
        last_model_output = sql_text

        print("RAW SQL GEN TEXT:")
        print(sql_text)
        print("GEN META:")
        print(meta)

        if meta.get("finish_reason") == "length":
            raise CGSimRunError(
                "SQL_GENERATION_LENGTH_CUTOFF",
                "vLLM stopped because max_tokens was reached during SQL generation.",
                finish_reason=meta.get("finish_reason"),
                max_tokens=MAX_TOKENS,
                raw_text=sql_text,
            )

        sql = clean_sql_output(sql_text)

        if not sql:
            raise CGSimRunError(
                "EMPTY_SQL",
                "Model generated empty SQL.",
                raw_text=sql_text,
            )

        print("SQL:")
        print(sql)

        messages.append(
            {
                "role": "assistant",
                "content": sql,
            }
        )

        # ============================================================
        # Execute SQL
        # ============================================================
        try:
            sql_result = dbt.execute_sql(cursor, sql)
        except sqlite3.Error as e:
            raise CGSimRunError(
                "SQL_EXECUTION_ERROR",
                str(e),
                sql=sql,
                raw_text=sql_text,
            )
        except Exception as e:
            raise CGSimRunError(
                "SQL_TOOL_RUNTIME_ERROR",
                str(e),
                sql=sql,
                raw_text=sql_text,
            )

        if looks_like_sql_error_result(sql_result):
            raise CGSimRunError(
                "SQL_HALLUCINATION_OR_EXECUTION_ERROR",
                "SQL result appears to contain an execution/schema error.",
                sql=sql,
                sql_result=sql_result,
            )

        if is_empty_sql_result(sql_result):
            raise CGSimRunError(
                "SQL_EMPTY_RESULT",
                "SQL executed but returned empty result.",
                sql=sql,
                sql_result=sql_result,
            )

        print("SQL RESULT:")
        print(sql_result)

        # ============================================================
        # Round 2: generate final answer from SQL result
        # ============================================================
        messages.append(
            {
                "role": "tool",
                "content": json.dumps(sql_result, ensure_ascii=False, default=str),
            }
        )

        answer_text, meta2 = gen_new_text(messages)
        last_model_output = answer_text

        print("RAW ANSWER GEN TEXT:")
        print(answer_text)
        print("GEN META:")
        print(meta2)

        if meta2.get("finish_reason") == "length":
            raise CGSimRunError(
                "ANSWER_GENERATION_LENGTH_CUTOFF",
                "vLLM stopped because max_tokens was reached during answer generation.",
                finish_reason=meta2.get("finish_reason"),
                max_tokens=MAX_TOKENS,
                raw_text=answer_text,
            )

        answer = answer_text.split("<eot_id>")[0].strip()

        if not answer:
            raise CGSimRunError(
                "EMPTY_FINAL_ANSWER",
                "Model generated empty final answer.",
                raw_text=answer_text,
            )

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        print("FINAL ANSWER:")
        print(answer)

        return {
            "success": True,
            "sql": sql,
            "sql_result": sql_result,
            "answer": answer,
            "messages": messages,
            "elapsed": meta.get("elapsed") + meta2.get("elapsed")
        }

    except CGSimRunError as e:
        log_error(
            user_request=usr_request,
            messages=messages,
            last_model_output=last_model_output,
            error_type=e.error_type,
            error_message=str(e),
            step=None,
            extra=e.extra,
        )

        print(f"[FAILED] {e.error_type}: {e}")

        return {
            "success": False,
            "sql": e.extra.get("sql"),
            "answer": None,
            "messages": messages,
            "error_type": e.error_type,
            "error_message": str(e),
        }

    except Exception as e:
        log_error(
            user_request=usr_request,
            messages=messages,
            last_model_output=last_model_output,
            error_type="UNEXPECTED_ERROR",
            error_message=str(e),
            step=None,
            extra={"traceback": traceback.format_exc()},
        )

        print(f"[FAILED] UNEXPECTED_ERROR: {e}")

        return {
            "success": False,
            "sql": None,
            "answer": None,
            "messages": messages,
            "error_type": "UNEXPECTED_ERROR",
            "error_message": str(e),
        }


# ============================================================
# Benchmark main
# ============================================================

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    n_total = 0
    n_success = 0
    t_success = 0.0
    n_failed = 0

    error_counter = {}

    gen_output = open(GENRES_PATH, 'w')

    try:
        for idx, usr_request, raw_case in load_testcases(TESTDATA_PATH):
            print("=" * 100)
            print(f"TESTCASE {idx}")

            n_total += 1

            result = test_ask_cgsim_finetuned_onlySQL(usr_request, cursor)

            if result["success"]:
                n_success += 1
                t_success += result["elapsed"]
                success_execute = {"user_question": usr_request, "sql": result["sql"], "answer": result["answer"]}
                gen_output.write(json.dumps(success_execute, ensure_ascii=False, default=str) + "\n")
            else:
                n_failed += 1
                err = result.get("error_type", "UNKNOWN")
                error_counter[err] = error_counter.get(err, 0) + 1

        success_rate = n_success*1.0/n_total
        p68_cl = np.sqrt( success_rate*(1-success_rate)/n_total )

        print("=" * 100)
        print("BENCHMARK SUMMARY")
        print(f"Total:   {n_total}")
        print(f"Success: {n_success}")
        print(f"Success rate: ({success_rate*100:.2f} ± {p68_cl*100:.2f})%")
        print(f"Average Time for Succeeded Generation: {t_success/n_success} s")
        print(f"Failed:  {n_failed}")
        print("Error breakdown:")
        for k, v in sorted(error_counter.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")
        print(f"Errors written to: {ERROR_PATH}")
        print(f"Benchmark Report written to: {BENCHMARK_REPORT_PATH}")
        
        with open(str(BENCHMARK_REPORT_PATH), 'w') as f:
            f.write("BENCHMARK SUMMARY\n")
            f.write(f"Input TestCase: {TESTDATA_PATH}\n")
            f.write(f"Total:   {n_total}\n")
            f.write(f"Success: {n_success}\n")
            f.write(f"Success rate: ({success_rate*100:.2f} ± {p68_cl*100:.2f})% ")
            f.write(f"Average Time for Succeeded Generation: {t_success/n_success} s\n")
            f.write(f"Failed: {n_failed}\n")
            f.write("Error breakdown:\n")
            for k, v in sorted(error_counter.items(), key=lambda x: -x[1]):
                f.write(f"  {k}: {v}\n")
            f.write(f"Errors written to: {ERROR_PATH}\n")

    finally:
        cursor.close()
        conn.close()

    gen_output.close()

if __name__ == "__main__":
    main()