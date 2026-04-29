import os, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
import Tools.DBTool as dbt

pscratch = os.environ["PSCRATCH"]
os.environ["HF_HOME"]=str(Path(pscratch)/".hf")
hf_home = os.environ["HF_HOME"]
os.environ["HF_HUB_CACHE"] = str(Path(hf_home) / "hub")

import json, time, sqlite3, requests
from transformers import AutoTokenizer

repo_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim-FineTuneV1"
tokenizer = AutoTokenizer.from_pretrained(repo_id)

test_path = str(Path(pscratch) / "resources" / "test_AI_QA_Gen.jsonl")
db_path = str(Path(pscratch) / "resources" / "CGSimSite.db")

def get_tool_info() -> list:
    with open(str(Path(pscratch) / "resources" / "tool_prompt.jsonl"), 'r') as f:
        line = f.readline()
        tool_prompt = json.loads(line)["tools"]
    return tool_prompt

def get_prompt(messages):
    tool_prompt = get_tool_info()
    prompt = tokenizer.apply_chat_template(
      messages,
      tools=tool_prompt,
      tokenize=False,
      add_generation_prompt=True,
    )
    return prompt

def loadInfoFile(filepath: str) -> dict:
    '''
    load information file from LLM deployment
    1. GPU_NODE
    2. PORT
    3. BASE_URL
    4. MODEL_NAME
    '''
    env = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env[key] = value
    return env

def poster(prompt):
    fileInfo = loadInfoFile(str(Path(pscratch) / "FineTunedLLM_V1_vllm.env"))
    # have already applied chat template, go to /completions port
    url = fileInfo["BASE_URL"]+"/completions"
    model = fileInfo["MODEL_NAME"]
    response = requests.post(
        url,
        json = {
            "model": model,
            "prompt": prompt,
            "top_p": 1.0,
            "max_tokens": 1024, #maxoutput
            "temperature": 0,
        },
    )
    resp_text = response.json()["choices"][0]["text"]
    return resp_text


def gen_new_text(messages):
    prompt = get_prompt(messages)
    resp_text = poster(prompt)
    return resp_text


def extract_toolcall_block(text: str):
    s = text.find("<TOOLCALL>[")
    if s == -1:
        return "", None
    e = text.find("]</TOOLCALL>", s)
    if e == -1:
        return "", None

    array_json = text[s + len("<TOOLCALL>") : e + 1]

    print("ARRAY JSON: \n", array_json)

    # This part should add insurance!
    # record those cannot work, with wrong responses and errors
    # toolcall_block = json.loads(array_json)[0] # dict

    try:
        toolcall_block = json.loads(array_json)[0]
    except json.JSONDecodeError:
        fixed = array_json.replace('{"}}', '{}}')
        toolcall_block = json.loads(fixed)[0]
    
    return text[:s], toolcall_block


def test_ask_cgsim_finetuned(usr_request, cursor, max_rounds=6):
    print("USER REQUEST: \n", usr_request)
    messages = [
        {'role': 'system',
        'content': 'You are a CGsim agent. Answer questions related to grid simulation related questions. Use tools when needed.'},
        {'role': 'user',
        'content': usr_request}]

    for step in range(max_rounds):
        gen_text = gen_new_text(messages)
        messages.append({'role': 'assistant', 'content': gen_text})

        print("RAW GEN TEXT: \n", gen_text)

        think, toolcall_block = extract_toolcall_block(gen_text)
        if toolcall_block is None:
            print("Answer \n", gen_text.split("<eot_id>")[0])
            return {'answer': gen_text.split("<eot_id>")[0], 'messages': messages}

        tool_name = toolcall_block["name"]
        tool_args = ""

        if tool_name.startswith("check_"):
            tool_result = getattr(dbt, tool_name)(cursor)
        elif tool_name == ("execute_sql"):
            tool_args = toolcall_block["arguments"]["sql"]
            print(tool_args)
            tool_result = dbt.execute_sql(cursor, tool_args)
        else:
            raise Exception(f"Unknown tool name: {tool_name}")

        # print("Thinking \n", think, "\n")
        # print("Tool Call \n", tool_name, tool_args, "\n")
        messages.append({'role': 'tool', 'content': json.dumps(tool_result, ensure_ascii=False)})

    return {'answer': None, 'messages': messages}

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    usr_request = "During execution of job 2794720992, what is the total queue time?"
    test_ask_cgsim_finetuned(usr_request, cursor)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()