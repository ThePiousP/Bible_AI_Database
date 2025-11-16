#!/usr/bin/env python3
"""Rename files in cache/Jude to STEP_Jude.#.json format"""
import os
from pathlib import Path

cache_dir = Path(r"D:\Project_PP\projects\bible\cache\Jude")

print(f"Renaming files in: {cache_dir}")
print("=" * 60)

# Get all .json files
files = sorted(cache_dir.glob("Jud.*.json"))

count = 0
for file in files:
    # Change Jud. to STEP_Jude.
    new_name = file.name.replace("Jud.", "STEP_Jude.")
    new_path = file.parent / new_name

    print(f"{file.name} -> {new_name}")
    file.rename(new_path)
    count += 1

print("=" * 60)
print(f"Renamed {count} files")
