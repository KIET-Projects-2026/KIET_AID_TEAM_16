"""
HealthCare-ChatBot Training Script
Trains a conversational AI model for healthcare symptom checking, 
medication information, and appointment workflows.
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    TrainingArguments, 
    Trainer,
    DataCollatorForSeq2Seq
)
from datasets import Dataset as HFDataset
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import warnings
import os
import json
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple
import logging
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
except:
    logger.warning("Some NLTK downloads failed, continuing anyway...")


class HealthcareChatDataset:
    """
    Processes and prepares healthcare chatbot dataset for training
    """
    
    def __init__(self, csv_path: str):
        """
        Initialize dataset processor
        
        Args:
            csv_path: Path to the healthcare chatbot CSV file
        """
        self.csv_path = csv_path
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Healthcare-specific terms to keep (not remove as stopwords)
        self.medical_terms = {
            'pain', 'fever', 'headache', 'symptom', 'medication',
            'doctor', 'emergency', 'help', 'treatment', 'dose'
        }
        
        logger.info(f"Loading dataset from {csv_path}")
        self.df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(self.df)} records")
        
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text using NLTK
        
        Args:
            text: Input text string
            
        Returns:
            Preprocessed text
        """
        if pd.isna(text) or text == "":
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Tokenization
        tokens = word_tokenize(text)
        
        # Remove stopwords (except medical terms) and lemmatize
        processed_tokens = []
        for token in tokens:
            if token.isalpha():  # Keep only alphabetic tokens
                if token in self.medical_terms or token not in self.stop_words:
                    lemmatized = self.lemmatizer.lemmatize(token)
                    processed_tokens.append(lemmatized)
        
        return ' '.join(processed_tokens)
    
    def create_conversation_pairs(self) -> List[Dict[str, str]]:
        """
        Create input-output pairs for training
        
        Returns:
            List of conversation dictionaries
        """
        conversations = []
        
        for idx, row in self.df.iterrows():
            # Build comprehensive input context
            input_parts = []
            
            # User input (main query)
            if pd.notna(row['user_input']) and row['user_input']:
                input_parts.append(f"Patient Query: {row['user_input']}")
            
            # Add context information
            if pd.notna(row['symptoms']) and row['symptoms']:
                input_parts.append(f"Symptoms: {row['symptoms']}")
            
            if pd.notna(row['conditions']) and row['conditions']:
                input_parts.append(f"Known Conditions: {row['conditions']}")
            
            if pd.notna(row['medications_mentioned']) and row['medications_mentioned']:
                input_parts.append(f"Medications: {row['medications_mentioned']}")
            
            # Add urgency level for context
            if pd.notna(row['urgency_level']):
                input_parts.append(f"Urgency: {row['urgency_level']}")
            
            # Add patient demographics
            if pd.notna(row['age_group']):
                input_parts.append(f"Age Group: {row['age_group']}")
            
            # Combine input
            full_input = " | ".join(input_parts)
            
            # Build comprehensive output response
            output_parts = []
            
            # Main bot response
            if pd.notna(row['bot_response']) and row['bot_response']:
                output_parts.append(row['bot_response'])
            
            # Add advice
            if pd.notna(row['advice_given']) and row['advice_given']:
                output_parts.append(f"Advice: {row['advice_given']}")
            
            # Add next steps
            if pd.notna(row['next_steps']) and row['next_steps']:
                output_parts.append(f"Next Steps: {row['next_steps']}")
            
            # Add warnings for emergency cases
            if pd.notna(row['emergency_signs']) and row['emergency_signs']:
                output_parts.append(f"⚠️ Emergency Signs: {row['emergency_signs']}")
            
            # Add home remedies if applicable
            if pd.notna(row['home_remedies']) and row['home_remedies']:
                output_parts.append(f"Home Care: {row['home_remedies']}")
            
            # Add when to seek help
            if pd.notna(row['when_to_seek_help']) and row['when_to_seek_help']:
                output_parts.append(f"Seek Medical Help If: {row['when_to_seek_help']}")
            
            # Always add disclaimer
            output_parts.append("⚕️ Disclaimer: This is not medical advice. Always consult with a healthcare professional for proper diagnosis and treatment.")
            
            # Combine output
            full_output = " ".join(output_parts)
            
            if full_input and full_output:
                conversations.append({
                    'input': full_input,
                    'output': full_output,
                    'intent': row['user_intent'] if pd.notna(row['user_intent']) else 'general',
                    'urgency': row['urgency_level'] if pd.notna(row['urgency_level']) else 'medium'
                })
            
            # Progress logging
            if (idx + 1) % 10000 == 0:
                logger.info(f"Processed {idx + 1} records...")
        
        logger.info(f"Created {len(conversations)} conversation pairs")
        return conversations
    
    def prepare_for_training(self, 
                            test_size: float = 0.1,
                            val_size: float = 0.1,
                            max_samples: int = None) -> Tuple[List, List, List]:
        """
        Prepare train/val/test splits
        
        Args:
            test_size: Proportion of data for testing
            val_size: Proportion of data for validation
            max_samples: Maximum number of samples to use (for memory constraints)
            
        Returns:
            Tuple of (train_data, val_data, test_data)
        """
        conversations = self.create_conversation_pairs()
        
        # Limit samples if specified
        if max_samples and len(conversations) > max_samples:
            logger.info(f"Limiting to {max_samples} samples")
            conversations = conversations[:max_samples]
        
        # First split: separate test set
        stratify_vals = [c['urgency'] for c in conversations]
        stratify_to_use = stratify_vals if len(set(stratify_vals)) > 1 else None
        try:
            train_val, test = train_test_split(
                conversations, 
                test_size=test_size, 
                random_state=42,
                stratify=stratify_to_use
            )
        except ValueError:
            # Not enough classes for stratify; fallback to no stratify
            train_val, test = train_test_split(
                conversations,
                test_size=test_size,
                random_state=42
            )
        
        # Second split: separate validation set
        val_size_adjusted = val_size / (1 - test_size)
        stratify_vals_train = [c['urgency'] for c in train_val]
        stratify_to_use_train = stratify_vals_train if len(set(stratify_vals_train)) > 1 else None
        try:
            train, val = train_test_split(
                train_val,
                test_size=val_size_adjusted,
                random_state=42,
                stratify=stratify_to_use_train
            )
        except ValueError:
            train, val = train_test_split(
                train_val,
                test_size=val_size_adjusted,
                random_state=42
            )
        
        logger.info(f"Dataset split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
        return train, val, test


class HealthcareChatTrainer:
    """
    Handles model training for healthcare chatbot
    """
    
    def __init__(self, 
                 model_name: str = "facebook/blenderbot-400M-distill",
                 output_dir: str = "./healthcare_chatbot_model",
                 max_length: int = 512):
        """
        Initialize trainer
        
        Args:
            model_name: Hugging Face model to use
            output_dir: Directory to save trained model
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.output_dir = output_dir
        self.max_length = max_length
        
        logger.info(f"Loading tokenizer and model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def tokenize_data(self, examples: Dict) -> Dict:
        """
        Tokenize input-output pairs
        
        Args:
            examples: Dictionary with 'input' and 'output' keys
            
        Returns:
            Tokenized dictionary
        """
        # Tokenize inputs
        model_inputs = self.tokenizer(
            examples['input'],
            max_length=self.max_length,
            truncation=True,
            padding='max_length'
        )
        
        # Tokenize outputs
        labels = self.tokenizer(
            examples['output'],
            max_length=self.max_length,
            truncation=True,
            padding='max_length'
        )
        
        model_inputs['labels'] = labels['input_ids']
        return model_inputs
    
    def train(self, 
              train_data: List[Dict],
              val_data: List[Dict],
              epochs: int = 3,
              batch_size: int = 8,
              learning_rate: float = 5e-5,
              warmup_steps: int = 500,
              save_steps: int = 1000,
              eval_steps: int = 500):
        """
        Train the model
        
        Args:
            train_data: Training conversations
            val_data: Validation conversations
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            warmup_steps: Warmup steps for learning rate
            save_steps: Steps between model saves
            eval_steps: Steps between evaluations
        """
        logger.info("Preparing datasets...")
        
        # Convert to Hugging Face datasets
        train_df = pd.DataFrame(train_data)
        val_df = pd.DataFrame(val_data)
        
        train_dataset = HFDataset.from_pandas(train_df)
        val_dataset = HFDataset.from_pandas(val_df)
        
        # Tokenize datasets
        logger.info("Tokenizing datasets...")
        train_dataset = train_dataset.map(
            self.tokenize_data,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        
        val_dataset = val_dataset.map(
            self.tokenize_data,
            batched=True,
            remove_columns=val_dataset.column_names
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            weight_decay=0.01,
            logging_dir=f'{self.output_dir}/logs',
            logging_steps=100,
            save_steps=save_steps,
            eval_steps=eval_steps,
            evaluation_strategy="steps",
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
            gradient_accumulation_steps=2,
            report_to="none"  # Disable wandb/tensorboard if not needed
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            self.tokenizer,
            model=self.model
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save final model
        logger.info(f"Saving model to {self.output_dir}")
        trainer.save_model(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        # Save training metrics
        metrics_path = os.path.join(self.output_dir, 'training_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(trainer.state.log_history, f, indent=2)
        
        logger.info("Training complete!")
        
        return trainer
    
    def evaluate(self, test_data: List[Dict]) -> Dict:
        """
        Evaluate model on test set
        
        Args:
            test_data: Test conversations
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model on test set...")
        
        test_df = pd.DataFrame(test_data)
        test_dataset = HFDataset.from_pandas(test_df)
        
        test_dataset = test_dataset.map(
            self.tokenize_data,
            batched=True,
            remove_columns=test_dataset.column_names
        )
        
        data_collator = DataCollatorForSeq2Seq(
            self.tokenizer,
            model=self.model
        )
        
        trainer = Trainer(
            model=self.model,
            data_collator=data_collator,
        )
        
        results = trainer.evaluate(test_dataset)
        
        logger.info(f"Test Results: {results}")
        
        # Save test results
        results_path = os.path.join(self.output_dir, 'test_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results


def main():
    """
    Main training pipeline
    """
    logger.info("=" * 50)
    logger.info("HealthCare-ChatBot Training Pipeline")
    logger.info("=" * 50)
    
    # Parse CLI arguments and environment defaults
    parser = argparse.ArgumentParser(description='Train Healthcare Chatbot Model')
    parser.add_argument('--csv_path', type=str, default=os.getenv('DATA_PATH', 'healthcare_chatbot_dataset_large.csv'), help='Path to dataset CSV')
    parser.add_argument('--model_name', type=str, default=os.getenv('MODEL_NAME', 'facebook/blenderbot-400M-distill'), help='Base model name')
    parser.add_argument('--output_dir', type=str, default=os.getenv('OUTPUT_DIR', './healthcare_chatbot_model'), help='Model output directory')
    parser.add_argument('--max_samples', type=int, default=int(os.getenv('MAX_SAMPLES', '50000')), help='Limit samples for faster runs')
    parser.add_argument('--epochs', type=int, default=int(os.getenv('EPOCHS', '3')), help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=int(os.getenv('BATCH_SIZE', '8')), help='Training batch size')
    parser.add_argument('--learning_rate', type=float, default=float(os.getenv('LEARNING_RATE', '5e-5')), help='Learning rate')
    parser.add_argument('--max_length', type=int, default=int(os.getenv('MAX_LENGTH', '512')), help='Maximum token length')
    parser.add_argument('--dry_run', action='store_true', help='If set, prepare data and trainer but skip actual training')
    args = parser.parse_args()

    CONFIG = {
        'csv_path': args.csv_path,
        'model_name': args.model_name,
        'output_dir': args.output_dir,
        'max_samples': args.max_samples,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate,
        'max_length': args.max_length
    }
    
    # Print configuration['pa]
    logger.info("Training Configuration:")
    for key, value in CONFIG.items():
        logger.info(f"  {key}: {value}")
    
    # Validate CSV existence
    if not os.path.exists(CONFIG['csv_path']):
        logger.error(f"Dataset not found at {CONFIG['csv_path']}. Make sure the path is correct or run Team16kietAid.py to generate it.")
        raise FileNotFoundError(CONFIG['csv_path'])

    try:
        # Step 1: Load and prepare dataset
        logger.info("\n" + "=" * 50)
        logger.info("Step 1: Loading and Preparing Dataset")
        logger.info("=" * 50)
        
        dataset = HealthcareChatDataset(CONFIG['csv_path'])
        train_data, val_data, test_data = dataset.prepare_for_training(
            max_samples=CONFIG.get('max_samples')
        )
        
        # Step 2: Initialize trainer
        logger.info("\n" + "=" * 50)
        logger.info("Step 2: Initializing Trainer")
        logger.info("=" * 50)
        
        trainer = HealthcareChatTrainer(
            model_name=CONFIG['model_name'],
            output_dir=CONFIG['output_dir'],
            max_length=CONFIG['max_length']
        )
        
        # Step 3: Train model
        logger.info("\n" + "=" * 50)
        logger.info("Step 3: Training Model")
        logger.info("=" * 50)
        
        if args.dry_run:
            logger.info("Dry run enabled — skipping trainer.train(). Model, tokenizer, and datasets prepared.")
        else:
            trainer.train(
            train_data=train_data,
            val_data=val_data,
            epochs=CONFIG['epochs'],
            batch_size=CONFIG['batch_size'],
            learning_rate=CONFIG['learning_rate']
        )
        
        # Step 4: Evaluate model
        logger.info("\n" + "=" * 50)
        logger.info("Step 4: Evaluating Model")
        logger.info("=" * 50)
        
        results = trainer.evaluate(test_data)
        
        logger.info("\n" + "=" * 50)
        logger.info("Training Pipeline Complete!")
        logger.info("=" * 50)
        logger.info(f"Model saved to: {CONFIG['output_dir']}")
        logger.info(f"Test Loss: {results.get('eval_loss', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Training failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    main()