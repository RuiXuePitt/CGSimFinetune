import traintools as tt
import json
import matplotlib.pyplot as plt
import torch
from datasets import load_dataset, Dataset
from pathlib import Path
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

currdir = Path(__file__).parent
trainpath = currdir.parent / "resources" / "traindata.jsonl"
repo_id = "AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"

def load_data():
    '''
    Load datasets for training & validation.
    The datasets should never be used for testing.
    '''
    train_data = []
    with open(str(trainpath), "r") as f:
        for line in f:
            train_data.append(json.loads(line))
    return train_data


def load_tokenizer(repo_id: str):
    '''
    Load tokenizer.
    Padding tokens are set as eos_token.
    '''
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    if tokenizer.pad_token is None:
        print("Setting pad token as ", tokenizer.eos_token)
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def process_data():
    train_data = load_data()
    tokenizer = load_tokenizer(repo_id)
    ds = Dataset.from_list(train_data)
    processed_ds = ds.map(lambda x: tt.tokenize_and_mask(x, tokenizer), remove_columns=ds.column_names)
    return processed_ds


def load_QLoRA_Model(repo_id: str):
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
    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
    )

    model = AutoModelForCausalLM.from_pretrained(repo_id, quantization_config=config)
    model.config.use_cache = False # turn off caching for training
    model = prepare_model_for_kbit_training(model)

    # summary of GPU resource after loading
    print("allocated GiB:", torch.cuda.memory_allocated()/1024**3)
    print("reserved  GiB:", torch.cuda.memory_reserved()/1024**3)
    print("is_loaded_in_4bit:", getattr(model, "is_loaded_in_4bit", None))
    print("is_loaded_in_8bit:", getattr(model, "is_loaded_in_8bit", None))

    model = get_peft_model(model, lora)
    # summary of trainable parameters
    model.print_trainable_parameters()

    return model


def set_train_config(model, processed_ds):
    '''
    All settings for training.
    '''

    batch_size = 4
    eval_steps = 50
    total_epoch = 1
    save_steps = 100

    run_name = "nemotron-llama8b-CGsim"
    output_dir = str(currdir.parent / "run" / run_name)
    logging_dir = str(currdir.parent / "run" / "logs")

    # setup collator to align data lengths
    tokenizer = load_tokenizer(repo_id)
    collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
        label_pad_token_id=tt.IGNORE_INDEX,
    )

    # setup training arguments for finetuning
    args = TrainingArguments(
        output_dir=output_dir,
        warmup_steps=1,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=1,
        gradient_checkpointing=True,
        num_train_epochs=total_epoch,
        learning_rate=2e-4,
        bf16=True,
        optim="paged_adamw_8bit",
        logging_dir=logging_dir,        # Directory for storing logs
        save_strategy="steps",       # Save the model checkpoint every logging step
        save_steps=save_steps,                # Save checkpoints every 100 steps
        logging_steps=10,
        per_device_eval_batch_size=batch_size,
        eval_strategy="steps",
        eval_steps=eval_steps,               # Evaluate and save checkpoints every 50 steps
        do_eval=True,                # Perform evaluation at the end of
        report_to="none"
    )

    splits = processed_ds.train_test_split(test_size=0.1, seed=42)
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
    Train a finetuned model.
    '''
    processed_ds = process_data()
    model = load_QLoRA_Model(repo_id)
    trainer = set_train_config(model, processed_ds)
    out = trainer.train()
    history = trainer.state.log_history
    return out, history

def main():
    _, history = train()

    run_name = "nemotron-llama8b-CGsim"
    output_dir = currdir.parent / "run" / run_name
    fig_loc = str(output_dir / "lossplot.png")

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
    plt.savefig(fig_loc)
    plt.close()

    return

if __name__ == "__main__":
    main()
