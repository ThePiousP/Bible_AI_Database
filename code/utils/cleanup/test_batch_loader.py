#!/usr/bin/env python3
import os
import glob

BATCH_DIR = r"D:\Project_PP\Projects\Bible\Data"

print(f"Looking in: {BATCH_DIR}")
print(f"Directory exists? {os.path.exists(BATCH_DIR)}")
print(f"Is directory? {os.path.isdir(BATCH_DIR)}")

print("\nAll files in directory:")
all_files = os.listdir(BATCH_DIR)
for f in all_files[:20]:  # First 20
    print(f"  {f}")

print(f"\nTotal files: {len(all_files)}")

print("\nSearching for batch_*_clues.txt:")
batch_files = glob.glob(os.path.join(BATCH_DIR, "batch_*_clues.txt"))
print(f"Found {len(batch_files)} batch files:")
for f in batch_files[:10]:
    print(f"  {os.path.basename(f)}")
