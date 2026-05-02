import json
from FineTune import FINETUNE_DIR

def config_loader(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return json.load(f)

FINETUNE_CONFIG = config_loader(str(FINETUNE_DIR / "config.jsonl"))
STEP_1_CONFIG = FINETUNE_CONFIG["STEP_1"]
STEP_2_CONFIG = FINETUNE_CONFIG["STEP_2"]
STEP_3_CONFIG = FINETUNE_CONFIG["STEP_3"]
MERGE_N_UPLOAD = FINETUNE_CONFIG["MERGE_N_UPLOAD"]