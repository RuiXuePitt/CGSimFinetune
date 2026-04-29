import os
from pathlib import Path
pscratch = os.environ["PSCRATCH"]
os.environ["HF_HOME"]=str(Path(pscratch)/".hf")
hf_home = os.environ["HF_HOME"]
os.environ["HF_HUB_CACHE"] = str(Path(hf_home) / "hub")

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

def merge_and_push_model():
    base_model_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"
    adapter_path = os.path.expandvars("${HOME}/run/nemotron-llama8b-CGsim/checkpoint-250")
    print("Adapter From: ", adapter_path)
    repo_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim-FineTuneV1"
    commit = "Fine Tune Nemotron V1 (Tool Call, SQL Query, Answer)"

    tokenizer = AutoTokenizer.from_pretrained(base_model_id)

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    model = PeftModel.from_pretrained(
        base_model,
        adapter_path,
    )

    model = model.merge_and_unload()
    model.push_to_hub(repo_id, commit_message=commit)
    tokenizer.push_to_hub(repo_id)

if __name__ == "__main__":
    merge_and_push_model()
