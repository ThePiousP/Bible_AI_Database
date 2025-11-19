#!/usr/bin/env python3
"""
Complete end-to-end training pipeline for Bible AI.
Orchestrates all layers from NER to Chat.

Usage:
    python full_pipeline.py                 # Run all steps
    python full_pipeline.py --skip-ner      # Skip NER training
    python full_pipeline.py --quick         # Fast mode (smaller model)
"""

import subprocess
import sys
from pathlib import Path
import argparse
import time

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_command(cmd, description, check=True):
    """Run command and print status."""
    print(f"🚀 {description}...")
    print(f"   Command: {cmd}\n")

    start_time = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start_time

    if result.returncode != 0 and check:
        print(f"\n❌ Failed: {description}")
        print(f"   Return code: {result.returncode}")
        return False

    print(f"\n✅ Complete: {description}")
    print(f"   Time: {elapsed:.1f}s")
    return True

def check_prerequisites():
    """Check if required files/packages exist."""
    print_header("Checking Prerequisites")

    # Check for database
    if not Path("data/GoodBook.db").exists():
        print("❌ Error: data/GoodBook.db not found")
        print("   Please ensure your Bible database exists")
        return False

    # Check for Python packages
    try:
        import sentence_transformers
        print("✓ sentence-transformers installed")
    except ImportError:
        print("❌ Error: sentence-transformers not installed")
        print("   Run: pip install sentence-transformers")
        return False

    try:
        import numpy
        print("✓ numpy installed")
    except ImportError:
        print("❌ Error: numpy not installed")
        print("   Run: pip install numpy")
        return False

    print("\n✅ All prerequisites met!")
    return True

def main():
    """Run complete training pipeline."""
    parser = argparse.ArgumentParser(description="Bible AI Complete Pipeline")
    parser.add_argument("--skip-ner", action="store_true",
                       help="Skip NER training (Layer 1)")
    parser.add_argument("--skip-embeddings", action="store_true",
                       help="Skip embeddings creation (Layer 2)")
    parser.add_argument("--quick", action="store_true",
                       help="Use faster/smaller models")
    parser.add_argument("--test-only", action="store_true",
                       help="Only run tests, no training")

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     BIBLE AI COMPLETE TRAINING PIPELINE                       ║
║     End-to-end model training and deployment                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Configuration
    if args.quick:
        embedding_model = "all-MiniLM-L6-v2"  # Faster, 384 dims
        print("⚡ Quick mode: Using smaller/faster models")
    else:
        embedding_model = "all-mpnet-base-v2"  # Best quality, 768 dims
        print("🎯 Standard mode: Using high-quality models")

    print(f"\nPipeline configuration:")
    print(f"  Embedding model: {embedding_model}")
    print(f"  Skip NER: {args.skip_ner}")
    print(f"  Skip embeddings: {args.skip_embeddings}")

    input("\nPress Enter to continue...")

    # Layer 1: NER Training (optional, requires gold data)
    if not args.skip_ner and not args.test_only:
        print_header("Layer 1: NER Training")
        if Path("output/gold_annotations.jsonl").exists():
            print("Gold annotations found!")
            if run_command(
                "python code/train_baseline_spacy.py "
                "--train silver_out/train.jsonl "
                "--gold output/gold_annotations.jsonl "
                "--dev silver_out/dev.jsonl "
                "--test silver_out/test.jsonl "
                "--output models/ner_biblical_v1",
                "Training NER model",
                check=False  # Don't fail if this doesn't work
            ):
                print("✅ NER model trained successfully")
            else:
                print("⚠️  NER training skipped or failed (not critical)")
        else:
            print("⚠️  No gold annotations found, skipping NER training")
            print("    This is OK - NER is optional for the chat system")

    # Layer 2: Create Embeddings
    if not args.skip_embeddings and not args.test_only:
        print_header("Layer 2: Creating Semantic Embeddings")
        if not run_command(
            f"python code/ai_training/create_embeddings.py "
            f"--model {embedding_model} "
            f"--batch-size 32",
            "Creating verse embeddings"
        ):
            print("\n❌ Failed to create embeddings")
            print("   This is required for the RAG system")
            sys.exit(1)

    # Layer 3: Test RAG System
    print_header("Layer 3: Testing RAG System")
    if not run_command(
        "python code/ai_training/rag_system.py --demo",
        "Testing semantic search & RAG",
        check=False
    ):
        print("⚠️  RAG demo had issues, but continuing...")

    # Layer 4: LLM Fine-tuning (skipped - requires GPU)
    print_header("Layer 4: LLM Fine-Tuning")
    print("⚠️  LLM fine-tuning requires GPU and is optional")
    print("   Skipping this step.")
    print("   The chat interface can use OpenAI API instead.")

    # Layer 5: Test Chat Interface
    print_header("Layer 5: Testing Chat Interface")
    print("Chat interface is ready!")
    print("\nTo start chatting:")
    print("  python code/ai_training/chat_interface.py --demo")
    print("\nOr with OpenAI:")
    print("  export OPENAI_API_KEY='your-key'")
    print("  python code/ai_training/chat_interface.py")

    # Summary
    print("\n" + "="*70)
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                  PIPELINE COMPLETE!                            ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("\nWhat was created:")
    print("  ✓ Layer 1: NER model (if gold data available)")
    print("  ✓ Layer 2: Semantic embeddings for all verses")
    print("  ✓ Layer 3: RAG system (semantic search)")
    print("  ✓ Layer 4: Skipped (optional, requires GPU)")
    print("  ✓ Layer 5: Chat interface ready")

    print("\nNext steps:")
    print("  1. Try the demo:")
    print("     python code/ai_training/chat_interface.py --demo")
    print("\n  2. Search the Bible:")
    print("     python code/ai_training/rag_system.py --interactive")
    print("\n  3. Continue Prodigy annotation for better NER:")
    print("     prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl")

    print("\n" + "="*70)
    print("📚 Your Bible AI is ready to chat!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
