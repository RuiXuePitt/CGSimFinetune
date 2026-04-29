"""
FineTuning with high quality data distilled from larger model.
Loss function is weighted for format matching.

Rui XUE
"""

import traintools as tt
import json
import matplotlib.pyplot as plt
import torch
from datasets import Dataset
from pathlib import Path
import os
import math

home = os.environ.get("HOME")
scratch = os.environ.get("PSCRATCH")
if scratch:
    currdir = Path(scratch) / "CGSimFinetune" / "FineTune"
else:
    currdir = Path(__file__).parent
TRAINDATA_PATH = Path(scratch) / "resources" / "AI_QA_v1" / "train_AI_QA_dataset_v1.jsonl"
base_model_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"
version = "nemotron-llama8b-CGsim_highqual_v1_weightedloss"
subversion = "v2"

STEP2_ADAPTER = str(Path(scratch) / "run" / "nemotron-llama8b-CGsim_highqual_v1" / "checkpoints" / "checkpoint-210")
CHECKPOINT_DIR = str(Path(scratch) / "run" / version / subversion / "checkpoints")
LOGGING_DIR = str(Path(scratch) / "run" / version / subversion / "logs")
lossplot_dir = str(Path(home) / "run" / version / subversion)
fig_path = str(Path(lossplot_dir) / "lossplot_HighQual_weightedloss.png")

# ============================================
# Weighted Loss Config
# ============================================
W_NORMAL = 1.0
# W_CHECK_TOOL = 1.5
# W_CHECK_ARG = 8.0
# W_SQL = 2.0
W_JSON_EXTRACT = 2.0 #v1
W_JSON_MARKER = 20.0 #v1
# W_JSON_EXTRACT = 8.0 #v2

# ============================================

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOGGING_DIR, exist_ok=True)
os.makedirs(lossplot_dir, exist_ok=True)

from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import PeftModel

def load_data():
    '''
    Load datasets for training & validation.
    The datasets should never be used for testing.
    '''
    train_data = []
    with open(str(TRAINDATA_PATH), "r") as f:
        for line in f:
            train_data.append(json.loads(line))
    print(TRAINDATA_PATH)
    print(len(train_data))
    print(train_data[0])
    return train_data


def load_tokenizer(base_model_id: str):
    '''
    Load tokenizer.
    Padding tokens are set as eos_token.
    '''
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    print(f"Tokenizer Padding Side {tokenizer.padding_side}")
    if tokenizer.pad_token is None:
        print("Setting pad token as ", tokenizer.eos_token)
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer

# ========================================================================
# Find KeyWords That Needs to Be Weighted
def find_spans(text: str, pattern: str):
    '''
    Return List of Tuple (start_idx, end_idx+1) of the Pattern
    '''
    spans = []
    start = 0
    while True:
        i = text.find(pattern, start)
        if i == -1:
            break
        spans.append((i, i + len(pattern)))
        start = i + len(pattern)
    return spans

def find_json_extract_spans(text: str):
    spans = []
    pattern = "json_extract(METADATA, '$."
    start = 0

    while True:
        i = text.find(pattern, start)
        if i == -1:
            break

        j = text.find(")", i)
        if j == -1:
            break

        spans.append((i, j + 1))
        start = j + 1

    return spans

def collect_weight_spans(example, rendered_text: str):
    '''
    Add Weights with Keyword Spans
    '''
    spans = []

    for msg in example["messages"]:
        if msg.get("role") != "assistant":
            continue

        if msg.get("tool_calls"):
            for tc in msg.get("tool_calls"):
                func = tc["function"]
                name = func["name"]
                args = func["arguments"]

                # if name.startswith("check_"):
                    # # tool name itself
                    # for s, e in find_spans(rendered_text, name):
                    #     spans.append((s, e, W_CHECK_TOOL))

                    # # full check-tool argument block
                    # check_arg = '"arguments": {"input": "NO_INPUT"}'
                    # for s, e in find_spans(rendered_text, check_arg):
                    #     spans.append((s, e, W_CHECK_ARG))

                    # check_arg = '"NO_INPUT"'
                    # for s, e in find_spans(rendered_text, check_arg):
                    #     spans.append((s, e, W_CHECK_ARG))
                # elif name == "execute_sql":
                #     sql = args["sql"]

                    # # full SQL query
                    # for s, e in find_spans(rendered_text, sql):
                    #     spans.append((s, e, W_SQL))

                    # # full json_extract(METADATA, '$.key') expressions
                    # for s, e in find_json_extract_spans(rendered_text):
                    #     spans.append((s, e, W_JSON_EXTRACT))
                
                if name == "execute_sql":
                    # # $. is often omitted
                    # for s, e in find_spans(rendered_text, "$."):
                    #     spans.append((s, e, W_JSON_MARKER))

                    # full json_extract(METADATA, '$.key') expressions
                    for s, e in find_json_extract_spans(rendered_text):
                        spans.append((s, e, W_JSON_EXTRACT))

    return spans


def add_loss_weights(example, encoded, tokenizer, max_length):
    text = tokenizer.apply_chat_template(
        example["messages"],
        tools=example.get("tools"),
        tokenize=False,
        add_generation_prompt=False,
    )

    enc = tokenizer(
        text,
        truncation=True,
        max_length=max_length,
        add_special_tokens=False,
        return_offsets_mapping=True,
    )

    labels = encoded["labels"]
    weights = [
        0.0 if y == tt.IGNORE_INDEX else W_NORMAL
        for y in labels
    ]

    spans = collect_weight_spans(example, text)

    for i, (a, b) in enumerate(enc["offset_mapping"][:len(weights)]):
        if labels[i] == tt.IGNORE_INDEX:
            continue

        for s, e, w in spans:
            if a < e and b > s:
                weights[i] = max(weights[i], w)

    encoded["loss_weights"] = weights
    return encoded
# ========================================================================


def process_data(tokenizer):
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

    def tokenize_with_weights(x):
        encoded = tt.tokenize_and_mask(x, tokenizer, max_length=max_length)
        encoded = add_loss_weights(x, encoded, tokenizer, max_length)
        return encoded

    processed_ds = ds.map(
        tokenize_with_weights,
        remove_columns=ds.column_names
    )

    print("processed columns:", processed_ds.column_names)
    print("first loss weight max:", max(processed_ds[0]["loss_weights"]))
    print("first loss weight count > 1:", sum(w > 1.0 for w in processed_ds[0]["loss_weights"]))

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

    ft_model = PeftModel.from_pretrained(base_model, STEP2_ADAPTER, is_trainable=True)

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


class WeightedCollator:
    def __init__(self, base_collator):
        self.base_collator = base_collator

    def __call__(self, features):
        weights = [f.pop("loss_weights") for f in features]
        batch = self.base_collator(features)

        max_len = batch["input_ids"].shape[1]
        padded_weights = []

        for w in weights:
            pad_len = max_len - len(w)

            if self.base_collator.tokenizer.padding_side == "right":
                padded_weights.append(w + [0.0] * pad_len)
            else:
                padded_weights.append([0.0] * pad_len + w)

        batch["loss_weights"] = torch.tensor(padded_weights, dtype=torch.float)
        return batch


class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        loss_weights = inputs.pop("loss_weights")

        outputs = model(**inputs)
        logits = outputs.logits

        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        shift_weights = loss_weights[..., 1:].to(shift_logits.device)

        token_loss = torch.nn.functional.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            reduction="none",
            ignore_index=tt.IGNORE_INDEX,
        ).view(shift_labels.shape)

        mask = shift_labels.ne(tt.IGNORE_INDEX)

        loss = (token_loss * shift_weights * mask).sum() / (shift_weights * mask).sum().clamp_min(1.0)
        # Only scale training loss for gradient accumulation.
        # Do NOT scale eval loss.
        # VERY IMPORTANT!
        if model.training:
            loss = loss / self.current_gradient_accumulation_steps

        return (loss, outputs) if return_outputs else loss
# class WeightedTrainer(Trainer):
#     def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
#         labels = inputs.pop("labels")
#         loss_weights = inputs.pop("loss_weights")

#         outputs = model(**inputs)
#         logits = outputs.logits

#         shift_logits = logits[..., :-1, :].contiguous()
#         shift_labels = labels[..., 1:].contiguous()
#         shift_weights = loss_weights[..., 1:].to(shift_logits.device)

#         token_loss = torch.nn.functional.cross_entropy(
#             shift_logits.view(-1, shift_logits.size(-1)),
#             shift_labels.view(-1),
#             reduction="none",
#             ignore_index=tt.IGNORE_INDEX,
#         ).view(shift_labels.shape)

#         mask = shift_labels.ne(tt.IGNORE_INDEX)

#         weighted_loss = (
#             token_loss * shift_weights * mask
#         ).sum() / (
#             shift_weights * mask
#         ).sum().clamp_min(1.0)

#         normal_loss = (
#             token_loss * mask
#         ).sum() / mask.sum().clamp_min(1.0)

#         if not hasattr(self, "_debug_loss_count"):
#             self._debug_loss_count = 0

#         if self._debug_loss_count < 10:
#             mode = "train" if model.training else "eval"
#             active_w = shift_weights[mask]
#             print(
#                 f"[LOSS DEBUG] mode={mode} "
#                 f"weighted={weighted_loss.item():.6f} "
#                 f"normal={normal_loss.item():.6f} "
#                 f"mean_w={active_w.mean().item():.3f} "
#                 f"max_w={active_w.max().item():.1f} "
#                 f"frac_w_gt1={(active_w > 1.0).float().mean().item():.3f}"
#             )
#             self._debug_loss_count += 1

#         return (weighted_loss, outputs) if return_outputs else weighted_loss

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
    max_steps = 100 # total optimizer updates

    learning_rate = 3e-5

    # Weighted Collaor
    base_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
        label_pad_token_id=tt.IGNORE_INDEX,
    )
    collator = WeightedCollator(base_collator)

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
        logging_dir=LOGGING_DIR,        # Directory for storing logs
        save_strategy="steps",       # Save the model checkpoint every logging step
        save_steps=save_steps,                # Save checkpoints every 100 steps
        logging_steps=log_steps,
        per_device_eval_batch_size=batch_size,
        eval_strategy="steps",
        eval_steps=eval_steps,               # Evaluate and save checkpoints every 50 steps
        do_eval=True,                # Perform evaluation at the end
        report_to="none",
        label_names=["labels", "loss_weights"]
    )

    splits = processed_ds.train_test_split(test_size=0.1, seed=42)
    train_ds = splits["train"]
    eval_ds  = splits["test"]

    # def weight_stats(ds, name):
    #     vals = []
    #     gt1 = []
    #     for x in ds:
    #         w = x["loss_weights"]
    #         vals.append(sum(w) / len(w))
    #         gt1.append(sum(v > 1.0 for v in w) / len(w))
    #     print(name, "avg_weight_mean:", sum(vals) / len(vals))
    #     print(name, "avg_frac_weight_gt1:", sum(gt1) / len(gt1))

    # weight_stats(train_ds, "train")
    # weight_stats(eval_ds, "eval")

    # Weighted Trainer
    trainer = WeightedTrainer(
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
    tokenizer = load_tokenizer(base_model_id)
    processed_ds = process_data(tokenizer)
    ft_model = load_QLoRA_Model(base_model_id)
    trainer = set_train_config(ft_model, processed_ds, tokenizer)
    out = trainer.train()
    history = trainer.state.log_history
    trainer.save_model()
    return out, history

def main():
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
