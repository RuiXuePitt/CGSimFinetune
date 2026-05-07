import os
import json
from FineTune import FINETUNE_DIR

def config_loader(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return json.load(f)

CONFIG_NAME = os.environ.get("FINETUNE_CONFIG", "config_CoT.json")
CONFIG_PATH = FINETUNE_DIR / CONFIG_NAME
FINETUNE_CONFIG = config_loader(str(CONFIG_PATH))

print("\n","=="*10)
print("FINETUNE CONFIG: ", str(CONFIG_PATH))

STEP_1_CONFIG = FINETUNE_CONFIG["STEP_1"]
STEP_2_CONFIG = FINETUNE_CONFIG["STEP_2"]
STEP_3_CONFIG = FINETUNE_CONFIG.get("STEP_3")
MERGE_N_UPLOAD = FINETUNE_CONFIG.get("MERGE_N_UPLOAD")