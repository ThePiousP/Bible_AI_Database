#!/usr/bin/env python3
"""
Clean up sermon transcript filenames by removing embedded Bible verse references
and other metadata patterns
"""

import re
from pathlib import Path

def clean_filename(filename):
    """
    Clean a filename by removing:
    - Bible verse references (e.g., DEU_7_1, MAT_6_33, 1PE_2_9)
    - Long descriptive metadata
    - Multiple underscores

    Keep:
    - Main sermon title
    - Part numbers
    - Display reference (the code at the end like _VZUQIs2E)
    """

    # Remove .txt extension temporarily
    name = filename.replace('.txt', '')

    # Pattern 1: Remove Bible verse references (like DEU_7_1MAT_6_33JHN_3_16)
    # These are 3-4 letter book codes followed by numbers and underscores
    # Common pattern: BOOK_CHAPTER_VERSE or DIGIT+BOOK_CHAPTER_VERSE
    verse_pattern = r'(?:[A-Z]{3,4}_\d+_\d+|[0-9][A-Z]{2,3}_\d+_\d+)+'
    name = re.sub(verse_pattern, '', name)

    # Pattern 2: Remove descriptive metadata that comes before "In_this_sermon" or "Chuck_Smith"
    # Example: "Obedience_to_GodGod's_SovereigntyDEU_1_6DEU_30_9Chuck_Smith_emphasizes..."
    # We want to keep the part before the metadata

    # Find patterns like "2Model_for_the_Church" or "0Compassion_in_Ministry" and remove the digit prefix
    name = re.sub(r'(\d+)([A-Z][a-z_]+)', r'\1_\2', name)

    # Remove long descriptive sections (topics/themes) - these are CamelCase words joined together
    # Pattern: Multiple capitalized words stuck together before scripture refs or "In_this" or "Chuck_Smith"
    # Example: "Spirit-led_MinistryChuck_Smith" -> keep title before, remove after

    # If there's "Chuck_Smith_emphasizes" or "In_this_sermon", remove everything from that point
    name = re.sub(r'Chuck_Smith_(?:emphasizes|discusses|explores|reflects|addresses|teaches|focuses).*$', '', name)
    name = re.sub(r'In_this_(?:sermon|video|lesson|message).*$', '', name)

    # Remove common descriptive topic patterns (CamelCase words before references)
    # These usually appear as TopicNameAnotherTopicThirdTopicScriptureRef
    # Look for pattern: word_word then CapitalWordCapitalWord (no underscores)
    name = re.sub(r'(?<=[a-z_])([A-Z][a-z]+){2,}(?=[A-Z0-9_]|$)', '', name)

    # Clean up multiple consecutive underscores
    name = re.sub(r'_{2,}', '_', name)

    # Remove trailing underscores before the display ref
    name = re.sub(r'_+(?=_[A-Za-z0-9_-]{6,10}$)', '', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Add .txt back
    return name + '.txt'

def preview_renames(directory, limit=20):
    """Preview what the renames would look like"""

    files = list(directory.glob('*.txt'))

    print(f"Found {len(files)} files\n")
    print("PREVIEW OF RENAMES (showing first {})".format(limit))
    print("=" * 100)

    changes = []
    for file_path in files:
        old_name = file_path.name
        new_name = clean_filename(old_name)

        if old_name != new_name:
            changes.append({
                'old': old_name,
                'new': new_name,
                'old_len': len(old_name),
                'new_len': len(new_name),
                'saved': len(old_name) - len(new_name)
            })

    # Sort by most characters saved
    changes.sort(key=lambda x: x['saved'], reverse=True)

    print(f"\nTotal files that will be renamed: {len(changes)}")
    print(f"Files unchanged: {len(files) - len(changes)}\n")

    for i, change in enumerate(changes[:limit], 1):
        print(f"\n{i}. OLD ({change['old_len']} chars): {change['old'][:80]}...")
        print(f"   NEW ({change['new_len']} chars): {change['new'][:80]}...")
        print(f"   SAVED: {change['saved']} characters")

    if len(changes) > limit:
        print(f"\n... and {len(changes) - limit} more files to rename")

    return changes

def apply_renames(directory, changes, dry_run=True):
    """Apply the renames"""

    if dry_run:
        print("\n" + "=" * 100)
        print("DRY RUN - No files will be renamed")
        print("=" * 100)
        return

    print("\n" + "=" * 100)
    print("APPLYING RENAMES...")
    print("=" * 100)

    success_count = 0
    error_count = 0

    for change in changes:
        old_path = directory / change['old']
        new_path = directory / change['new']

        try:
            if new_path.exists():
                print(f"ERROR: Target already exists: {change['new']}")
                error_count += 1
            else:
                old_path.rename(new_path)
                success_count += 1
                if success_count % 100 == 0:
                    print(f"  Renamed {success_count} files...")
        except Exception as e:
            print(f"ERROR renaming {change['old']}: {e}")
            error_count += 1

    print(f"\nCompleted!")
    print(f"  Successfully renamed: {success_count}")
    print(f"  Errors: {error_count}")

def main():
    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    print("FILENAME CLEANUP UTILITY")
    print("=" * 100)
    print(f"Directory: {cleaned_dir}\n")

    # Preview the changes
    changes = preview_renames(cleaned_dir, limit=30)

    if not changes:
        print("\nNo files need renaming!")
        return

    # Ask user if they want to proceed
    print("\n" + "=" * 100)
    print("Applying renames...")
    print("=" * 100)

    # Actually rename the files
    apply_renames(cleaned_dir, changes, dry_run=False)

if __name__ == '__main__':
    main()
