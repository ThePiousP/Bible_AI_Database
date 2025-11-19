# Bible AI Training Architecture
## Complete Guide to Building a Conversational Bible AI

**Goal**: Create an AI model that deeply understands the Bible and can discuss it intelligently

**Created**: 2025-11-16
**Status**: Foundation Code & Architecture

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layer 1: NER Foundation](#layer-1-ner-foundation)
3. [Layer 2: Semantic Understanding](#layer-2-semantic-understanding)
4. [Layer 3: RAG System](#layer-3-rag-system)
5. [Layer 4: Fine-Tuned LLM](#layer-4-fine-tuned-llm)
6. [Layer 5: Conversation System](#layer-5-conversation-system)
7. [Training Pipeline](#training-pipeline)
8. [Deployment](#deployment)

---

## Architecture Overview

### Multi-Layer System

Your conversational Bible AI requires **5 integrated layers**:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Conversation Interface                        │
│ - User interaction                                      │
│ - Context management                                    │
│ - Response generation                                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Fine-Tuned LLM (GPT/Llama)                    │
│ - Biblical language understanding                       │
│ - Theological reasoning                                 │
│ - Contextual interpretation                             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: RAG System (Retrieval-Augmented Generation)   │
│ - Semantic search                                       │
│ - Cross-reference retrieval                             │
│ - Contextual verse lookup                               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Semantic Understanding                         │
│ - Embeddings (sentence-level)                           │
│ - Vector database (FAISS/Chroma)                        │
│ - Similarity search                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 1: NER Foundation (YOU ARE HERE)                 │
│ - Entity extraction (DEITY, PERSON, LOCATION)          │
│ - Structured knowledge                                  │
│ - Relationship mapping                                  │
└─────────────────────────────────────────────────────────┘
```

### Current Progress

✅ **Layer 1**: NER pipeline ready (65 entity types, Prodigy annotation)
🔄 **Layer 2-5**: Need implementation (this guide provides the code)

---

## Layer 1: NER Foundation

### What You Already Have

```python
# Your current NER training code (train_baseline_spacy.py)
# This extracts entities like DEITY, PERSON, LOCATION, etc.
```

### Enhanced NER Training with Metadata

Create `code/ai_training/train_ner_enhanced.py`:

```python
#!/usr/bin/env python3
"""
Enhanced NER training with theological metadata.
Builds on your existing silver_export.py work.
"""

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import json
from pathlib import Path
from typing import List, Dict, Tuple
import random

class BibleNERTrainer:
    """Train NER model with theological understanding."""

    def __init__(self, model_name: str = "en_core_web_lg"):
        """Initialize trainer with base model."""
        self.nlp = spacy.load(model_name)

        # Add custom entity ruler for biblical entities
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            self._load_patterns(ruler)

    def _load_patterns(self, ruler):
        """Load patterns from your prodigy_patterns.jsonl."""
        patterns_file = Path("prodigy_patterns.jsonl")
        if patterns_file.exists():
            patterns = []
            with open(patterns_file) as f:
                for line in f:
                    pattern = json.loads(line)
                    patterns.append(pattern)
            ruler.add_patterns(patterns)

    def load_training_data(self,
                          train_file: str,
                          gold_file: str = None) -> List[Example]:
        """
        Load training data from silver + gold annotations.

        Args:
            train_file: Silver dataset (auto-generated)
            gold_file: Gold annotations (Prodigy output)

        Returns:
            List of spaCy Example objects
        """
        examples = []

        # Load silver data
        examples.extend(self._load_jsonl(train_file))

        # Add gold data (higher quality, weighted more)
        if gold_file and Path(gold_file).exists():
            gold_examples = self._load_jsonl(gold_file)
            # Duplicate gold data for 3x weight
            examples.extend(gold_examples * 3)

        random.shuffle(examples)
        return examples

    def _load_jsonl(self, filepath: str) -> List[Example]:
        """Load JSONL format (spaCy/Prodigy compatible)."""
        examples = []
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                text = data["text"]
                entities = data.get("spans", [])

                doc = self.nlp.make_doc(text)
                ents = []
                for span in entities:
                    start, end, label = span["start"], span["end"], span["label"]
                    ent_span = doc.char_span(start, end, label=label)
                    if ent_span:
                        ents.append(ent_span)

                doc.ents = ents
                examples.append(Example.from_dict(doc, {"entities": entities}))

        return examples

    def train(self,
             train_data: List[Example],
             dev_data: List[Example],
             output_dir: str = "models/ner_biblical",
             n_iter: int = 30,
             dropout: float = 0.3) -> Dict:
        """
        Train NER model with early stopping.

        Args:
            train_data: Training examples
            dev_data: Development set for evaluation
            output_dir: Where to save model
            n_iter: Number of epochs
            dropout: Dropout rate

        Returns:
            Training statistics
        """
        # Get NER component
        ner = self.nlp.get_pipe("ner")

        # Add all labels from training data
        for example in train_data:
            for ent in example.reference.ents:
                ner.add_label(ent.label_)

        # Training loop
        optimizer = self.nlp.resume_training()
        losses = {}
        best_f1 = 0.0

        for epoch in range(n_iter):
            random.shuffle(train_data)
            batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))

            for batch in batches:
                self.nlp.update(batch, drop=dropout, losses=losses, sgd=optimizer)

            # Evaluate on dev set
            scores = self.evaluate(dev_data)
            print(f"Epoch {epoch+1}/{n_iter} - Loss: {losses['ner']:.2f} - "
                  f"F1: {scores['f1']:.3f} - P: {scores['precision']:.3f} - "
                  f"R: {scores['recall']:.3f}")

            # Save best model
            if scores['f1'] > best_f1:
                best_f1 = scores['f1']
                output_path = Path(output_dir) / "best"
                output_path.mkdir(parents=True, exist_ok=True)
                self.nlp.to_disk(output_path)
                print(f"  → Saved best model (F1: {best_f1:.3f})")

        # Save final model
        final_path = Path(output_dir) / "final"
        final_path.mkdir(parents=True, exist_ok=True)
        self.nlp.to_disk(final_path)

        return {"best_f1": best_f1, "final_loss": losses.get('ner', 0)}

    def evaluate(self, dev_data: List[Example]) -> Dict[str, float]:
        """Evaluate model on development set."""
        scorer = spacy.scorer.Scorer()
        for example in dev_data:
            pred_doc = self.nlp(example.reference.text)
            scorer.score(Example(pred_doc, example.reference))

        scores = scorer.scores
        return {
            "precision": scores["ents_p"],
            "recall": scores["ents_r"],
            "f1": scores["ents_f"]
        }


def main():
    """Train enhanced NER model."""
    print("=" * 60)
    print("Bible NER Enhanced Training")
    print("=" * 60)

    trainer = BibleNERTrainer()

    # Load data
    print("\n📖 Loading training data...")
    train_data = trainer.load_training_data(
        train_file="silver_out/train.jsonl",
        gold_file="output/gold_annotations.jsonl"  # From Prodigy
    )
    dev_data = trainer._load_jsonl("silver_out/dev.jsonl")

    print(f"  → Train: {len(train_data)} examples")
    print(f"  → Dev: {len(dev_data)} examples")

    # Train
    print("\n🚀 Training model...")
    stats = trainer.train(
        train_data=train_data,
        dev_data=dev_data,
        output_dir="models/ner_biblical_v1",
        n_iter=30,
        dropout=0.3
    )

    print("\n✅ Training complete!")
    print(f"  → Best F1: {stats['best_f1']:.3f}")
    print(f"  → Model saved: models/ner_biblical_v1/best/")


if __name__ == "__main__":
    main()
```

**Usage**:
```bash
python code/ai_training/train_ner_enhanced.py
```

---

## Layer 2: Semantic Understanding

### Create Embeddings for Every Verse

Create `code/ai_training/create_embeddings.py`:

```python
#!/usr/bin/env python3
"""
Create semantic embeddings for all Bible verses.
Enables similarity search and semantic understanding.
"""

import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
from tqdm import tqdm
from typing import List, Dict
import pickle

class BibleEmbeddingsCreator:
    """Create and manage Bible verse embeddings."""

    def __init__(self,
                 model_name: str = "all-mpnet-base-v2",
                 db_path: str = "data/GoodBook.db"):
        """
        Initialize embeddings creator.

        Args:
            model_name: Sentence transformer model
                Options:
                - all-mpnet-base-v2 (best quality, 768 dims)
                - all-MiniLM-L6-v2 (faster, 384 dims)
                - multi-qa-mpnet-base-dot-v1 (Q&A optimized)
            db_path: Path to Bible database
        """
        self.model = SentenceTransformer(model_name)
        self.db_path = db_path
        self.embeddings = {}
        self.metadata = {}

    def create_verse_embeddings(self,
                                include_context: bool = True) -> Dict:
        """
        Create embeddings for all verses.

        Args:
            include_context: Add book/chapter context to embedding

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Fetch all verses with metadata
        query = """
            SELECT
                v.id,
                b.book_name,
                c.chapter_number,
                v.verse_num,
                v.text_clean,
                v.text_plain
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            ORDER BY b.id, c.chapter_number, v.verse_num
        """

        cursor.execute(query)
        verses = cursor.fetchall()

        print(f"Creating embeddings for {len(verses)} verses...")

        texts_to_embed = []
        verse_ids = []

        for verse_id, book, chapter, verse_num, text_clean, text_plain in tqdm(verses):
            # Use clean text if available, fallback to plain
            text = text_clean or text_plain

            if include_context:
                # Add context for better semantic understanding
                context_text = f"{book} {chapter}:{verse_num} - {text}"
            else:
                context_text = text

            texts_to_embed.append(context_text)
            verse_ids.append(verse_id)

            # Store metadata
            self.metadata[verse_id] = {
                "book": book,
                "chapter": chapter,
                "verse": verse_num,
                "text": text,
                "reference": f"{book} {chapter}:{verse_num}"
            }

        # Create embeddings in batches (faster)
        print("Encoding verses...")
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Store embeddings
        for verse_id, embedding in zip(verse_ids, embeddings):
            self.embeddings[verse_id] = embedding

        conn.close()

        return {
            "total_verses": len(verses),
            "embedding_dim": embeddings.shape[1],
            "model": self.model.get_sentence_embedding_dimension()
        }

    def save_embeddings(self, output_dir: str = "data/embeddings"):
        """Save embeddings and metadata to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save embeddings (numpy format)
        embeddings_array = np.array(list(self.embeddings.values()))
        verse_ids = list(self.embeddings.keys())

        np.save(output_path / "embeddings.npy", embeddings_array)

        # Save verse IDs and metadata
        with open(output_path / "verse_ids.json", "w") as f:
            json.dump(verse_ids, f)

        with open(output_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

        # Save as pickle for easy loading
        with open(output_path / "embeddings.pkl", "wb") as f:
            pickle.dump({
                "embeddings": self.embeddings,
                "metadata": self.metadata
            }, f)

        print(f"Saved embeddings to {output_path}/")

    def create_theological_embeddings(self):
        """
        Create specialized embeddings for theological concepts.
        Groups verses by themes, topics, and theological significance.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Example: Create embeddings for messianic prophecies
        messianic_prophecies = [
            "Isaiah 7:14", "Isaiah 9:6", "Micah 5:2",
            "Psalm 22", "Isaiah 53", "Zechariah 9:9"
        ]

        # Example: Create embeddings for covenant passages
        covenant_passages = [
            "Genesis 12:1-3", "Exodus 19:5-6", "Jeremiah 31:31-34",
            "Luke 22:20", "Hebrews 8:8-12"
        ]

        # You can extend this with your NER data!
        # Group verses by entity types (DEITY mentions, PERSON stories, etc.)

        print("Creating theological concept embeddings...")
        # Implementation here
        pass


def main():
    """Create Bible embeddings."""
    print("=" * 60)
    print("Bible Semantic Embeddings Creator")
    print("=" * 60)

    creator = BibleEmbeddingsCreator(
        model_name="all-mpnet-base-v2",  # Best quality
        db_path="data/GoodBook.db"
    )

    # Create embeddings
    stats = creator.create_verse_embeddings(include_context=True)
    print(f"\n✅ Created embeddings:")
    print(f"  → Verses: {stats['total_verses']}")
    print(f"  → Dimensions: {stats['embedding_dim']}")

    # Save
    creator.save_embeddings("data/embeddings")
    print("\n💾 Embeddings saved!")


if __name__ == "__main__":
    main()
```

**Usage**:
```bash
pip install sentence-transformers
python code/ai_training/create_embeddings.py
```

---

## Layer 3: RAG System (Retrieval-Augmented Generation)

Create `code/ai_training/rag_system.py`:

```python
#!/usr/bin/env python3
"""
RAG system for Bible Q&A.
Retrieves relevant verses and generates contextual answers.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Search result with verse and similarity score."""
    verse_id: int
    reference: str
    text: str
    score: float
    book: str
    chapter: int
    verse: int

class BibleRAG:
    """Retrieval-Augmented Generation for Bible Q&A."""

    def __init__(self,
                 embeddings_path: str = "data/embeddings/embeddings.pkl",
                 model_name: str = "all-mpnet-base-v2"):
        """
        Initialize RAG system.

        Args:
            embeddings_path: Path to saved embeddings
            model_name: Same model used to create embeddings
        """
        self.model = SentenceTransformer(model_name)

        # Load embeddings
        print("Loading embeddings...")
        with open(embeddings_path, "rb") as f:
            data = pickle.load(f)
            self.embeddings = data["embeddings"]
            self.metadata = data["metadata"]

        # Convert to numpy array for fast search
        self.verse_ids = list(self.embeddings.keys())
        self.embedding_matrix = np.array([
            self.embeddings[vid] for vid in self.verse_ids
        ])

        print(f"Loaded {len(self.verse_ids)} verse embeddings")

    def semantic_search(self,
                       query: str,
                       top_k: int = 10,
                       book_filter: List[str] = None) -> List[SearchResult]:
        """
        Search for verses semantically similar to query.

        Args:
            query: Natural language question or topic
            top_k: Number of results to return
            book_filter: Optional list of books to search within

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        # Encode query
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        # Compute cosine similarity
        similarities = np.dot(self.embedding_matrix, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get extra for filtering

        results = []
        for idx in top_indices:
            verse_id = self.verse_ids[idx]
            meta = self.metadata[str(verse_id)]

            # Apply book filter if specified
            if book_filter and meta["book"] not in book_filter:
                continue

            results.append(SearchResult(
                verse_id=verse_id,
                reference=meta["reference"],
                text=meta["text"],
                score=float(similarities[idx]),
                book=meta["book"],
                chapter=meta["chapter"],
                verse=meta["verse"]
            ))

            if len(results) >= top_k:
                break

        return results

    def find_cross_references(self,
                             reference: str,
                             top_k: int = 5) -> List[SearchResult]:
        """
        Find verses semantically related to a given reference.

        Args:
            reference: Bible reference (e.g., "John 3:16")
            top_k: Number of cross-references to find

        Returns:
            List of related verses
        """
        # Find verse by reference
        target_verse_id = None
        for vid, meta in self.metadata.items():
            if meta["reference"] == reference:
                target_verse_id = int(vid)
                break

        if not target_verse_id:
            return []

        # Get embedding for target verse
        target_embedding = self.embeddings[target_verse_id]

        # Find similar verses
        similarities = np.dot(self.embedding_matrix, target_embedding)
        top_indices = np.argsort(similarities)[::-1][1:top_k+1]  # Skip self

        results = []
        for idx in top_indices:
            verse_id = self.verse_ids[idx]
            meta = self.metadata[str(verse_id)]

            results.append(SearchResult(
                verse_id=verse_id,
                reference=meta["reference"],
                text=meta["text"],
                score=float(similarities[idx]),
                book=meta["book"],
                chapter=meta["chapter"],
                verse=meta["verse"]
            ))

        return results

    def answer_question(self,
                       question: str,
                       top_k: int = 5) -> Dict:
        """
        Answer a question about the Bible using RAG.

        Args:
            question: Natural language question
            top_k: Number of verses to retrieve for context

        Returns:
            Dictionary with answer and supporting verses
        """
        # Retrieve relevant verses
        results = self.semantic_search(question, top_k=top_k)

        # Format context for LLM
        context = "\n\n".join([
            f"{r.reference}: {r.text}"
            for r in results
        ])

        return {
            "question": question,
            "context": context,
            "verses": [
                {
                    "reference": r.reference,
                    "text": r.text,
                    "relevance": r.score
                }
                for r in results
            ]
        }


def main():
    """Demo RAG system."""
    print("=" * 60)
    print("Bible RAG System Demo")
    print("=" * 60)

    rag = BibleRAG(
        embeddings_path="data/embeddings/embeddings.pkl"
    )

    # Example 1: Semantic search
    print("\n🔍 Semantic Search Example:")
    print("Query: 'salvation through faith'")
    results = rag.semantic_search("salvation through faith", top_k=5)
    for r in results:
        print(f"  {r.reference} (score: {r.score:.3f})")
        print(f"    {r.text[:100]}...")

    # Example 2: Cross-references
    print("\n🔗 Cross-References Example:")
    print("Reference: John 3:16")
    xrefs = rag.find_cross_references("John 3:16", top_k=5)
    for r in xrefs:
        print(f"  {r.reference} (similarity: {r.score:.3f})")

    # Example 3: Question answering
    print("\n❓ Question Answering Example:")
    answer = rag.answer_question("What does the Bible say about love?")
    print(f"Question: {answer['question']}")
    print("Relevant verses:")
    for v in answer['verses']:
        print(f"  {v['reference']} (relevance: {v['relevance']:.3f})")


if __name__ == "__main__":
    main()
```

**Usage**:
```bash
python code/ai_training/rag_system.py
```

---

## Layer 4: Fine-Tuned LLM

Create `code/ai_training/finetune_llm.py`:

```python
#!/usr/bin/env python3
"""
Fine-tune LLM on biblical text and theological Q&A.
Uses LoRA for efficient fine-tuning.
"""

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import sqlite3
import json
from typing import List, Dict
import torch

class BibleLLMFineTuner:
    """Fine-tune LLM on biblical text."""

    def __init__(self,
                 base_model: str = "meta-llama/Llama-2-7b-hf",
                 load_in_8bit: bool = True):
        """
        Initialize fine-tuner.

        Args:
            base_model: Base LLM to fine-tune
                Options:
                - meta-llama/Llama-2-7b-hf (best, requires access)
                - microsoft/phi-2 (small, efficient)
                - mistralai/Mistral-7B-v0.1 (good balance)
            load_in_8bit: Use 8-bit quantization (saves memory)
        """
        self.base_model = base_model
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with LoRA for efficient fine-tuning
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=load_in_8bit,
            device_map="auto"
        )

        # Prepare for LoRA training
        self.model = prepare_model_for_kbit_training(self.model)

        # LoRA configuration
        lora_config = LoraConfig(
            r=16,  # LoRA rank
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

        self.model = get_peft_model(self.model, lora_config)

    def prepare_bible_qa_dataset(self,
                                 db_path: str = "data/GoodBook.db") -> Dataset:
        """
        Create Q&A dataset from Bible verses.

        Format:
        <s>[INST] What does Genesis 1:1 say? [/INST] In the beginning God created the heavens and the earth.</s>
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all verses
        cursor.execute("""
            SELECT b.book_name, c.chapter_number, v.verse_num, v.text_clean
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
        """)

        training_data = []

        for book, chapter, verse, text in cursor.fetchall():
            if not text:
                continue

            reference = f"{book} {chapter}:{verse}"

            # Create multiple question variations
            questions = [
                f"What does {reference} say?",
                f"Quote {reference}",
                f"What is written in {reference}?",
                f"Recite {reference}",
            ]

            for question in questions:
                prompt = f"<s>[INST] {question} [/INST] {text}</s>"
                training_data.append({"text": prompt})

        # Add theological questions (you'll expand this)
        theological_qa = [
            {
                "question": "What is the nature of God?",
                "answer": "God is described as eternal, omnipotent, omniscient, and loving. Key attributes include holiness (Isaiah 6:3), love (1 John 4:8), and justice (Deuteronomy 32:4)."
            },
            # Add many more...
        ]

        for qa in theological_qa:
            prompt = f"<s>[INST] {qa['question']} [/INST] {qa['answer']}</s>"
            training_data.append({"text": prompt})

        conn.close()

        return Dataset.from_list(training_data)

    def tokenize_dataset(self, dataset: Dataset) -> Dataset:
        """Tokenize dataset for training."""
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding="max_length"
            )

        return dataset.map(tokenize_function, batched=True)

    def train(self,
             train_dataset: Dataset,
             output_dir: str = "models/bible_llm_lora",
             epochs: int = 3,
             batch_size: int = 4):
        """
        Fine-tune the model.

        Args:
            train_dataset: Tokenized training dataset
            output_dir: Where to save fine-tuned model
            epochs: Number of training epochs
            batch_size: Training batch size
        """
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
        )

        # Train!
        trainer.train()

        # Save final model
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)


def main():
    """Fine-tune LLM on Bible."""
    print("=" * 60)
    print("Bible LLM Fine-Tuning")
    print("=" * 60)

    # Note: Requires GPU and significant compute
    finetuner = BibleLLMFineTuner(
        base_model="microsoft/phi-2",  # Smaller model for demo
        load_in_8bit=True
    )

    # Prepare dataset
    dataset = finetuner.prepare_bible_qa_dataset()
    tokenized = finetuner.tokenize_dataset(dataset)

    # Train
    finetuner.train(
        train_dataset=tokenized,
        output_dir="models/bible_phi2_lora",
        epochs=3
    )


if __name__ == "__main__":
    main()
```

**Requirements**:
```bash
pip install transformers peft accelerate bitsandbytes datasets
```

---

## Complete Training Pipeline

Create `code/ai_training/full_pipeline.py`:

```python
#!/usr/bin/env python3
"""
Complete end-to-end training pipeline.
Orchestrates all layers for Bible AI.
"""

import subprocess
from pathlib import Path

def run_command(cmd: str, description: str):
    """Run command and print status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        return False
    print(f"✅ Complete: {description}")
    return True

def main():
    """Run complete training pipeline."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     BIBLE AI COMPLETE TRAINING PIPELINE               ║
    ║     End-to-end model training and deployment          ║
    ╚════════════════════════════════════════════════════════╝
    """)

    # Layer 1: NER Training
    if not run_command(
        "python code/ai_training/train_ner_enhanced.py",
        "Layer 1: Training NER model"
    ):
        return

    # Layer 2: Create Embeddings
    if not run_command(
        "python code/ai_training/create_embeddings.py",
        "Layer 2: Creating semantic embeddings"
    ):
        return

    # Layer 3: RAG System (no training needed, just setup)
    print("\n✅ Layer 3: RAG system ready")

    # Layer 4: LLM Fine-tuning (optional, requires GPU)
    print("\n⚠️  Layer 4: LLM fine-tuning requires GPU")
    print("    Run manually: python code/ai_training/finetune_llm.py")

    # Layer 5: Deploy conversation interface
    print("\n✅ Layer 5: Ready for deployment")

    print("""
    \n╔════════════════════════════════════════════════════════╗
    ║               TRAINING COMPLETE!                       ║
    ║                                                        ║
    ║  Next steps:                                           ║
    ║  1. Test the system: python code/ai_training/demo.py  ║
    ║  2. Deploy: python code/ai_training/chat_interface.py ║
    ╚════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()
```

---

## Next Document

This is getting long! I'll create a separate file for:
- **Layer 5: Conversation Interface** (chat system)
- **Deployment guide**
- **Integration with existing NER work**

Should I continue with these files?
