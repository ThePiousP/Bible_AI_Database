#!/usr/bin/env python3
"""
Bible AI Chat Interface
Interactive conversational system for Bible Q&A and discussion.

This integrates:
- NER for entity recognition
- Semantic search for verse retrieval
- RAG for context-aware answers
- (Optional) Fine-tuned LLM for natural responses
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Note: OpenAI not installed. Using basic RAG mode only.")

class BibleChatbot:
    """Interactive Bible AI chatbot."""

    def __init__(self,
                 use_llm: bool = True,
                 llm_provider: str = "openai",
                 api_key: Optional[str] = None):
        """
        Initialize chatbot.

        Args:
            use_llm: Use LLM for responses (requires API key or local model)
            llm_provider: "openai", "anthropic", or "local"
            api_key: API key for cloud LLM (or None for local)
        """
        self.use_llm = use_llm
        self.llm_provider = llm_provider

        # Try to load RAG system
        try:
            from rag_system import BibleRAG
            self.rag = BibleRAG()
            self.has_rag = True
            print("✅ RAG system loaded")
        except Exception as e:
            print(f"⚠️  RAG system not available: {e}")
            print("    Run: python code/ai_training/create_embeddings.py first")
            self.has_rag = False
            self.rag = None

        # Set up LLM if requested
        if use_llm:
            if llm_provider == "openai" and HAS_OPENAI:
                openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
                self.llm_model = "gpt-4"
            else:
                print("⚠️  LLM not configured, using RAG-only mode")
                self.use_llm = False

        # Conversation history
        self.history: List[Dict[str, str]] = []

        # System prompt for biblical understanding
        self.system_prompt = """You are a knowledgeable Bible scholar and theologian.
You provide accurate, insightful answers about the Bible based on the verses provided.

Guidelines:
- Base answers on the retrieved Bible verses
- Cite specific verse references
- Explain historical and theological context
- Be respectful of different interpretations
- Admit uncertainty when appropriate
- Use clear, accessible language
"""

    def search_verses(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant verses."""
        if not self.has_rag:
            return []

        results = self.rag.semantic_search(query, top_k=top_k)
        return [
            {
                "reference": r.reference,
                "text": r.text,
                "score": r.score
            }
            for r in results
        ]

    def format_context(self, verses: List[Dict]) -> str:
        """Format verses as context for LLM."""
        if not verses:
            return "No relevant verses found."

        context = "Relevant Bible verses:\n\n"
        for v in verses:
            context += f"{v['reference']}: {v['text']}\n\n"
        return context

    def generate_response(self,
                         question: str,
                         context: str) -> str:
        """Generate response using LLM or simple formatting."""

        if self.use_llm and self.llm_provider == "openai":
            # Use OpenAI GPT
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]

            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        else:
            # Simple RAG-only response
            return f"{context}\n\nBased on these verses, {question.lower()}"

    def chat(self, user_input: str) -> str:
        """
        Process user input and generate response.

        Args:
            user_input: User's question or message

        Returns:
            Chatbot response
        """
        # Handle special commands
        if user_input.lower() in ["/quit", "/exit", "/bye"]:
            return "Goodbye! May God bless you."

        if user_input.lower() == "/help":
            return self._help_message()

        if user_input.lower() == "/history":
            return self._format_history()

        # Search for relevant verses
        verses = self.search_verses(user_input, top_k=5)

        if not verses:
            return "I couldn't find relevant verses. Try rephrasing your question."

        # Format context
        context = self.format_context(verses)

        # Generate response
        response = self.generate_response(user_input, context)

        # Save to history
        self.history.append({
            "user": user_input,
            "assistant": response,
            "verses": verses
        })

        return response

    def _help_message(self) -> str:
        """Display help message."""
        return """
╔════════════════════════════════════════════════════════╗
║              BIBLE AI CHATBOT - HELP                  ║
╚════════════════════════════════════════════════════════╝

ASK QUESTIONS:
  - "What does the Bible say about love?"
  - "Tell me about David and Goliath"
  - "What is the Gospel?"
  - "Explain John 3:16"

COMMANDS:
  /help     - Show this help message
  /history  - View conversation history
  /quit     - Exit the chat

FEATURES:
  ✓ Semantic search across all Bible verses
  ✓ Context-aware answers
  ✓ Cross-reference suggestions
  ✓ Theological insights

TIPS:
  - Be specific in your questions
  - Ask about themes, people, or events
  - Request verse explanations
  - Explore theological concepts
"""

    def _format_history(self) -> str:
        """Format conversation history."""
        if not self.history:
            return "No conversation history yet."

        output = "Conversation History:\n" + "="*50 + "\n\n"
        for i, turn in enumerate(self.history, 1):
            output += f"[{i}] You: {turn['user']}\n"
            output += f"    Bot: {turn['assistant'][:100]}...\n\n"
        return output


def interactive_mode():
    """Run chatbot in interactive mode."""
    print("""
╔════════════════════════════════════════════════════════╗
║         WELCOME TO BIBLE AI CHATBOT                   ║
║         Deep Biblical Understanding & Discussion       ║
╚════════════════════════════════════════════════════════╝

Type /help for commands, /quit to exit
    """)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    use_llm = bool(api_key)

    if not use_llm:
        print("⚠️  No OpenAI API key found. Using basic RAG mode.")
        print("    Set OPENAI_API_KEY environment variable for AI responses.\n")

    # Initialize chatbot
    try:
        bot = BibleChatbot(use_llm=use_llm)
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return

    # Main loop
    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            response = bot.chat(user_input)
            print(f"\n🤖 Bible AI: {response}")

            if user_input.lower() in ["/quit", "/exit", "/bye"]:
                break

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_mode():
    """Run demo with pre-set questions."""
    print("""
╔════════════════════════════════════════════════════════╗
║              BIBLE AI CHATBOT - DEMO                  ║
╚════════════════════════════════════════════════════════╝
    """)

    bot = BibleChatbot(use_llm=False)  # RAG-only for demo

    demo_questions = [
        "What does the Bible say about love?",
        "Tell me about the creation story",
        "What is the Gospel message?",
        "Who was David?",
        "What are the Ten Commandments?",
    ]

    for i, question in enumerate(demo_questions, 1):
        print(f"\n{'='*60}")
        print(f"Demo Question {i}: {question}")
        print('='*60)

        response = bot.chat(question)
        print(f"\n{response}\n")

        input("Press Enter for next question...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bible AI Chatbot")
    parser.add_argument("--demo", action="store_true",
                       help="Run demo mode with sample questions")
    parser.add_argument("--api-key", help="OpenAI API key")

    args = parser.parse_args()

    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    if args.demo:
        demo_mode()
    else:
        interactive_mode()
