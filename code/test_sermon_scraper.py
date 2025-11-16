#!/usr/bin/env python3
"""
Test script for sermon_scraper.py

Quick validation before running full scrape.
Tests API connectivity, data parsing, and file creation.
"""

import sys
import json
from pathlib import Path

def test_api_connectivity():
    """Test 1: Can we reach the SermonIndex API?"""
    print("=" * 70)
    print("TEST 1: API Connectivity")
    print("=" * 70)
    
    try:
        import requests
        
        # Test speaker index
        url = "https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/_sermonindex.json"
        print(f"Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        speaker_index = response.json()
        print(f"✓ Successfully fetched speaker index")
        print(f"  Found {len(speaker_index)} speakers")
        
        # Check if Chuck Smith is in the index
        if "chuck_smith" in speaker_index:
            print(f"✓ Chuck Smith found in index")
            print(f"  Path: {speaker_index['chuck_smith']}")
        else:
            print(f"✗ Chuck Smith NOT found in index")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_sermon_list():
    """Test 2: Can we fetch Chuck Smith's sermon list?"""
    print("\n" + "=" * 70)
    print("TEST 2: Sermon List Fetch")
    print("=" * 70)
    
    try:
        import requests
        
        url = "https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/chuck_smith.json"
        print(f"Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        sermons = response.json()
        print(f"✓ Successfully fetched sermon list")
        print(f"  Total sermons: {len(sermons)}")
        
        if len(sermons) > 0:
            # Show first sermon
            first = sermons[0]
            print(f"\n  First sermon:")
            print(f"    Title: {first.get('title', 'N/A')}")
            print(f"    Scripture: {first.get('scripture', 'N/A')}")
            print(f"    Topics: {first.get('topic', 'N/A')}")
            
            # Check for transcript URL
            if first.get('displayRef'):
                print(f"    Display Ref: {first.get('displayRef')}")
            
            return True
        else:
            print(f"✗ No sermons found")
            return False
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_scraper_dry_run():
    """Test 3: Run scraper on just 3 sermons"""
    print("\n" + "=" * 70)
    print("TEST 3: Scraper Dry Run (3 sermons)")
    print("=" * 70)
    
    try:
        # Run the scraper with max-sermons=3
        import subprocess
        
        cmd = [
            sys.executable,
            "sermon_scraper.py",
            "--speaker", "chuck_smith",
            "--max-sermons", "3",
            "--log-level", "INFO",
            "--no-resume"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("-" * 70)
        
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        print("-" * 70)
        
        if result.returncode == 0:
            print("✓ Scraper completed successfully")
            
            # Check output files
            output_dir = Path("output/sermons/chuck_smith")
            metadata_dir = output_dir / "metadata"
            transcripts_dir = output_dir / "transcripts"
            
            if metadata_dir.exists():
                metadata_count = len(list(metadata_dir.glob("*.json")))
                print(f"  Metadata files: {metadata_count}")
            
            if transcripts_dir.exists():
                transcript_count = len(list(transcripts_dir.glob("*.txt")))
                print(f"  Transcript files: {transcript_count}")
            
            # Check logs
            log_file = Path("output/logs/sermon_scraper.log")
            if log_file.exists():
                print(f"  Log file: {log_file} ({log_file.stat().st_size} bytes)")
            
            return True
        else:
            print(f"✗ Scraper failed with code {result.returncode}")
            return False
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_output_structure():
    """Test 4: Validate output file structure"""
    print("\n" + "=" * 70)
    print("TEST 4: Output Structure Validation")
    print("=" * 70)
    
    try:
        output_dir = Path("output/sermons/chuck_smith")
        
        if not output_dir.exists():
            print("✗ Output directory doesn't exist")
            print("  (Run Test 3 first)")
            return False
        
        # Check metadata
        metadata_dir = output_dir / "metadata"
        if metadata_dir.exists():
            metadata_files = list(metadata_dir.glob("*.json"))
            if len(metadata_files) > 0:
                print(f"✓ Found {len(metadata_files)} metadata files")
                
                # Validate first metadata file
                with open(metadata_files[0], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                required_fields = ['sermon_id', 'title', 'speaker', 'scraped_at']
                missing = [f for f in required_fields if f not in metadata]
                
                if missing:
                    print(f"✗ Metadata missing fields: {missing}")
                    return False
                else:
                    print(f"✓ Metadata structure valid")
                    print(f"  Sample: {metadata['title']}")
            else:
                print("✗ No metadata files found")
                return False
        else:
            print("✗ Metadata directory doesn't exist")
            return False
        
        # Check transcripts
        transcripts_dir = output_dir / "transcripts"
        if transcripts_dir.exists():
            transcript_files = list(transcripts_dir.glob("*.txt"))
            if len(transcript_files) > 0:
                print(f"✓ Found {len(transcript_files)} transcript files")
                
                # Check first transcript
                with open(transcript_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) > 100:
                    print(f"✓ Transcript content valid ({len(content)} chars)")
                else:
                    print(f"⚠ Transcript seems short ({len(content)} chars)")
            else:
                print("⚠ No transcript files (may be normal if not available)")
        
        # Check logs
        log_dir = Path("output/logs")
        if log_dir.exists():
            completed_file = log_dir / "sermon_completed.json"
            if completed_file.exists():
                with open(completed_file, 'r', encoding='utf-8') as f:
                    completed = json.load(f)
                print(f"✓ Progress tracking working ({len(completed)} completed)")
            else:
                print("⚠ No progress tracking file")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SERMON SCRAPER TEST SUITE")
    print("=" * 70)
    print("\nThis will test:")
    print("1. API connectivity to SermonIndex")
    print("2. Sermon list fetching")
    print("3. Scraper functionality (3 sample sermons)")
    print("4. Output file structure validation")
    print("\n" + "=" * 70)
    
    results = []
    
    # Run tests
    results.append(("API Connectivity", test_api_connectivity()))
    results.append(("Sermon List Fetch", test_sermon_list()))
    results.append(("Scraper Dry Run", test_scraper_dry_run()))
    results.append(("Output Validation", test_output_structure()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYou can now run the full scraper:")
        print("  python sermon_scraper.py --speaker chuck_smith")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nPlease fix issues before running full scraper.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
