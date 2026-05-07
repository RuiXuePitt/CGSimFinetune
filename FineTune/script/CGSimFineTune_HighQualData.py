"""
FineTuning with high quality data distilled from larger model.

Rui XUE
"""
import os
import sys
import FineTune.traintools as tt
from FineTune.config_loader import STEP_2_CONFIG
import json
import matplotlib.pyplot as plt
import torch
from datasets import Dataset
from pathlib import Path
import math

# ============================================================
# Config
# ============================================================
SEED = 42
TRAINDATA = os.path.expandvars(STEP_2_CONFIG["TRAINDATA"])
REPOID = STEP_2_CONFIG["BASE_MODEL"]
VERSION = STEP_2_CONFIG["VERSION"]
OUTPUT_DIR = Path(os.path.expandvars(STEP_2_CONFIG["OUTPUT_DIR"]))
ONLYSQL = STEP_2_CONFIG.get("onlySQL", False)

ADAPTER = os.path.expandvars(STEP_2_CONFIG["LORA_ADAPTER"])
CHECKPOINT_DIR = str(OUTPUT_DIR / VERSION / "checkpoints")
LOGGING_DIR = str(OUTPUT_DIR / VERSION / "logs")
LOSSPLOT_DIR = str(OUTPUT_DIR / VERSION)
fig_path = str(Path(LOSSPLOT_DIR) / "lossplot_HighQual.png")
# ============================================================

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOGGING_DIR, exist_ok=True)
os.makedirs(LOSSPLOT_DIR, exist_ok=True)

from transformers import (
    set_seed, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import PeftModel

# ============================================================
set_seed(SEED)
# ============================================================

def load_data():
    '''
    Load datasets for training & validation.
    The datasets should never be used for testing.
    '''
    train_data = []
    with open(str(TRAINDATA), "r") as f:
        for line in f:
            train_data.append(json.loads(line))
    print(TRAINDATA)
    print(len(train_data))
    print(train_data[0])
    return train_data


def load_tokenizer(base_model_id: str):
    '''
    Load tokenizer.
    Padding tokens are set as eos_token.
    '''
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    if tokenizer.pad_token is None:
        print("Setting pad token as ", tokenizer.eos_token)
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def process_data(tokenizer):
    """
    CoT + Tool Calling
    """
    train_data = load_data()
    ds = Dataset.from_list(train_data)

    def get_len(x):
        text = tokenizer.apply_chat_template(
            x["messages"],
            tools=x.get("tools"),
            tokenize=False,
            add_generation_prompt=False,
        )
        enc = tokenizer(text, truncation=False, add_special_tokens=False)
        return {"seq_len": len(enc["input_ids"])}

    len_ds = ds.map(get_len)
    max_len = max(len_ds["seq_len"])
    max_length = min(math.ceil(max_len / 1024) * 1024, 8192)

    print("raw max token length:", max_len)
    print("rounded max_length:", max_length)

    processed_ds = ds.map(
        lambda x: tt.tokenize_and_mask(x, tokenizer, max_length=max_length),
        remove_columns=ds.column_names
    )
    return processed_ds

def process_data_onlySQL(tokenizer):
    """
    Only SQL
    """
    train_data = load_data()
    ds = Dataset.from_list(train_data)

    def get_len(x):
        text = tokenizer.apply_chat_template(
            x["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        enc = tokenizer(text, truncation=False, add_special_tokens=False)
        return {"seq_len": len(enc["input_ids"])}

    len_ds = ds.map(get_len)
    max_len = max(len_ds["seq_len"])
    max_length = min(math.ceil(max_len / 1024) * 1024, 8192)

    print("raw max token length:", max_len)
    print("rounded max_length:", max_length)

    processed_ds = ds.map(
        lambda x: tt.tokenize_and_mask_onlySQL(x, tokenizer, max_length=max_length),
        remove_columns=ds.column_names
    )
    return processed_ds

def load_QLoRA_Model(base_model_id: str):
    '''
    Load model for QLoRA finetuning.
    Only used for training, so the kv_cache is turned off.
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

    ft_model = PeftModel.from_pretrained(base_model, ADAPTER, is_trainable=True)

    # summary of GPU resource after loading
    print("allocated GiB:", torch.cuda.memory_allocated()/1024**3)
    print("reserved  GiB:", torch.cuda.memory_reserved()/1024**3)
    print("is_loaded_in_4bit:", getattr(ft_model, "is_loaded_in_4bit", None))
    print("is_loaded_in_8bit:", getattr(ft_model, "is_loaded_in_8bit", None))

    ft_model.train()
    # important for further train, never forget
    ft_model.enable_input_require_grads()
    ft_model.config.use_cache = False

    # summary of trainable parameters
    ft_model.print_trainable_parameters()

    return ft_model


def set_train_config(model, processed_ds, tokenizer):
    '''
    All settings for training.
    '''

    # equivalent batch size = real batch size x grad accu steps
    batch_size = 1
    grad_accu_steps = 8

    log_steps = 10 # log record steps
    eval_steps = 10 # evaluate every 10 optimizer updates = 10 * grad_accum * batch samples
    total_epoch = 1 # overwritten when max_steps > 0
    save_steps = 10 # save checkpoint every 10 optimizer updates
    max_steps = 250 # total optimizer updates

    learning_rate = 5e-5

    # setup collator to align data lengths
    collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
        label_pad_token_id=tt.IGNORE_INDEX,
    )

    # setup training arguments for finetuning
    args = TrainingArguments(
        output_dir=CHECKPOINT_DIR,
        warmup_steps=1,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accu_steps,
        gradient_checkpointing=True,
        num_train_epochs=total_epoch,
        max_steps = max_steps,
        learning_rate=learning_rate,
        bf16=True,
        optim="paged_adamw_8bit",

        seed=SEED,
        data_seed=SEED,
        dataloader_num_workers=0,

        logging_dir=LOGGING_DIR,        # Directory for storing logs
        save_strategy="steps",       # Save the model checkpoint every logging step
        save_steps=save_steps,                # Save checkpoints every 100 steps
        logging_steps=log_steps,
        per_device_eval_batch_size=batch_size,
        eval_strategy="steps",
        eval_steps=eval_steps,               # Evaluate and save checkpoints every 50 steps
        do_eval=True,                # Perform evaluation at the end
        report_to="none"
    )

    splits = processed_ds.train_test_split(test_size=0.1, seed=SEED)
    train_ds = splits["train"]
    eval_ds  = splits["test"]

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
    )

    return trainer

def train():
    '''
    Futher Train a finetuned model.
    '''
    tokenizer = load_tokenizer(REPOID)
    if (ONLYSQL):
        print("\nTraining with ONLY SQL data.\n")
        processed_ds = process_data_onlySQL(tokenizer)
    else:
        print("\nTraining with TOOL CALLING data.\n")
        processed_ds = process_data(tokenizer)
    ft_model = load_QLoRA_Model(REPOID)
    trainer = set_train_config(ft_model, processed_ds, tokenizer)
    out = trainer.train()
    history = trainer.state.log_history
    trainer.save_model()
    return out, history

def main():
    print("\n", "=="*10)
    print("STEP 2 of Training:")
    print(f"Train Data from: {TRAINDATA}")
    print(f"Base Model from: {REPOID}")
    print(f"Adapter from: {ADAPTER}")
    print("=="*10, "\n")

    with open(LOGGING_DIR+"/summary.txt", 'w') as f:
        f.write("STEP 2 of Training:\n")
        f.write(f"Train Data from: {TRAINDATA}\n")
        f.write(f"Base Model from: {REPOID}\n")
        f.write(f"Adapter from: {ADAPTER}\n")

    _, history = train()

    train_steps, train_loss = [], []
    eval_steps, eval_loss = [], []
    for h in history:
        if "loss" in h and "step" in h:
            train_steps.append(h["step"])
            train_loss.append(h["loss"])
        if "eval_loss" in h and "step" in h:
            eval_steps.append(h["step"])
            eval_loss.append(h["eval_loss"])

    plt.figure(figsize=(8,6))
    plt.plot(train_steps, train_loss, label="train")
    plt.plot(eval_steps, eval_loss, label="val")
    plt.xlabel("step")
    plt.ylabel("loss")
    plt.legend()
    plt.savefig(fig_path)
    plt.close()

    return

if __name__ == "__main__":
    main()
