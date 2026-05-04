import os
import json
from Deployment import DEPLOYMENT_DIR

def config_loader(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return json.load(f)

CONFIG_NAME = os.environ.get("DEPLOY_CONFIG", "config_CoT.json")
CONFIG_PATH = DEPLOYMENT_DIR / CONFIG_NAME
BENCHMARK_CONFIG = config_loader(str(CONFIG_PATH))

print("BENCHMARK_CONFIG: ", str(CONFIG_PATH))

HIGHQUAL_BENCH = BENCHMARK_CONFIG["HIGHQUAL_BENCH"]
WL_BENCH = BENCHMARK_CONFIG["WL_BENCH"]