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
from Deployment.config_loader import DEPLOYMENT_DIR, BENCHMARK_CONFIG, HIGHQUAL_BENCH

# ============================================================
# Project path
# ============================================================

PROJECT_ROOT = DEPLOYMENT_DIR.resolve().parent
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

REPOID = HIGHQUAL_BENCH["BASE_MODEL"]
tokenizer = AutoTokenizer.from_pretrained(REPOID)

RESOURCE_DIR = Path(os.path.expandvars(HIGHQUAL_BENCH["RESOURCE_DIR"]))
OUTPUT_DIR = RESOURCE_DIR / HIGHQUAL_BENCH["BENCH_VER"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

TESTDATA_PATH = RESOURCE_DIR / BENCHMARK_CONFIG["TESTDATA"]
DB_PATH = RESOURCE_DIR / BENCHMARK_CONFIG["DB"]
TOOL_PATH = RESOURCE_DIR / BENCHMARK_CONFIG["TOOLPROMPT"]
GENRES_PATH = OUTPUT_DIR / BENCHMARK_CONFIG["SUCCESS_RES"]
ERROR_PATH = OUTPUT_DIR / BENCHMARK_CONFIG["ERR_MSG"]
BENCHMARK_REPORT_PATH = OUTPUT_DIR / BENCHMARK_CONFIG["BENCH_REPORT"]

VLLM_INFO_PATH = Path(pscratch) / HIGHQUAL_BENCH["VLLM_INFO_PATH"]
print(VLLM_INFO_PATH)

MAX_ROUNDS = 6
MAX_TOKENS = 1024
TEMPERATURE = 0
TOP_P = 1.0
REQUEST_TIMEOUT = 180

SYSTEM_PROMPT = BENCHMARK_CONFIG["SYSTEM_PROMPT"]

# ============================================================
# Error class
# ============================================================

class CGSimRunError(Exception):
    def __init__(self, error_type: str, message: str):
        super().__init__(message)
        self.error_type = error_type


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


def get_tool_info() -> list:
    with open(TOOL_PATH, "r", encoding="utf-8") as f:
        line = f.readline()
        return json.loads(line)["tools"]


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
    step: int | None = None
):
    ERROR_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "user_request": user_request,
        "step": step,
        "error_type": error_type,
        "error_message": error_message,
        "last_model_output": last_model_output,
        "messages": messages
    }

    with open(ERROR_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


# ============================================================
# Prompt + vLLM
# ============================================================

def get_prompt(messages: list) -> str:
    tool_prompt = get_tool_info()

    prompt = tokenizer.apply_chat_template(
        messages,
        tools=tool_prompt,
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
            str(e)
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
            str(e)
        )


def gen_new_text(messages: list) -> tuple[str, dict]:
    prompt = get_prompt(messages)
    return poster(prompt)


# ============================================================
# Tool call parser
# ============================================================

def extract_toolcall_block(text: str):
    s = text.find("<TOOLCALL>[")
    if s == -1:
        return text, None

    e = text.find("]</TOOLCALL>", s)
    if e == -1:
        raise CGSimRunError(
            "TOOLCALL_TAG_UNCLOSED",
            "Found <TOOLCALL>[ but no closing ]</TOOLCALL>."
        )

    array_json = text[s + len("<TOOLCALL>"): e + 1]

    try:
        calls = json.loads(array_json)
    except json.JSONDecodeError as err:
        raise CGSimRunError(
            "TOOLCALL_JSON_ERROR",
            str(err)
        )

    if not isinstance(calls, list):
        raise CGSimRunError(
            "TOOLCALL_NOT_LIST",
            "Tool call block is not a JSON list."
        )

    if len(calls) == 0:
        raise CGSimRunError(
            "EMPTY_TOOLCALL",
            "Model generated <TOOLCALL>[]</TOOLCALL>."
        )

    toolcall_block = calls[0]

    if not isinstance(toolcall_block, dict):
        raise CGSimRunError(
            "TOOLCALL_NOT_DICT",
            "First tool call is not a JSON object."
        )

    return text[:s], toolcall_block


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

def test_ask_cgsim_finetuned(usr_request: str, cursor, max_rounds: int = MAX_ROUNDS):
    print("=" * 100)
    print("USER REQUEST:")
    print(usr_request)

    sql = ""
    checktool = ""

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
    seen_toolcalls = set()

    try:
        elapsed_time = 0.0
        for step in range(max_rounds):
            gen_text, meta = gen_new_text(messages)
            elapsed_time += meta.get("elapsed",0.0)
            last_model_output = gen_text

            messages.append(
                {
                    "role": "assistant",
                    "content": gen_text,
                }
            )

            print("RAW GEN TEXT:")
            print(gen_text)
            # print("GEN META:")
            # print(meta)

            # Important: vLLM generation loop / cutoff detection
            if meta.get("finish_reason") == "length":
                raise CGSimRunError(
                    "GENERATION_LENGTH_CUTOFF",
                    (
                        "vLLM stopped because max_tokens was reached. "
                        "The model likely entered a long reasoning loop or failed to terminate."
                    )
                )

            think, toolcall_block = extract_toolcall_block(gen_text)

            if toolcall_block is None:
                answer = gen_text.split("<eot_id>")[0].strip()

                if not answer:
                    raise CGSimRunError(
                        "EMPTY_FINAL_ANSWER",
                        "No tool call and empty final answer."
                    )

                print("FINAL ANSWER:")
                print(answer)

                print("\n", "=="*10)
                print("=="*5, "Full Messages", "=="*5)
                print(messages)

                return {
                    "success": True,
                    "checktool": checktool,
                    "sql": sql,
                    "answer": answer,
                    "messages": messages,
                    "elapsed": elapsed_time
                }

            if "name" not in toolcall_block:
                raise CGSimRunError(
                    "TOOLCALL_MISSING_NAME",
                    "Tool call does not contain key 'name'."
                )

            tool_name = toolcall_block["name"]
            tool_args = ""

            # Detect repeated toolcall loop
            toolcall_signature = json.dumps(toolcall_block, sort_keys=True, ensure_ascii=False)
            if toolcall_signature in seen_toolcalls:
                raise CGSimRunError(
                    "REPEATED_TOOLCALL_LOOP",
                    "The model repeated the same tool call, likely stuck in a tool-use loop."
                )
            seen_toolcalls.add(toolcall_signature)

            if tool_name.startswith("check_"):
                checktool = tool_name
                if not hasattr(dbt, tool_name):
                    raise CGSimRunError(
                        "UNKNOWN_CHECK_TOOL",
                        f"Unknown check tool: {tool_name}"
                    )

                tool_result = getattr(dbt, tool_name)(cursor)

            elif tool_name == "execute_sql":
                try:
                    tool_args = toolcall_block["arguments"]["sql"]
                    sql = tool_args
                except Exception:
                    raise CGSimRunError(
                        "SQL_ARGUMENT_ERROR",
                        "execute_sql tool call does not contain arguments.sql."
                    )

                # print("SQL:")
                # print(tool_args)

                try:
                    tool_result = dbt.execute_sql(cursor, tool_args)
                except sqlite3.Error as e:
                    raise CGSimRunError(
                        "SQL_EXECUTION_ERROR",
                        str(e)
                    )
                except Exception as e:
                    raise CGSimRunError(
                        "SQL_TOOL_RUNTIME_ERROR",
                        str(e)
                    )

                if looks_like_sql_error_result(tool_result):
                    raise CGSimRunError(
                        "SQL_HALLUCINATION_OR_EXECUTION_ERROR",
                        "SQL result appears to contain an execution/schema error."
                    )

                if is_empty_sql_result(tool_result):
                    raise CGSimRunError(
                        "SQL_EMPTY_RESULT",
                        "SQL executed but returned empty result."
                    )

            else:
                raise CGSimRunError(
                    "UNKNOWN_TOOL",
                    f"Unknown tool name: {tool_name}"
                )

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                }
            )

        raise CGSimRunError(
            "MAX_ROUNDS_EXCEEDED",
            f"Exceeded max_rounds={max_rounds}.",
        )

    except CGSimRunError as e:
        log_error(
            user_request=usr_request,
            messages=messages,
            last_model_output=last_model_output,
            error_type=e.error_type,
            error_message=str(e),
            step=step if "step" in locals() else None
        )

        print(f"[FAILED] {e.error_type}: {e}")

        return {
            "success": False,
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
            step=step if "step" in locals() else None
        )

        print(f"[FAILED] UNEXPECTED_ERROR: {e}")

        return {
            "success": False,
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

            result = test_ask_cgsim_finetuned(usr_request, cursor)

            if result["success"]:
                n_success += 1
                t_success += result["elapsed"]
                success_execute = {"user_question": usr_request, "checktool": result["checktool"], "sql": result["sql"], "answer": result["answer"]}
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


if __name__ == "__main__":
    main()