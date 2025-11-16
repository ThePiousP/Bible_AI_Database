#!/usr/bin/env python3
"""Check OSIS codes for potentially problematic books"""
import sys
sys.path.insert(0, r"D:\Project_PP\projects\bible\code\STEP")

from step_constants import BOOK_OSIS, resolve_book_code

problem_books = ['Philemon', '2 John', '3 John', 'Jude', 'Obadiah']

print("Problem Books - OSIS Codes:")
print("=" * 60)
for book in problem_books:
    osis = BOOK_OSIS[book]
    print(f"{book:15} -> {osis:10}")

print("\n" + "=" * 60)
print("Testing Ambiguous Inputs:")
print("=" * 60)

# Test various inputs that could be ambiguous
test_inputs = [
    "Phil",     # Could be Philippians or Philemon?
    "Phlm",     # Philemon
    "Philemon",
    "2John",
    "2 John",
    "3John",
    "3 John",
    "Jud",      # We fixed this one
    "Jude",
    "Obad",
    "Obadiah"
]

for inp in test_inputs:
    resolved = resolve_book_code(inp)
    print(f"{inp:15} -> {resolved}")
