#!/usr/bin/env python3
"""
RAG system for Bible Q&A.
Retrieves relevant verses and generates contextual answers.

Usage:
    python rag_system.py                    # Run demo
    python rag_system.py --query "love"     # Search for topic
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import argparse
import sys

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
        # Check if embeddings exist
        if not Path(embeddings_path).exists():
            print(f"❌ Error: Embeddings not found at {embeddings_path}")
            print("\nPlease create embeddings first:")
            print("  python code/ai_training/create_embeddings.py")
            sys.exit(1)

        print("Loading embeddings...")
        with open(embeddings_path, "rb") as f:
            data = pickle.load(f)
            self.embeddings = data["embeddings"]
            self.metadata = data["metadata"]
            saved_model = data.get("model_name", model_name)

        print(f"✓ Loaded {len(self.embeddings):,} verse embeddings")

        # Load model
        print(f"Loading model: {saved_model}...")
        self.model = SentenceTransformer(saved_model)
        print(f"✓ Model loaded")

        # Convert to numpy array for fast search
        self.verse_ids = list(self.embeddings.keys())
        self.embedding_matrix = np.array([
            self.embeddings[vid] for vid in self.verse_ids
        ])

        print(f"✓ Ready for semantic search!")

    def semantic_search(self,
                       query: str,
                       top_k: int = 10,
                       book_filter: Optional[List[str]] = None,
                       min_score: float = 0.0) -> List[SearchResult]:
        """
        Search for verses semantically similar to query.

        Args:
            query: Natural language question or topic
            top_k: Number of results to return
            book_filter: Optional list of books to search within
            min_score: Minimum similarity score (0-1)

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        # Encode query
        query_embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Compute cosine similarity
        similarities = np.dot(self.embedding_matrix, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get extra for filtering

        results = []
        for idx in top_indices:
            verse_id = self.verse_ids[idx]
            meta = self.metadata[str(verse_id)]
            score = float(similarities[idx])

            # Apply score filter
            if score < min_score:
                continue

            # Apply book filter if specified
            if book_filter and meta["book"] not in book_filter:
                continue

            results.append(SearchResult(
                verse_id=verse_id,
                reference=meta["reference"],
                text=meta["text"],
                score=score,
                book=meta["book"],
                chapter=meta["chapter"],
                verse=meta["verse"]
            ))

            if len(results) >= top_k:
                break

        return results

    def find_cross_references(self,
                             reference: str,
                             top_k: int = 5,
                             exclude_same_chapter: bool = True) -> List[SearchResult]:
        """
        Find verses semantically related to a given reference.

        Args:
            reference: Bible reference (e.g., "John 3:16")
            top_k: Number of cross-references to find
            exclude_same_chapter: Don't return verses from same chapter

        Returns:
            List of related verses
        """
        # Find verse by reference
        target_verse_id = None
        target_book = None
        target_chapter = None

        for vid, meta in self.metadata.items():
            if meta["reference"] == reference:
                target_verse_id = int(vid)
                target_book = meta["book"]
                target_chapter = meta["chapter"]
                break

        if not target_verse_id:
            print(f"⚠️  Reference not found: {reference}")
            return []

        # Get embedding for target verse
        target_embedding = self.embeddings[target_verse_id]

        # Find similar verses
        similarities = np.dot(self.embedding_matrix, target_embedding)
        top_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in top_indices:
            verse_id = self.verse_ids[idx]
            meta = self.metadata[str(verse_id)]

            # Skip self
            if verse_id == target_verse_id:
                continue

            # Skip same chapter if requested
            if exclude_same_chapter:
                if meta["book"] == target_book and meta["chapter"] == target_chapter:
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

    def search_by_book(self, book: str, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search within a specific book."""
        return self.semantic_search(query, top_k=top_k, book_filter=[book])

    def get_verse_context(self, reference: str, context_verses: int = 2) -> Dict:
        """
        Get a verse with surrounding context.

        Args:
            reference: Bible reference (e.g., "John 3:16")
            context_verses: Number of verses before/after to include

        Returns:
            Dictionary with verse and context
        """
        # Find target verse
        target_meta = None
        for meta in self.metadata.values():
            if meta["reference"] == reference:
                target_meta = meta
                break

        if not target_meta:
            return {"error": f"Reference not found: {reference}"}

        # Find surrounding verses
        target_book = target_meta["book"]
        target_chapter = target_meta["chapter"]
        target_verse = target_meta["verse"]

        context = {
            "reference": reference,
            "text": target_meta["text"],
            "before": [],
            "after": []
        }

        # Get context verses
        for meta in self.metadata.values():
            if meta["book"] == target_book and meta["chapter"] == target_chapter:
                verse_num = meta["verse"]

                # Before context
                if target_verse - context_verses <= verse_num < target_verse:
                    context["before"].append({
                        "reference": meta["reference"],
                        "text": meta["text"]
                    })

                # After context
                if target_verse < verse_num <= target_verse + context_verses:
                    context["after"].append({
                        "reference": meta["reference"],
                        "text": meta["text"]
                    })

        return context


def demo():
    """Demo RAG system."""
    print("=" * 70)
    print("Bible RAG System Demo")
    print("=" * 70)

    try:
        rag = BibleRAG()
    except SystemExit:
        return

    # Example 1: Semantic search
    print("\n" + "="*70)
    print("DEMO 1: Semantic Search")
    print("="*70)
    print("Query: 'salvation through faith'\n")

    results = rag.semantic_search("salvation through faith", top_k=5)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.reference} (score: {r.score:.3f})")
        print(f"   {r.text[:150]}...")
        print()

    # Example 2: Cross-references
    print("="*70)
    print("DEMO 2: Cross-References")
    print("="*70)
    print("Reference: John 3:16\n")

    xrefs = rag.find_cross_references("John 3:16", top_k=5)
    for i, r in enumerate(xrefs, 1):
        print(f"{i}. {r.reference} (similarity: {r.score:.3f})")
        print(f"   {r.text[:150]}...")
        print()

    # Example 3: Question answering
    print("="*70)
    print("DEMO 3: Question Answering")
    print("="*70)
    print("Question: What does the Bible say about love?\n")

    answer = rag.answer_question("What does the Bible say about love?", top_k=3)
    print("Relevant verses:\n")
    for i, v in enumerate(answer['verses'], 1):
        print(f"{i}. {v['reference']} (relevance: {v['relevance']:.3f})")
        print(f"   {v['text'][:150]}...")
        print()

    # Example 4: Book-specific search
    print("="*70)
    print("DEMO 4: Search Within Specific Book")
    print("="*70)
    print("Search in Psalms for: 'God's protection'\n")

    results = rag.search_by_book("Psalms", "God's protection", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.reference} (score: {r.score:.3f})")
        print(f"   {r.text[:150]}...")
        print()

    print("="*70)
    print("✅ Demo complete!")
    print("="*70)


def interactive():
    """Interactive search mode."""
    print("=" * 70)
    print("Bible RAG Interactive Search")
    print("=" * 70)
    print("\nCommands:")
    print("  /search <query>  - Semantic search")
    print("  /xref <ref>      - Find cross-references")
    print("  /book <book> <query> - Search within book")
    print("  /quit            - Exit")
    print()

    try:
        rag = BibleRAG()
    except SystemExit:
        return

    while True:
        try:
            user_input = input("\n📖 > ").strip()

            if not user_input:
                continue

            if user_input == "/quit":
                print("Goodbye!")
                break

            if user_input.startswith("/search "):
                query = user_input[8:]
                results = rag.semantic_search(query, top_k=5)
                print(f"\nTop 5 results for: '{query}'\n")
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r.reference} (score: {r.score:.3f})")
                    print(f"   {r.text}")
                    print()

            elif user_input.startswith("/xref "):
                ref = user_input[6:]
                results = rag.find_cross_references(ref, top_k=5)
                print(f"\nCross-references for: {ref}\n")
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r.reference} (similarity: {r.score:.3f})")
                    print(f"   {r.text}")
                    print()

            elif user_input.startswith("/book "):
                parts = user_input[6:].split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /book <book_name> <query>")
                    continue
                book, query = parts
                results = rag.search_by_book(book, query, top_k=5)
                print(f"\nResults in {book} for: '{query}'\n")
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r.reference} (score: {r.score:.3f})")
                    print(f"   {r.text}")
                    print()

            else:
                # Default to search
                results = rag.semantic_search(user_input, top_k=5)
                print(f"\nResults for: '{user_input}'\n")
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r.reference} (score: {r.score:.3f})")
                    print(f"   {r.text[:150]}...")
                    print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bible RAG System")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--embeddings", default="data/embeddings/embeddings.pkl",
                       help="Path to embeddings file")

    args = parser.parse_args()

    if args.demo:
        demo()
    elif args.interactive:
        interactive()
    elif args.query:
        rag = BibleRAG(embeddings_path=args.embeddings)
        results = rag.semantic_search(args.query, top_k=5)
        print(f"\nResults for: '{args.query}'\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.reference} (score: {r.score:.3f})")
            print(f"   {r.text}")
            print()
    else:
        # Default to demo
        demo()


if __name__ == "__main__":
    main()
