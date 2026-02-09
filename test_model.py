import os
import argparse
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# -------------------------------
# Config: model path (env var / CLI / fallback locations)
# -------------------------------
import argparse

parser = argparse.ArgumentParser(description='Test a local model folder for inference')
parser.add_argument('--model_path', type=str, help='Path to local model folder (overrides env MODEL_PATH)')
args = parser.parse_args()

# Candidate paths (you can set MODEL_PATH env var or pass --model_path)
from pathlib import Path as _Path
repo_root = _Path(__file__).resolve().parent.parent  # project root

candidates = []
# 1) CLI override
if args.model_path:
    candidates.append(_Path(args.model_path))
# 2) Environment override
if os.getenv('MODEL_PATH'):
    candidates.append(_Path(os.getenv('MODEL_PATH')))
# 3) backend config if available
try:
    from backend.config import MODEL_PATH as CONFIG_MODEL_PATH
    candidates.append(_Path(CONFIG_MODEL_PATH))
except Exception:
    pass

# 4) Common locations (relative to repo root and training working dir)
candidates += [
    repo_root / "healthcare_chatbot_model" / "flan_t5_base",
    repo_root / "healthcare_chatbot_model" / "finetuned_model",
    repo_root / "healthcare_chatbot_model",
    repo_root / "backend" / "model" / "flan_t5_base",
    repo_root / "backend" / "model" / "MyFinetunedModel",
    _Path("healthcare_chatbot_model"),  # fallback relative
    _Path("../healthcare_chatbot_model"),
]

# Normalize candidates to check expanded/resolved paths
_normed = []
for p in candidates:
    if not p:
        continue
    # expand user and resolve when possible
    try:
        _normed.append(p.expanduser())
        _normed.append(p.resolve())
    except Exception:
        _normed.append(p)

# Use unique order-preserving
seen = set()
candidates = []
for p in _normed:
    s = str(p)
    if s in seen:
        continue
    seen.add(s)
    candidates.append(p)

BASE_MODEL_PATH = None
for p in candidates:
    if p and p.exists():
        BASE_MODEL_PATH = p
        break

if BASE_MODEL_PATH is None:
    tried = ', '.join(str(p) for p in candidates if p)
    raise FileNotFoundError(
        "Model folder not found. Tried: " + tried + 
        "\nPlease run `filetuning.py` or `train.py` to produce a model, or set the path via the MODEL_PATH environment variable or --model_path argument."
    )

# -------------------------------
# Device selection (CPU/GPU)
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️ Using device: {device}")

# -------------------------------
# Load tokenizer and model
# -------------------------------
print("🔽 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(str(BASE_MODEL_PATH), local_files_only=True)

print("🔽 Loading model...")
model = AutoModelForSeq2SeqLM.from_pretrained(str(BASE_MODEL_PATH), local_files_only=True)
model.to(device)

# -------------------------------
# Main loop for user input
# -------------------------------
print("✅ Model loaded successfully!")
print("Type 'exit' to quit.\n")

while True:
    input_text = input("Enter text: ")
    if input_text.lower() == "exit":
        break

    # Tokenize input
    inputs = tokenizer(input_text, return_tensors="pt").to(device)

    # Generate output
    outputs = model.generate(**inputs, max_new_tokens=200)

    # Decode and print
    decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Output: {decoded_output}\n")
