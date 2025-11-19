#!/usr/bin/env python3
"""
Create semantic embeddings for all Bible verses.
Enables similarity search and semantic understanding.

Usage:
    python create_embeddings.py
    python create_embeddings.py --model all-MiniLM-L6-v2  # Faster, smaller
    python create_embeddings.py --no-context              # Without book/chapter context
"""

import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
from tqdm import tqdm
from typing import List, Dict, Tuple
import pickle
import argparse
import sys

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
                - all-mpnet-base-v2 (best quality, 768 dims) [RECOMMENDED]
                - all-MiniLM-L6-v2 (faster, 384 dims)
                - multi-qa-mpnet-base-dot-v1 (Q&A optimized)
            db_path: Path to Bible database
        """
        print(f"Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.db_path = db_path
        self.embeddings = {}
        self.metadata = {}

        print(f"✓ Model loaded: {model_name}")
        print(f"  Embedding dimensions: {self.model.get_sentence_embedding_dimension()}")

    def create_verse_embeddings(self,
                                include_context: bool = True,
                                batch_size: int = 32) -> Dict:
        """
        Create embeddings for all verses.

        Args:
            include_context: Add book/chapter context to embedding
            batch_size: Number of verses to encode at once

        Returns:
            Dictionary with statistics
        """
        # Check if database exists
        if not Path(self.db_path).exists():
            print(f"❌ Error: Database not found at {self.db_path}")
            print("   Make sure GoodBook.db exists in the data/ directory")
            sys.exit(1)

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
                v.text_plain,
                v.text
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            ORDER BY b.id, c.chapter_number, v.verse_num
        """

        print("\nFetching verses from database...")
        cursor.execute(query)
        verses = cursor.fetchall()

        print(f"✓ Found {len(verses):,} verses")

        texts_to_embed = []
        verse_ids = []

        print("\nPreparing verse texts...")
        for verse_id, book, chapter, verse_num, text_clean, text_plain, text in tqdm(verses, desc="Processing"):
            # Use clean text if available, fallback to plain, then to text
            verse_text = text_clean or text_plain or text

            if not verse_text:
                continue

            if include_context:
                # Add context for better semantic understanding
                context_text = f"{book} {chapter}:{verse_num} - {verse_text}"
            else:
                context_text = verse_text

            texts_to_embed.append(context_text)
            verse_ids.append(verse_id)

            # Store metadata
            self.metadata[verse_id] = {
                "book": book,
                "chapter": chapter,
                "verse": verse_num,
                "text": verse_text,
                "reference": f"{book} {chapter}:{verse_num}"
            }

        # Create embeddings in batches (faster)
        print(f"\nEncoding {len(texts_to_embed):,} verses into vectors...")
        print(f"Batch size: {batch_size}")
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )

        # Store embeddings
        print("\nStoring embeddings...")
        for verse_id, embedding in zip(verse_ids, embeddings):
            self.embeddings[verse_id] = embedding

        conn.close()

        return {
            "total_verses": len(verses),
            "embedded_verses": len(self.embeddings),
            "embedding_dim": embeddings.shape[1],
            "model": self.model.get_sentence_embedding_dimension()
        }

    def save_embeddings(self, output_dir: str = "data/embeddings"):
        """Save embeddings and metadata to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving embeddings to {output_path}/...")

        # Save embeddings (numpy format)
        embeddings_array = np.array(list(self.embeddings.values()))
        verse_ids = list(self.embeddings.keys())

        np.save(output_path / "embeddings.npy", embeddings_array)
        print(f"  ✓ Saved embeddings.npy ({embeddings_array.nbytes / 1024 / 1024:.1f} MB)")

        # Save verse IDs and metadata
        with open(output_path / "verse_ids.json", "w") as f:
            json.dump(verse_ids, f)
        print(f"  ✓ Saved verse_ids.json")

        with open(output_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
        print(f"  ✓ Saved metadata.json")

        # Save as pickle for easy loading
        with open(output_path / "embeddings.pkl", "wb") as f:
            pickle.dump({
                "embeddings": self.embeddings,
                "metadata": self.metadata,
                "model_name": self.model._modules['0'].auto_model.name_or_path
            }, f)
        print(f"  ✓ Saved embeddings.pkl")

        # Save info file
        info = {
            "total_verses": len(self.embeddings),
            "embedding_dim": embeddings_array.shape[1],
            "model": self.model._modules['0'].auto_model.name_or_path,
            "files": [
                "embeddings.npy",
                "verse_ids.json",
                "metadata.json",
                "embeddings.pkl"
            ]
        }
        with open(output_path / "info.json", "w") as f:
            json.dump(info, f, indent=2)
        print(f"  ✓ Saved info.json")

        print(f"\n✅ All embeddings saved to {output_path}/")


def main():
    """Create Bible embeddings."""
    parser = argparse.ArgumentParser(description="Create Bible verse embeddings")
    parser.add_argument("--model", default="all-mpnet-base-v2",
                       help="Sentence transformer model name")
    parser.add_argument("--db", default="data/GoodBook.db",
                       help="Path to Bible database")
    parser.add_argument("--output", default="data/embeddings",
                       help="Output directory for embeddings")
    parser.add_argument("--no-context", action="store_true",
                       help="Don't include book/chapter context")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Batch size for encoding")

    args = parser.parse_args()

    print("=" * 70)
    print("Bible Semantic Embeddings Creator")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model: {args.model}")
    print(f"  Database: {args.db}")
    print(f"  Output: {args.output}")
    print(f"  Include context: {not args.no_context}")
    print(f"  Batch size: {args.batch_size}")

    creator = BibleEmbeddingsCreator(
        model_name=args.model,
        db_path=args.db
    )

    # Create embeddings
    stats = creator.create_verse_embeddings(
        include_context=not args.no_context,
        batch_size=args.batch_size
    )

    print(f"\n{'='*70}")
    print("Embedding Statistics")
    print('='*70)
    print(f"  Total verses in database: {stats['total_verses']:,}")
    print(f"  Verses embedded: {stats['embedded_verses']:,}")
    print(f"  Embedding dimensions: {stats['embedding_dim']}")
    print(f"  Total size: {stats['embedded_verses'] * stats['embedding_dim'] * 4 / 1024 / 1024:.1f} MB")

    # Save
    creator.save_embeddings(args.output)

    print("\n" + "="*70)
    print("✅ Complete! Embeddings ready for use.")
    print("="*70)
    print("\nNext steps:")
    print("  1. Test embeddings: python code/ai_training/rag_system.py")
    print("  2. Start chatbot: python code/ai_training/chat_interface.py")


if __name__ == "__main__":
    main()
