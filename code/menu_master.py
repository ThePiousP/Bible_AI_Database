#!/usr/bin/env python3
"""
Bible Tools Master Menu
A unified menu system for Bible scraping tools
"""

import sys
import json
import os
import subprocess
import yaml
from pathlib import Path
from datetime import datetime

# Configuration file path
CONFIG_FILE = Path(__file__).parent / "menu_master_CFG.json"

# Default configuration
DEFAULT_CONFIG = {
    "output_folder": "../output",
    "overwrite_existing": "ask",
    "database_path": "../data/GoodBook.db",
    "bible_version": "NKJV",
    "last_scraper_used": "bible",
    "step_base_url": "http://localhost:8989",
    "step_options": "NHVUG",
    "step_include_italics": True,
    "prodigy_port": "8001",
    "prodigy_dataset": "bible_v1",
    "prodigy_input_file": "../output/silver_out/train.jsonl",
    "label_rules_path": "label_rules.yml",
    "prodigy_patterns_path": "../output/prodigy_patterns.jsonl",
    "sermon_speaker": "chuck_smith",
    "sermon_output_dir": "output/sermons",
    "sermon_log_dir": "output/logs",
    "sermon_max_sermons": None,
    "sermon_resume": True
}


def load_config():
    """Load configuration from file or create with defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults in case new keys were added
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Warning: Error loading config: {e}")
            print("Using default configuration.")
            return DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, indent=2, fp=f)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def prompt(message, default=""):
    """Prompt user for input with optional default."""
    if default:
        response = input(f"{message} [{default}]: ").strip()
        return response if response else default
    else:
        return input(f"{message}: ").strip()


def yn(question, default="y"):
    """Ask yes/no question."""
    valid = {"yes": True, "y": True, "no": False, "n": False}
    default_prompt = "[Y/n]" if default.lower() == "y" else "[y/N]"

    while True:
        response = input(f"{question} {default_prompt}: ").strip().lower()
        if not response:
            return valid.get(default.lower(), True)
        if response in valid:
            return valid[response]
        print("Please respond with 'y' or 'n'")


def show_banner():
    """Display the menu banner."""
    print("\n" + "=" * 60)
    print("          BIBLE TOOLS MASTER MENU")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def convert_gazetteers_to_patterns(label_rules_path, output_path, filter_labels=None):
    """
    Read label_rules.yml and convert gazetteer files to Prodigy pattern format.

    Args:
        label_rules_path: Path to label_rules.yml
        output_path: Path for output JSONL file
        filter_labels: Optional list of labels to include (None = include all)

    Returns:
        Number of patterns generated
    """
    # Load label rules
    label_rules_path = Path(label_rules_path).resolve()
    with open(label_rules_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    patterns = []

    # Get the directory containing label_rules.yml (project root)
    label_rules_dir = label_rules_path.parent

    # Process each label's gazetteers
    for label, rules in config.get('rules', {}).items():
        # Skip if filtering and label not in filter list
        if filter_labels and label not in filter_labels:
            continue

        gazetteer_files = rules.get('gazetteer_files', [])

        for gaz_file in gazetteer_files:
            # Resolve gazetteer path relative to label_rules.yml location
            gaz_path = (label_rules_dir / gaz_file).resolve()

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
                            if len(tokens) == 1:
                                # Single-token case-sensitive
                                pattern_obj = {
                                    "label": label,
                                    "pattern": [{"TEXT": term}]
                                }
                            else:
                                # Multi-token: match exact text for all tokens
                                pattern_obj = {
                                    "label": label,
                                    "pattern": [{"TEXT": token} for token in tokens]
                                }
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

    return len(patterns)


def run_bible_scraper(config):
    """Launch the Bible (BibleGateway) scraper."""
    print("\n" + "-" * 60)
    print("BIBLE SCRAPER (BibleGateway)")
    print("-" * 60)

    try:
        # Set up the legacy path
        legacy_path = Path(__file__).parent / "legacy"
        bible_scraper_path = legacy_path / "bible_scraper.py"
        
        # Validate paths exist
        if not legacy_path.exists():
            print(f"\nError: Legacy folder not found at: {legacy_path}")
            print("Please create the 'legacy' folder in the code directory.")
            input("\nPress Enter to continue...")
            return
            
        if not bible_scraper_path.exists():
            print(f"\nError: Bible scraper not found at: {bible_scraper_path}")
            print("Please ensure bible_scraper.py exists in the legacy folder.")
            input("\nPress Enter to continue...")
            return
        
        # Add to Python path
        legacy_path_str = str(legacy_path.resolve())
        if legacy_path_str not in sys.path:
            sys.path.insert(0, legacy_path_str)
        
        # Try to import the BibleScraper class with better error handling
        try:
            # First, try to import the module
            import bible_scraper  # type: ignore

            # Check if BibleScraper class exists in the module
            if not hasattr(bible_scraper, 'BibleScraper'):
                print(f"\nError: BibleScraper class not found in bible_scraper.py")
                print("The bible_scraper.py file exists but doesn't contain a BibleScraper class.")
                print("\nPlease ensure bible_scraper.py contains:")
                print("  class BibleScraper:")
                print("      # ... class implementation ...")
                input("\nPress Enter to continue...")
                return

            # Import the class
            BibleScraper = bible_scraper.BibleScraper  # type: ignore
            
        except ImportError as import_err:
            print(f"\nError: Could not import bible_scraper module")
            print(f"Import error: {import_err}")
            print("\nPossible causes:")
            print("1. Syntax errors in bible_scraper.py")
            print("2. Missing dependencies required by bible_scraper.py")
            print("3. The file bible_scraper.py is corrupted or empty")
            print(f"4. Python path issue with: {legacy_path}")
            print("\nTo diagnose:")
            print(f"1. Try running: python {bible_scraper_path}")
            print("2. Check for syntax errors in the file")
            print("3. Ensure all required imports are available")
            input("\nPress Enter to continue...")
            return
            
        except Exception as other_err:
            print(f"\nError: Unexpected error importing bible_scraper")
            print(f"Error: {other_err}")
            print(f"Error type: {type(other_err).__name__}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")
            return

        print(f"Bible Version: {config['bible_version']}")
        print(f"Output Folder: {config['output_folder']}")
        print(f"Database: {config['database_path']}")

        # Update the legacy config.json with current settings
        legacy_config_path = legacy_path / "config.json"
        if legacy_config_path.exists():
            with open(legacy_config_path, 'r') as f:
                legacy_config = json.load(f)
            # Update bible version from menu config
            legacy_config['bible_version'] = config['bible_version']
            with open(legacy_config_path, 'w') as f:
                json.dump(legacy_config, f, indent=2)

        # Create scraper instance with config path
        try:
            scraper = BibleScraper(config_path=str(legacy_config_path))
            print("\nBible Scraper initialized successfully!")
        except Exception as init_err:
            print(f"\nError initializing BibleScraper: {init_err}")
            print("The BibleScraper class was found but failed to initialize.")
            print("Check the constructor parameters and dependencies.")
            input("\nPress Enter to continue...")
            return

        print("Note: Full scraping menu from 66MASTER_v.983.py will be integrated later.")
        print("For now, you can use the scraper instance directly in code.")

        # TODO: Integrate the scraping menu from 66MASTER_v.983.py
        input("\nPress Enter to return to main menu...")

        # Update last used
        config['last_scraper_used'] = 'bible'
        save_config(config)

    except Exception as e:
        print(f"\nUnexpected error running Bible scraper: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")


def run_step_scraper(config):
    """Launch the STEP scraper menu."""
    print("\n" + "-" * 60)
    print("STEP SCRAPER")
    print("-" * 60)

    try:
        # Set up the STEP path
        step_path = Path(__file__).parent / "STEP"
        step_cli_path = step_path / "step_cli.py"
        
        # Validate paths exist
        if not step_path.exists():
            print(f"\nError: STEP folder not found at: {step_path}")
            print("Please create the 'STEP' folder in the code directory.")
            input("\nPress Enter to continue...")
            return
            
        if not step_cli_path.exists():
            print(f"\nError: step_cli.py not found at: {step_cli_path}")
            print("Please ensure step_cli.py exists in the STEP folder.")
            input("\nPress Enter to continue...")
            return

        # Add to Python path
        step_path_str = str(step_path.resolve())
        if step_path_str not in sys.path:
            sys.path.insert(0, step_path_str)
        
        # Try to import step_cli with better error handling
        try:
            import step_cli  # type: ignore

            # Check if run_menu function exists
            if not hasattr(step_cli, 'run_menu'):
                print(f"\nError: run_menu function not found in step_cli.py")
                print("The step_cli.py file exists but doesn't contain a run_menu function.")
                input("\nPress Enter to continue...")
                return
                
        except ImportError as import_err:
            print(f"\nError: Could not import step_cli module")
            print(f"Import error: {import_err}")
            print("\nPossible causes:")
            print("1. Syntax errors in step_cli.py")
            print("2. Missing dependencies required by step_cli.py")
            print("3. The file step_cli.py is corrupted or empty")
            print(f"4. Python path issue with: {step_path}")
            print("\nTo diagnose:")
            print(f"1. Try running: python {step_cli_path}")
            print("2. Check for syntax errors in the file")
            print("3. Ensure all required imports are available")
            input("\nPress Enter to continue...")
            return
            
        except Exception as other_err:
            print(f"\nError: Unexpected error importing step_cli")
            print(f"Error: {other_err}")
            print(f"Error type: {type(other_err).__name__}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")
            return

        print("Launching STEP scraper menu...")
        print("-" * 60)

        # Run the STEP menu
        try:
            step_cli.run_menu()
        except Exception as run_err:
            print(f"\nError running STEP menu: {run_err}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")
            return

        # Update last used
        config['last_scraper_used'] = 'step'
        save_config(config)

    except Exception as e:
        print(f"\nUnexpected error running STEP scraper: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")


def run_sermon_scraper(config):
    """Launch the Enhanced Sermon scraper with validation and punctuation restoration."""
    print("\n" + "-" * 60)
    print("ENHANCED SERMON SCRAPER (SermonIndex.net)")
    print("-" * 60)

    try:
        sermon_scraper_path = Path(__file__).parent / "sermon_scraper_enhanced.py"

        # Validate path exists
        if not sermon_scraper_path.exists():
            print(f"\nError: Enhanced sermon scraper not found at: {sermon_scraper_path}")
            print("Please ensure sermon_scraper_enhanced.py exists in the code directory.")
            input("\nPress Enter to continue...")
            return

        # Get current settings
        print(f"\nCurrent Sermon Scraper Settings:")
        print(f"  Speaker: {config['sermon_speaker']}")
        print(f"  Output Directory: {config['sermon_output_dir']}")
        print(f"  Log Directory: {config['sermon_log_dir']}")
        print(f"  Max Sermons: {config['sermon_max_sermons'] or 'All'}")
        print(f"  Resume Mode: {config['sermon_resume']}")

        # Ask if user wants to change settings
        print("\n" + "-" * 60)
        if yn("Use current settings?", "y"):
            speaker = config['sermon_speaker']
            max_sermons = config['sermon_max_sermons']
            resume = config['sermon_resume']
        else:
            # Customize settings
            speaker = prompt("Enter speaker code", config['sermon_speaker'])
            max_input = prompt("Max sermons (press Enter for all)",
                             str(config['sermon_max_sermons']) if config['sermon_max_sermons'] else "")
            max_sermons = int(max_input) if max_input.strip() else None
            resume = yn("Resume from previous run?", "y" if config['sermon_resume'] else "n")

            # Update config
            config['sermon_speaker'] = speaker
            config['sermon_max_sermons'] = max_sermons
            config['sermon_resume'] = resume
            save_config(config)

        # Build command
        cmd_parts = [
            sys.executable,
            str(sermon_scraper_path),
            "--speaker", speaker,
            "--output-dir", config['sermon_output_dir'],
            "--log-dir", config['sermon_log_dir'],
        ]

        if max_sermons:
            cmd_parts.extend(["--max-sermons", str(max_sermons)])

        if not resume:
            cmd_parts.append("--no-resume")

        # Show command
        print("\n" + "-" * 60)
        print("Sermon Scraper Command:")
        print("-" * 60)
        print(" ".join(cmd_parts))
        print("-" * 60)

        # Confirm before launching
        if yn("\nLaunch sermon scraper?", "y"):
            print(f"\nLaunching sermon scraper for {speaker}...")
            print("Press Ctrl+C to stop scraper and return to menu.\n")

            try:
                # Run from project root (parent of code directory)
                project_root = Path(__file__).parent.parent
                subprocess.run(cmd_parts, cwd=str(project_root))
            except KeyboardInterrupt:
                print("\n\nScraper stopped by user.")

        # Update last used
        config['last_scraper_used'] = 'sermon'
        save_config(config)

        input("\nPress Enter to return to main menu...")

    except Exception as e:
        print(f"\nError running sermon scraper: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")


def run_prodigy_ner(config):
    """Launch Prodigy NER annotation with custom labels."""
    print("\n" + "-" * 60)
    print("PRODIGY NER ANNOTATION")
    print("-" * 60)

    try:
        # Get current settings
        print(f"\nCurrent Prodigy Settings:")
        print(f"  Port: {config['prodigy_port']}")
        print(f"  Dataset: {config['prodigy_dataset']}")
        print(f"  Input File: {config['prodigy_input_file']}")
        print(f"  Pattern File: {config['prodigy_patterns_path']}")
        print(f"  Label Rules: {config['label_rules_path']}")

        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent
        label_rules_path = (project_root / config['label_rules_path']).resolve()
        patterns_path = (project_root / config['prodigy_patterns_path']).resolve()
        input_file = (project_root / config['prodigy_input_file']).resolve()

        # Get labels from user
        print("\n" + "-" * 60)
        print("Enter labels as comma-separated list (e.g., DEITY,PERSON,LOCATION)")
        print("Or press Enter to use all labels from label_rules.yml")
        print("-" * 60)

        labels_input = input("Labels: ").strip()

        # Parse labels
        if labels_input:
            labels_list = [label.strip() for label in labels_input.split(',') if label.strip()]
            print(f"\nUsing labels: {', '.join(labels_list)}")
        else:
            labels_list = None
            print("\nUsing all labels from pattern file")

        # Generate patterns
        print(f"\nGenerating patterns from gazetteers...")
        print(f"  Label rules: {label_rules_path}")
        print(f"  Output: {patterns_path}")

        pattern_count = convert_gazetteers_to_patterns(
            label_rules_path=label_rules_path,
            output_path=patterns_path,
            filter_labels=labels_list
        )

        print(f"✓ Generated {pattern_count} patterns")

        # Show pattern summary
        if pattern_count > 0:
            label_counts = {}
            with open(patterns_path, 'r', encoding='utf-8') as f:
                for line in f:
                    pattern = json.loads(line)
                    label = pattern['label']
                    label_counts[label] = label_counts.get(label, 0) + 1

            print(f"\nPattern counts by label:")
            for label in sorted(label_counts.keys()):
                print(f"  {label}: {label_counts[label]}")

        # Construct Prodigy command
        port = config['prodigy_port']
        dataset = config['prodigy_dataset']

        cmd_parts = [
            f"SET PRODIGY_PORT={port}",
            "&&",
            "python", "-m", "prodigy",
            "ner.manual",
            dataset,
            "blank:en",
            str(input_file),
        ]

        # Add labels if specified
        if labels_list:
            cmd_parts.extend(["--label", ",".join(labels_list)])

        # Add patterns file
        cmd_parts.extend(["--patterns", str(patterns_path)])

        # Show command
        print("\n" + "-" * 60)
        print("Prodigy Command:")
        print("-" * 60)
        print(" ".join(cmd_parts))
        print("-" * 60)

        # Confirm before launching
        if yn("\nLaunch Prodigy?", "y"):
            # Execute command
            cmd_string = " ".join(cmd_parts)
            print(f"\nLaunching Prodigy on port {port}...")
            print("Press Ctrl+C to stop Prodigy and return to menu.\n")

            try:
                subprocess.run(cmd_string, shell=True, cwd=project_root)
            except KeyboardInterrupt:
                print("\n\nProdigy stopped by user.")

        input("\nPress Enter to return to main menu...")

    except FileNotFoundError as e:
        print(f"\nError: File not found: {e}")
        print("Please check your configuration paths.")
        input("\nPress Enter to continue...")
    except Exception as e:
        print(f"\nError running Prodigy: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")


def settings_menu(config):
    """Display and manage settings."""
    while True:
        print("\n" + "=" * 60)
        print("SETTINGS")
        print("=" * 60)
        print("\n1. Change output folder")
        print("2. Change overwrite mode (ask/yes/no)")
        print("3. Change Bible version")
        print("4. Change database path")
        print("5. Change STEP base URL")
        print("6. Change Prodigy port")
        print("7. Change Prodigy dataset name")
        print("8. Change Prodigy input file")
        print("9. Change sermon speaker (default)")
        print("10. Change sermon output directory")
        print("11. Show all settings")
        print("12. Reset to defaults")
        print("0. Back to main menu")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            new_folder = prompt("Enter output folder", config['output_folder'])
            config['output_folder'] = new_folder
            print(f"Output folder set to: {new_folder}")
            save_config(config)

        elif choice == "2":
            print("\nOverwrite mode options:")
            print("  ask - Prompt each time")
            print("  yes - Always overwrite")
            print("  no  - Never overwrite")
            mode = prompt("Enter mode (ask/yes/no)", config['overwrite_existing'])
            if mode.lower() in ['ask', 'yes', 'no']:
                config['overwrite_existing'] = mode.lower()
                print(f"Overwrite mode set to: {mode}")
                save_config(config)
            else:
                print("Invalid mode. Use 'ask', 'yes', or 'no'.")

        elif choice == "3":
            new_version = prompt("Enter Bible version (e.g., NKJV, KJV, ESV)",
                                config['bible_version'])
            config['bible_version'] = new_version
            print(f"Bible version set to: {new_version}")
            save_config(config)

        elif choice == "4":
            new_db = prompt("Enter database path", config['database_path'])
            config['database_path'] = new_db
            print(f"Database path set to: {new_db}")
            save_config(config)

        elif choice == "5":
            new_url = prompt("Enter STEP base URL", config['step_base_url'])
            config['step_base_url'] = new_url.rstrip("/")
            print(f"STEP base URL set to: {new_url}")
            save_config(config)

        elif choice == "6":
            new_port = prompt("Enter Prodigy port", config['prodigy_port'])
            config['prodigy_port'] = new_port
            print(f"Prodigy port set to: {new_port}")
            save_config(config)

        elif choice == "7":
            new_dataset = prompt("Enter Prodigy dataset name", config['prodigy_dataset'])
            config['prodigy_dataset'] = new_dataset
            print(f"Prodigy dataset set to: {new_dataset}")
            save_config(config)

        elif choice == "8":
            new_input = prompt("Enter Prodigy input file path", config['prodigy_input_file'])
            config['prodigy_input_file'] = new_input
            print(f"Prodigy input file set to: {new_input}")
            save_config(config)

        elif choice == "9":
            new_speaker = prompt("Enter default sermon speaker code", config['sermon_speaker'])
            config['sermon_speaker'] = new_speaker
            print(f"Sermon speaker set to: {new_speaker}")
            save_config(config)

        elif choice == "10":
            new_sermon_dir = prompt("Enter sermon output directory", config['sermon_output_dir'])
            config['sermon_output_dir'] = new_sermon_dir
            print(f"Sermon output directory set to: {new_sermon_dir}")
            save_config(config)

        elif choice == "11":
            print("\n" + "-" * 60)
            print("CURRENT SETTINGS:")
            print("-" * 60)
            for key, value in config.items():
                print(f"  {key:25s} = {value}")
            print("-" * 60)
            input("\nPress Enter to continue...")

        elif choice == "12":
            if yn("Reset all settings to defaults?", "n"):
                config.clear()
                config.update(DEFAULT_CONFIG.copy())
                save_config(config)
                print("Settings reset to defaults.")

        elif choice == "0":
            break

        else:
            print("Invalid choice. Please try again.")


def main_menu():
    """Main menu loop."""
    config = load_config()

    while True:
        show_banner()
        print("\nMAIN MENU:")
        print("-" * 60)
        print("  1. Run Bible Scraper (BibleGateway)")
        print("  2. Run STEP Scraper")
        print("  3. Run Prodigy NER Annotation")
        print("  4. Run Sermon Scraper (SermonIndex)")
        print("  5. [Placeholder - Future Tool]")
        print("  6. [Placeholder - Future Tool]")
        print("  7. [Placeholder - Future Tool]")
        print("  8. [Placeholder - Future Tool]")
        print("  9. Settings")
        print(" 10. Exit")
        print("-" * 60)

        choice = input("\nSelect option (1-10): ").strip()

        if choice == "1":
            run_bible_scraper(config)

        elif choice == "2":
            run_step_scraper(config)

        elif choice == "3":
            run_prodigy_ner(config)

        elif choice == "4":
            run_sermon_scraper(config)

        elif choice in ["5", "6", "7", "8"]:
            print(f"\nOption {choice} is a placeholder for future functionality.")
            input("Press Enter to continue...")

        elif choice == "9":
            settings_menu(config)

        elif choice == "10" or choice == "0":
            if yn("Exit Bible Tools Menu?", "y"):
                print("\nGoodbye!")
                sys.exit(0)

        else:
            print("\nInvalid choice. Please enter a number from 1 to 10.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
