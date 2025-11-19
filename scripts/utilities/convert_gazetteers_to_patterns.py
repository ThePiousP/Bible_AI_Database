"""
Convert gazetteer text files to Prodigy JSONL pattern format.
"""
import json
from pathlib import Path
import yaml

def convert_gazetteers_to_patterns(label_rules_path, output_path):
    """
    Read label_rules.yml and convert all gazetteer files to Prodigy pattern format.

    Args:
        label_rules_path: Path to label_rules.yml
        output_path: Path for output JSONL file
    """
    # Load label rules
    with open(label_rules_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    patterns = []

    # Process each label's gazetteers
    for label, rules in config.get('rules', {}).items():
        gazetteer_files = rules.get('gazetteer_files', [])

        for gaz_file in gazetteer_files:
            gaz_path = Path(gaz_file)

            # Skip if file doesn't exist
            if not gaz_path.exists():
                print(f"Warning: Gazetteer file not found: {gaz_file}")
                continue

            # Get case sensitivity setting for this label
            case_sensitive = rules.get('case_sensitive', False)

            # Read gazetteer entries
            with open(gaz_path, 'r', encoding='utf-8') as f:
                for line in f:
                    term = line.strip()
                    if term:  # Skip empty lines
                        if case_sensitive:
                            # Use token pattern for case-sensitive matching
                            tokens = term.split()
                            pattern_obj = {
                                "label": label,
                                "pattern": [{"LOWER": token.lower()} if i > 0 else {"TEXT": token}
                                           for i, token in enumerate(tokens)]
                            }
                            # For single-token case-sensitive, use simpler format
                            if len(tokens) == 1:
                                pattern_obj["pattern"] = [{"TEXT": term}]
                            else:
                                # Multi-token: match exact text for all tokens
                                pattern_obj["pattern"] = [{"TEXT": token} for token in tokens]
                            patterns.append(pattern_obj)
                        else:
                            # Simple string pattern for case-insensitive
                            patterns.append({
                                "label": label,
                                "pattern": term
                            })

    # Write patterns to JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for pattern in patterns:
            f.write(json.dumps(pattern) + '\n')

    print(f"Converted {len(patterns)} patterns to {output_path}")

    # Print summary by label
    label_counts = {}
    for p in patterns:
        label_counts[p['label']] = label_counts.get(p['label'], 0) + 1

    print("\nPattern counts by label:")
    for label in sorted(label_counts.keys()):
        print(f"  {label}: {label_counts[label]}")

if __name__ == "__main__":
    convert_gazetteers_to_patterns(
        label_rules_path="label_rules.yml",
        output_path="prodigy_patterns.jsonl"
    )
