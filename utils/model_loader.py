import os
import logging
import re
from typing import Optional, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from config import MODEL_PATH, BASE_MODEL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

device = "cuda" if torch.cuda.is_available() else "cpu"

# Lazy load variables
_tokenizer = None
_model = None


def _load_base():
    global _tokenizer, _model
    # Try to load tokenizer/model from a local finetuned model first
    if MODEL_PATH and os.path.exists(MODEL_PATH):
        try:
            logger.info(f"Loading tokenizer and model from {MODEL_PATH}")
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
            _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH, local_files_only=True)
            _model.to(device)
            _model.eval()
            return
        except Exception as e:
            logger.warning(f"Failed to load model from MODEL_PATH ({MODEL_PATH}): {e}")

    # Fallback to base model from Hugging Face
    try:
        logger.info(f"Loading base tokenizer and model: {BASE_MODEL}")
        _tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)
        _model.to(device)
        _model.eval()
    except Exception as e:
        logger.error(f"Error loading base model {BASE_MODEL}: {e}")
        _tokenizer = None
        _model = None


# Simple medication caution list (extend as needed)
_MED_WARNING = {
    'ibuprofen': 'Caution: Nonsteroidal anti-inflammatory drugs (e.g., ibuprofen) may increase blood pressure or interact with antihypertensive drugs. Consult your doctor or pharmacist before taking.'
}


def _collapse_repetition(text: str) -> str:
    # Remove only severe repetition (3+ identical sentences)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    out = []
    repeat_count = 0
    
    for s in sentences:
        if out and s and s == out[-1]:
            repeat_count += 1
            if repeat_count < 2:  # Allow 1 repetition
                out.append(s)
        else:
            repeat_count = 0
            out.append(s)
    
    cleaned = ' '.join(out)
    # Only remove excessive runs (4+ times)
    cleaned = re.sub(r'(\b[\w\s,]{10,}?\.)\s*(\1){3,}', r'\1', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _apply_med_warnings(question: str, generated: str, context: Optional[Dict] = None) -> str:
    q = question.lower()
    ctx_meds = []
    if context and isinstance(context, dict):
        # e.g., context may include 'medications' or 'conditions'
        ctx_meds = [m.lower() for m in context.get('medications', [])]
    for med, warning in _MED_WARNING.items():
        if med in q or med in ' '.join(ctx_meds):
            # Prepend a caution if not present
            if warning not in generated:
                generated = f"{warning}\n\n{generated}"
    return generated


def generate_answer(question: str, role: str = 'patient', context: Optional[Dict] = None) -> str:
    """Generate an answer with enhanced role-aware prompting for realistic, detailed responses.

    Args:
      question: user question text
      role: 'patient' or 'doctor' (affects prompt style)
      context: optional dict with keys like 'medications', 'conditions', 'symptoms'
    """
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _load_base()

    if _tokenizer is None or _model is None:
        logger.warning("No model available; returning canned response")
        return "Sorry, model unavailable right now. Please try again later."

    # Enhanced role-aware instruction prompts with better structure
    if role == 'patient':
        role_instruction = (
            "You are a knowledgeable, empathetic medical information assistant. Provide detailed, practical guidance. "
            "Structure your response with clear sections when helpful. Include specific steps, examples, and when to seek care."
        )
    else:
        role_instruction = (
            "You are an experienced clinician. Provide professional, evidence-based clinical advice for a colleague. "
            "Include clinical reasoning, suggested next steps, red flags to watch for, and any relevant cautions."
        )

    context_str = ''
    if context and isinstance(context, dict):
        if 'medications' in context and context['medications']:
            context_str += 'Current medications: ' + ', '.join(context['medications']) + '. '
        if 'conditions' in context and context['conditions']:
            context_str += 'Known conditions: ' + ', '.join(context['conditions']) + '. '
        if 'symptoms' in context and context['symptoms']:
            context_str += 'Presenting symptoms: ' + context['symptoms'] + '. '
        if 'allergies' in context and context['allergies']:
            context_str += 'Allergies: ' + context['allergies'] + '. '

    prompt = (
        role_instruction + '\n\n' +
        'CONTEXT: ' + (context_str if context_str else 'General medical information request') + '\n\n' +
        'QUESTION: ' + question + '\n\n' +
        'RESPONSE: Provide a thorough, practical answer with specific details and guidance.'
    )

    # Tokenize and generate with balanced parameters for quality responses
    inputs = _tokenizer(prompt, return_tensors='pt', truncation=True, padding=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            max_length=512,  # Increased for more detailed responses
            num_beams=5,  # Improved beam search
            temperature=0.7,  # Better balance between diversity and quality
            do_sample=True,  # Allow sampling for more natural text
            top_p=0.9,  # Nucleus sampling
            repetition_penalty=1.8,  # Softer penalty
            no_repeat_ngram_size=4,
            early_stopping=True,
            length_penalty=1.0
        )
    raw = _tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Lighter post-processing to preserve useful information
    cleaned = _collapse_repetition(raw)
    cleaned = _apply_med_warnings(question, cleaned, context)

    # Lenient truncation - preserve complete thoughts
    if len(cleaned) > 3000:
        cleaned = cleaned[:3000].rsplit('. ', 1)[0] + '.'

    return cleaned.strip()


