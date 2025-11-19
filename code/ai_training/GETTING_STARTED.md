# Getting Started with Bible AI Training

This guide will help you build a conversational Bible AI from scratch.

## Prerequisites

1. **Python 3.8+** (you have Python 3.11 ✓)
2. **Bible Database** (`data/GoodBook.db`) - Created from your existing pipeline
3. **~2GB disk space** for models and embeddings

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
# Option A: Automatic (recommended)
chmod +x code/ai_training/install_dependencies.sh
./code/ai_training/install_dependencies.sh

# Option B: Manual
pip3 install sentence-transformers numpy tqdm
pip3 install openai  # Optional: for chat with GPT-4
```

### Step 2: Create Embeddings

This is the MOST IMPORTANT step - it enables semantic search.

```bash
# Create embeddings for all Bible verses (~10-15 minutes on CPU)
python3 code/ai_training/create_embeddings.py
```

**What this does:**
- Encodes all 31,000+ Bible verses as vectors
- Enables semantic similarity search
- Saves to `data/embeddings/`

**Output:**
```
✅ Found 31,102 verses
✅ Encoding 31,102 verses into vectors...
✅ All embeddings saved to data/embeddings/
```

### Step 3: Start Using Your AI!

```bash
# Option A: Demo mode (no API key needed)
python3 code/ai_training/chat_interface.py --demo

# Option B: Interactive RAG search
python3 code/ai_training/rag_system.py --interactive

# Option C: With OpenAI GPT-4
export OPENAI_API_KEY="sk-..."
python3 code/ai_training/chat_interface.py
```

---

## What Can You Do?

### 1. Semantic Search

Find verses by meaning, not just keywords:

```bash
python3 code/ai_training/rag_system.py --query "God's love for humanity"
```

**Output:**
```
1. John 3:16 (score: 0.856)
   For God so loved the world...

2. Romans 5:8 (score: 0.823)
   But God demonstrates His own love...

3. 1 John 4:10 (score: 0.811)
   This is love: not that we loved God...
```

### 2. Cross-References

Find related verses automatically:

```python
from rag_system import BibleRAG

rag = BibleRAG()
xrefs = rag.find_cross_references("John 3:16", top_k=5)
for r in xrefs:
    print(f"{r.reference}: {r.text}")
```

### 3. Question Answering

Ask questions about the Bible:

```bash
python3 code/ai_training/chat_interface.py
```

```
💬 You: What does the Bible say about faith?

🤖 Bible AI:
   Based on these verses:

   Hebrews 11:1: Now faith is the substance of things hoped for...
   Romans 10:17: So then faith comes by hearing...
   James 2:17: Thus also faith by itself, if it does not have works...

   Faith is described as confidence in what we hope for...
```

---

## Full Pipeline (All Layers)

Want to run everything?

```bash
python3 code/ai_training/full_pipeline.py
```

This runs:
1. ✓ Check prerequisites
2. ✓ Create embeddings (Layer 2)
3. ✓ Test RAG system (Layer 3)
4. ✓ Test chat interface (Layer 5)

**Note**: NER training (Layer 1) and LLM fine-tuning (Layer 4) are optional.

---

## Understanding the System

### What You Have Now

**Your current work (NER annotation):**
```
Prodigy Annotation
    ↓
Gold Dataset (high-quality entity labels)
    ↓
NER Model (recognizes 65 entity types)
```

**What we're adding:**
```
Semantic Embeddings
    ↓
RAG System (smart verse retrieval)
    ↓
Chat Interface (conversational AI)
```

### How They Work Together

```
User Question: "What does the Bible say about love?"
         ↓
    1. Convert question to vector (embedding)
         ↓
    2. Search for similar verse vectors (RAG)
         ↓
    3. Retrieve top 5 relevant verses
         ↓
    4. (Optional) Use NER to highlight entities
         ↓
    5. Generate response with context
         ↓
    Answer with relevant verses!
```

---

## Configuration Options

### Embedding Models

**Default** (best quality):
```bash
python3 code/ai_training/create_embeddings.py --model all-mpnet-base-v2
```
- 768 dimensions
- ~15 minutes on CPU
- Best semantic understanding

**Fast** (smaller, faster):
```bash
python3 code/ai_training/create_embeddings.py --model all-MiniLM-L6-v2
```
- 384 dimensions
- ~8 minutes on CPU
- 90% of the quality, 2x faster

### Context Options

**With context** (recommended):
```bash
python3 code/ai_training/create_embeddings.py
```
Embeds: "John 3:16 - For God so loved the world..."

**Without context**:
```bash
python3 code/ai_training/create_embeddings.py --no-context
```
Embeds: "For God so loved the world..."

---

## Common Issues

### Issue: "Database not found"

**Problem:**
```
❌ Error: Database not found at data/GoodBook.db
```

**Solution:**
1. Check if database exists: `ls -lh data/GoodBook.db`
2. If not, you need to create it first using your bible scraper
3. Or specify custom path: `--db path/to/your/bible.db`

### Issue: "sentence-transformers not installed"

**Solution:**
```bash
pip3 install sentence-transformers
```

### Issue: "CUDA out of memory"

**Solution:**
```bash
# Use smaller batch size
python3 code/ai_training/create_embeddings.py --batch-size 16
```

### Issue: "Embeddings not found"

**Problem:**
```
❌ Error: Embeddings not found at data/embeddings/embeddings.pkl
```

**Solution:**
```bash
# Create embeddings first
python3 code/ai_training/create_embeddings.py
```

---

## Advanced Usage

### Search Within Specific Books

```python
from rag_system import BibleRAG

rag = BibleRAG()
results = rag.search_by_book("Psalms", "God's protection", top_k=5)
```

### Get Verse with Context

```python
context = rag.get_verse_context("John 3:16", context_verses=2)
print(context["before"])  # 2 verses before
print(context["text"])    # The verse itself
print(context["after"])   # 2 verses after
```

### Custom Search Parameters

```python
results = rag.semantic_search(
    query="salvation",
    top_k=10,
    book_filter=["Romans", "Ephesians"],
    min_score=0.7
)
```

---

## Performance Expectations

| Task | Time (CPU) | Time (GPU) | Storage |
|------|-----------|------------|---------|
| Install dependencies | 2-3 min | 2-3 min | ~500 MB |
| Create embeddings | 10-15 min | 2-3 min | ~100 MB |
| Semantic search | <1 sec | <0.1 sec | - |
| RAG retrieval | <2 sec | <0.5 sec | - |
| Chat response (API) | 2-5 sec | 2-5 sec | - |

**Total setup time: ~15-20 minutes**

---

## Testing Your Installation

### 1. Test Embeddings

```bash
python3 -c "
from rag_system import BibleRAG
rag = BibleRAG()
print('✅ Embeddings loaded successfully!')
print(f'   Total verses: {len(rag.embeddings):,}')
"
```

### 2. Test Search

```bash
python3 code/ai_training/rag_system.py --query "love"
```

### 3. Test Chat

```bash
python3 code/ai_training/chat_interface.py --demo
```

---

## Next Steps

1. **Create embeddings** (if you haven't):
   ```bash
   python3 code/ai_training/create_embeddings.py
   ```

2. **Try the demo**:
   ```bash
   python3 code/ai_training/chat_interface.py --demo
   ```

3. **Continue Prodigy annotation** to improve NER:
   ```bash
   prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl
   ```

4. **Integrate with your work**:
   - Your NER entities can enhance the RAG system
   - Better entity recognition = smarter AI responses

---

## Getting Help

If you run into issues:

1. Check this guide first
2. Read the architecture doc: `DOCUMENTATION/AI_TRAINING_ARCHITECTURE.md`
3. Run tests: `python3 code/ai_training/full_pipeline.py --test-only`

---

## What's Optional vs Required

**Required (for basic chat):**
- ✅ Bible database (`data/GoodBook.db`)
- ✅ Embeddings (`python3 code/ai_training/create_embeddings.py`)
- ✅ sentence-transformers package

**Optional (for enhanced features):**
- ⭐ NER model (from Prodigy annotation)
- ⭐ OpenAI API (for GPT-4 responses)
- ⭐ LLM fine-tuning (requires GPU)

**You can start with just the required items and add optional features later!**

---

**Ready to begin? Run this:**

```bash
# 1. Install dependencies
pip3 install sentence-transformers numpy tqdm

# 2. Create embeddings
python3 code/ai_training/create_embeddings.py

# 3. Chat!
python3 code/ai_training/chat_interface.py --demo
```

**Estimated time: 15-20 minutes** ⏱️

Good luck! 🚀
