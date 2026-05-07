"""
Check the template and mask are working as expected.

Rui XUE
"""

import os
import sys
import FineTune.traintools as tt
from FineTune.config_loader import STEP_1_CONFIG
from pathlib import Path

pscratch = os.environ["PSCRATCH"]
os.environ["HF_HOME"] = str(Path(pscratch) / ".hf")
os.environ["HF_HUB_CACHE"] = str(Path(pscratch) / ".hf" / "hub")

from transformers import AutoTokenizer

TRAINDATA = os.path.expandvars(STEP_1_CONFIG["TRAINDATA"])
REPOID = STEP_1_CONFIG["BASE_MODEL"]
tokenizer = AutoTokenizer.from_pretrained(REPOID)

def main():
    datasample = tt.load_data(TRAINDATA)[0]
    feat = tt.tokenize_and_mask_onlySQL(datasample, tokenizer, max_length=4096)
    # feat = tt.tokenize_and_mask(datasample, tokenizer, max_length=4096)
    full_text, trained_text = tt.render_masked_view(
        feat["input_ids"], feat["labels"], tokenizer, mask_token="█"
    )

    print("===== FULL =====")
    print(full_text)
    print("\n===== TRAINED (mask others) =====")
    print(trained_text)
    print("\nPadding_side:", tokenizer.padding_side)

if __name__ == "__main__":
    main()