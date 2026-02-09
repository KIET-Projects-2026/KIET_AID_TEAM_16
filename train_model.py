# ======================= 0. INSTALL CHECK =======================
# Run once in terminal:
# pip install transformers datasets peft accelerate sentencepiece torch pandas

# ======================= 1. IMPORTS =============================
import os
import json
import torch
import shutil
import pandas as pd

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model

# ======================= 2. PATH CONFIG ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "healthcare_chatbot_dataset_large.csv"
)

OUTPUT_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "backend", "model", "MyFinetunedModel")
)

BASE_MODEL_NAME = "google/flan-t5-base"

print("📁 Dataset Path:", DATA_PATH)
print("📁 Output Model Path:", OUTPUT_DIR)

# ======================= 3. SAFE DIRECTORY CREATION ===============
# IMPORTANT FIX FOR YOUR ERROR

if os.path.exists(OUTPUT_DIR):
    if os.path.isfile(OUTPUT_DIR):
        print("⚠️ Output path is a FILE. Deleting it...")
        os.remove(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
    else:
        print("✅ Output directory already exists. Reusing it.")
else:
    os.makedirs(OUTPUT_DIR)

# ======================= 4. LOAD BASE MODEL ======================
print("\n🔽 Loading base FLAN-T5 model...")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_NAME)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ======================= 5. LOAD DATA =============================
print("\n📂 Loading dataset...")

df = pd.read_csv(DATA_PATH)
print("✅ Rows:", len(df))
print("📋 Columns:", list(df.columns))

# -------- AUTO COLUMN DETECTION ----------
possible_input_cols = [
    "prompt", "input", "question", "query",
    "user_input", "text", "Patient", "Question"
]
possible_output_cols = [
    "response", "output", "answer", "reply",
    "target", "Doctor", "Answer"
]

INPUT_COL = None
TARGET_COL = None

for col in possible_input_cols:
    if col in df.columns:
        INPUT_COL = col
        break

for col in possible_output_cols:
    if col in df.columns:
        TARGET_COL = col
        break

if INPUT_COL is None:
    INPUT_COL = df.columns[0]

if TARGET_COL is None:
    TARGET_COL = df.columns[1]

print(f"🧠 Using INPUT column: {INPUT_COL}")
print(f"🧠 Using OUTPUT column: {TARGET_COL}")

df = df.dropna(subset=[INPUT_COL, TARGET_COL])

# ======================= 6. SAMPLE DATA ===========================
SAMPLE_SIZE = 500
EPOCHS = 50

if len(df) > SAMPLE_SIZE:
    df = df.sample(SAMPLE_SIZE, random_state=42).reset_index(drop=True)

print(f"🎯 Training on {len(df)} samples")

# ======================= 7. DATASET FORMAT ========================
def format_example(row):
    return {
        "input_text": str(row[INPUT_COL]).strip(),
        "target_text": str(row[TARGET_COL]).strip()
    }

dataset = Dataset.from_list(
    [format_example(row) for _, row in df.iterrows()]
)

# ======================= 8. TOKENIZATION ==========================
def tokenize(batch):
    inputs = tokenizer(
        batch["input_text"],
        padding="max_length",
        truncation=True,
        max_length=256
    )

    targets = tokenizer(
        batch["target_text"],
        padding="max_length",
        truncation=True,
        max_length=256
    )

    inputs["labels"] = targets["input_ids"]
    return inputs

tokenized_dataset = dataset.map(
    tokenize,
    batched=True,
    remove_columns=dataset.column_names
)

# ======================= 9. APPLY LORA ============================
print("\n🔧 Applying LoRA...")

lora_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q", "v"],
    lora_dropout=0.05,
    bias="none",
    task_type="SEQ_2_SEQ_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ======================= 10. TRAINING =============================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=4,   # safer for Windows
    gradient_accumulation_steps=2,
    learning_rate=3e-4,
    logging_steps=20,
    save_strategy="epoch",
    save_total_limit=1,
    report_to="none",
    fp16=torch.cuda.is_available(),
    warmup_steps=50,
    weight_decay=0.01
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer
)

print("\n🚀 TRAINING STARTED...\n")
trainer.train()

# ======================= 11. SAVE MODEL ===========================
print("\n💾 Saving model...")

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

config_info = {
    "input_column": INPUT_COL,
    "output_column": TARGET_COL,
    "samples_used": len(df)
}

with open(os.path.join(OUTPUT_DIR, "training_config.json"), "w") as f:
    json.dump(config_info, f, indent=2)

print("\n✅ TRAINING COMPLETE")
print("📁 Model saved to:", OUTPUT_DIR)
