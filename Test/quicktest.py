import json
import torch
import os
import sys
import sqlite3
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

scratch = os.environ.get("PSCRATCH")
if scratch:
    currdir = Path(scratch) / "CGSimFinetune" / "Test"
else:
    currdir = Path(__file__).parent

trainpath = currdir.parent / "resources" / "AI_QA_TrainData.jsonl"
dbpath = currdir.parent / "resources" / "CGsimSite.db"

sys.path.append(str(currdir.parent / "Tools"))
import DBTool as dbt

base_model_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"

checkpoint_path = currdir.parent / "run" / "nemotron-llama8b-CGsim-HighQual" / "checkpoint-250"
if not checkpoint_path.exists():
    raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")


def load_toolmeta():
    '''
    Load tool meta data for system prompts.
    '''
    with open(str(trainpath), "r") as f:
        toolmeta = json.loads(f.readline().strip())["tools"]
    return toolmeta


def gen_new_text(model, tokenizer, messages):
    toolmeta = load_toolmeta()
    prompt = tokenizer.apply_chat_template(
      messages,
      tools=toolmeta,
      tokenize=False,
      add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            pad_token_id=tokenizer.eos_token_id,
            max_new_tokens=256,
            do_sample=False,
        )

    prompt_len = inputs["input_ids"].shape[1]
    new_ids = out[0][prompt_len:]
    return tokenizer.decode(new_ids, skip_special_tokens=False)


def extract_toolcall_block(text: str):
    s = text.find("<TOOLCALL>[")
    if s == -1:
        return "", None
    e = text.find("]</TOOLCALL>", s)
    if e == -1:
        return "", None

    array_json = text[s + len("<TOOLCALL>") : e + 1]
    toolcall_block = json.loads(array_json)[0] # dict

    return text[:s], toolcall_block


def load_QModel(base_model_id: str):
    '''
    Load Quantized Model.
    reference: https://huggingface.co/docs/peft/developer_guides/quantization
    '''
    config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id, 
        quantization_config=config,
        device_map = "auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True)

    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    ft_model = PeftModel.from_pretrained(base_model, checkpoint_path, is_trainable=False)
    ft_model.eval()
    ft_model.config.use_cache = True

    print("Model Default Temperature : ", ft_model.generation_config.temperature)
    print("Model Default Top P : ",ft_model.generation_config.top_p)
    print("Model Default Top K : ", ft_model.generation_config.top_k)

    # summary of GPU resource after loading
    print("allocated GiB:", torch.cuda.memory_allocated()/1024**3)
    print("reserved  GiB:", torch.cuda.memory_reserved()/1024**3)
    print("is_loaded_in_4bit:", getattr(ft_model, "is_loaded_in_4bit", None))
    print("is_loaded_in_8bit:", getattr(ft_model, "is_loaded_in_8bit", None))

    return ft_model, tokenizer


def ask_cgsim(model, tokenizer, cursor, question, max_rounds=6):
    print("Question: ", question, "\n")
    messages = [
      {'role': 'system',
      'content': 'You are a CGsim agent. Answer questions related to grid simulation related questions. Use tools when needed.'},
      {'role': 'user',
      'content': question}]

    for step in range(max_rounds):
        gen_text = gen_new_text(model, tokenizer, messages)
        messages.append({'role': 'assistant', 'content': gen_text})

        think, toolcall_block = extract_toolcall_block(gen_text)
        if toolcall_block is None:
            print("Answer \n", gen_text.split("<eot_id>")[0])
            print("Finished \n")
            return {'answer': gen_text.split("<eot_id>")[0], 'messages': messages}

        tool_name = toolcall_block["name"]
        tool_args = ""

        if tool_name.startswith("check_"):
            tool_result = getattr(dbt, tool_name)(cursor)
        elif tool_name == ("execute_sql"):
            tool_args = toolcall_block["arguments"]["sql"]
            tool_result = dbt.execute_sql(cursor, tool_args)
        else:
            raise Exception(f"Unknown tool name: {tool_name}")

        print("Thinking \n", think, "\n")
        print("Tool Call \n", tool_name, tool_args, "\n")
        messages.append({'role': 'tool', 'content': json.dumps(tool_result, ensure_ascii=False)})

    return {'answer': None, 'messages': messages}

def main():
    ft_model, tokenizer = load_QModel(base_model_id)
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    
    ans1 = ask_cgsim(ft_model, tokenizer, cursor, "For job 9590968381, what was the average transfer rate for all the successful data movements that originated from AGLT2_site_4?")
    ans2 = ask_cgsim(ft_model, tokenizer, cursor, "Could you rank the different sites by the total volume of data they successfully read from their local storage?")
    ans3 = ask_cgsim(ft_model, tokenizer, cursor, "What is the possible reason that execution of job 8774052003 takes so long time, could you please explain?")
    
    cursor.close()
    conn.close()
    return

if __name__ == "__main__":
    main()
