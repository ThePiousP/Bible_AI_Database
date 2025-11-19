# Bible AI Training - Quick Start Guide

## Goal

Build an AI that deeply understands the Bible and can discuss it with you.

## Architecture

Your Bible AI has **5 layers** that work together:

```
Layer 1: NER (Entity Recognition)      ← YOU ARE HERE (Prodigy annotation)
Layer 2: Semantic Embeddings            ← Next step
Layer 3: RAG System (Retrieval)         ← Smart verse search
Layer 4: Fine-Tuned LLM (Optional)      ← Deep understanding
Layer 5: Chat Interface                 ← Talk to your AI
```

---

## Step-by-Step Implementation

### Prerequisites

```bash
# Install core dependencies
pip install -r requirements.txt

# Install AI training dependencies
pip install sentence-transformers openai anthropic torch transformers peft
```

---

### Step 1: Complete NER Training (Layer 1)

**You're working on this now!**

```bash
# 1. Generate silver dataset (auto-labeled)
python code/silver_export.py \
    --db data/GoodBook.db \
    --rules label_rules.yml \
    --outdir silver_out

# 2. Annotate with Prodigy (creates gold dataset)
prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl \
    --label DEITY,PERSON,LOCATION \
    --patterns ./prodigy_patterns.jsonl

# 3. Export gold annotations
prodigy db-out bible_gold > output/gold_annotations.jsonl

# 4. Train NER model (silver + gold)
python code/train_baseline_spacy.py \
    --train silver_out/train.jsonl \
    --gold output/gold_annotations.jsonl \
    --dev silver_out/dev.jsonl \
    --test silver_out/test.jsonl \
    --output models/ner_biblical_v1
```

**Output**: Trained NER model that recognizes 65 biblical entity types

---

### Step 2: Create Semantic Embeddings (Layer 2)

This creates vector representations of every Bible verse for semantic search.

```bash
# Create embeddings for all verses
python code/ai_training/create_embeddings.py
```

**What it does**:
- Encodes all 31,000+ verses as vectors
- Enables semantic similarity search
- Saves to `data/embeddings/`

**Time**: ~10-15 minutes on CPU

---

### Step 3: Set Up RAG System (Layer 3)

No training needed! The RAG system uses the embeddings you created.

```bash
# Test RAG system
python code/ai_training/rag_system.py
```

**What it does**:
- Searches Bible semantically (not just keywords)
- Finds cross-references automatically
- Retrieves relevant context for questions

**Example**:
```python
from rag_system import BibleRAG

rag = BibleRAG()

# Semantic search
results = rag.semantic_search("salvation through faith", top_k=5)
for r in results:
    print(f"{r.reference}: {r.text}")

# Cross-references
xrefs = rag.find_cross_references("John 3:16", top_k=5)
```

---

### Step 4: Fine-Tune LLM (Layer 4) - OPTIONAL

**Warning**: Requires GPU and significant compute (skip for now if no GPU)

```bash
# Fine-tune on biblical text
python code/ai_training/finetune_llm.py
```

**What it does**:
- Trains LLM on Bible verses and Q&A
- Uses LoRA for efficient training
- Creates Bible-specialized language model

**Requirements**:
- GPU with 16GB+ VRAM
- ~8-12 hours training time
- Or use cloud GPU (Colab, Runpod, etc.)

**Alternative**: Use OpenAI API or Anthropic Claude (no training needed)

---

### Step 5: Chat with Your Bible AI (Layer 5)

```bash
# Interactive chat mode
python code/ai_training/chat_interface.py

# Demo mode (no API key needed)
python code/ai_training/chat_interface.py --demo

# With OpenAI API
export OPENAI_API_KEY="sk-..."
python code/ai_training/chat_interface.py
```

**What you can ask**:
- "What does the Bible say about love?"
- "Tell me about David and Goliath"
- "Explain John 3:16"
- "What is salvation?"
- "Find verses about faith"

---

## Quick Start (Minimum Viable Product)

If you want to get something working RIGHT NOW:

```bash
# 1. Create embeddings (required)
python code/ai_training/create_embeddings.py

# 2. Chat! (RAG-only mode, no LLM needed)
python code/ai_training/chat_interface.py --demo
```

This gives you:
- ✅ Semantic verse search
- ✅ Contextual answers
- ✅ Cross-reference finding
- ❌ No conversational AI (just retrieval)

To add conversational AI:
```bash
export OPENAI_API_KEY="sk-..."
python code/ai_training/chat_interface.py
```

---

## Full Pipeline (Production-Ready)

Run everything in sequence:

```bash
# Complete pipeline script
python code/ai_training/full_pipeline.py
```

This runs:
1. NER training (if gold data exists)
2. Embeddings creation
3. RAG system setup
4. (Optional) LLM fine-tuning

---

## Understanding the Code

### Layer 1: NER (What You're Doing Now)

**Purpose**: Identify entities (people, places, concepts)

**Files**:
- `code/silver_export.py` - Generate auto-labeled data
- `code/train_baseline_spacy.py` - Train NER model
- `prodigy_patterns.jsonl` - 2,833 entity patterns

**Why it matters**: Structured knowledge extraction

### Layer 2: Embeddings

**Purpose**: Convert verses to vectors for semantic search

**Files**:
- `code/ai_training/create_embeddings.py`

**Model**: `all-mpnet-base-v2` (768-dimensional vectors)

**Why it matters**: Finds verses by meaning, not just keywords

### Layer 3: RAG

**Purpose**: Retrieve relevant verses for any question

**Files**:
- `code/ai_training/rag_system.py`

**How it works**:
1. User asks question
2. Convert question to vector
3. Find similar verse vectors
4. Return relevant verses

**Why it matters**: Provides accurate context for answers

### Layer 4: Fine-Tuned LLM

**Purpose**: Generate natural, theologically-informed responses

**Files**:
- `code/ai_training/finetune_llm.py`

**Approach**: LoRA fine-tuning on Llama-2 or similar

**Why it matters**: Deep biblical language understanding

**Alternative**: Use GPT-4 API (no training needed)

### Layer 5: Chat Interface

**Purpose**: Interactive conversation with your Bible AI

**Files**:
- `code/ai_training/chat_interface.py`

**Features**:
- Question answering
- Verse lookup
- Cross-references
- Theological discussion

---

## Integration with Your Current Work

Your **Prodigy NER annotation** feeds into the system like this:

```
Your Prodigy Work
      ↓
Gold Annotations (high quality)
      ↓
Combined with Silver Data (auto-generated)
      ↓
Train NER Model
      ↓
Extract Entities from Verses
      ↓
Enhance Embeddings with Entity Info
      ↓
Better Semantic Search
      ↓
More Accurate RAG Retrieval
      ↓
Smarter AI Conversations
```

**The better your NER annotations, the smarter your AI becomes!**

---

## Testing Each Layer

### Test Layer 1 (NER)

```python
import spacy

nlp = spacy.load("models/ner_biblical_v1/best")
text = "In the beginning God created the heavens and the earth."
doc = nlp(text)

for ent in doc.ents:
    print(f"{ent.text} -> {ent.label_}")
# Output: God -> DEITY
```

### Test Layer 2 (Embeddings)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-mpnet-base-v2")
verse = "For God so loved the world..."
embedding = model.encode(verse)
print(embedding.shape)  # (768,)
```

### Test Layer 3 (RAG)

```python
from code.ai_training.rag_system import BibleRAG

rag = BibleRAG()
results = rag.semantic_search("God's love", top_k=3)
for r in results:
    print(r.reference, r.score)
```

### Test Layer 5 (Chat)

```bash
python code/ai_training/chat_interface.py --demo
```

---

## Performance Expectations

| Component | Time | Resources |
|-----------|------|-----------|
| NER Training | 10-30 min | CPU OK |
| Create Embeddings | 10-15 min | CPU OK |
| RAG Search | <1 sec | CPU OK |
| LLM Fine-tune | 8-12 hours | GPU required |
| Chat Response | 2-5 sec | CPU OK (with API) |

---

## Common Issues

### Issue: "RAG system not available"

**Solution**: Create embeddings first
```bash
python code/ai_training/create_embeddings.py
```

### Issue: "No module named sentence_transformers"

**Solution**: Install dependencies
```bash
pip install sentence-transformers
```

### Issue: "CUDA out of memory"

**Solution**: Use smaller batch size or CPU
```python
# In create_embeddings.py
embeddings = model.encode(texts, batch_size=16)  # Reduce from 32
```

### Issue: "No relevant verses found"

**Solution**: Check embeddings exist
```bash
ls -lh data/embeddings/
```

---

## Next Steps After This Guide

1. **Improve NER**: Continue Prodigy annotation for better entity recognition
2. **Expand theological Q&A**: Add more training questions to `finetune_llm.py`
3. **Add conversation memory**: Track context across multiple questions
4. **Create web interface**: Deploy as a website or mobile app
5. **Add audio**: Text-to-speech for verse recitation

---

## Resources

- **Sentence Transformers**: https://www.sbert.net/
- **LoRA Fine-tuning**: https://github.com/microsoft/LoRA
- **RAG Guide**: https://www.pinecone.io/learn/retrieval-augmented-generation/
- **spaCy NER**: https://spacy.io/usage/training

---

**Created**: 2025-11-16
**Status**: Ready for implementation
**Estimated Total Time**: 2-3 hours (without LLM fine-tuning)
