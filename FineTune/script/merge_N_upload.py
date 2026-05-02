import os
from pathlib import Path
from FineTune.config_loader import MERGE_N_UPLOAD

pscratch = os.environ["PSCRATCH"]
os.environ["HF_HOME"]=str(Path(pscratch)/".hf")
hf_home = os.environ["HF_HOME"]
os.environ["HF_HUB_CACHE"] = str(Path(hf_home) / "hub")

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

def merge_and_push_model():
    base_model_id = MERGE_N_UPLOAD["BASE_MODEL"]
    adapter_path = os.path.expandvars(MERGE_N_UPLOAD["LORA_ADAPTER"])
    print("Adapter From: ", adapter_path)
    repo_id = MERGE_N_UPLOAD["NEW_MODEL_NAME"]
    commit = MERGE_N_UPLOAD["COMMIT"]

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
