#!/usr/bin/env python3
"""Quick diagnostic to check SermonIndex API response format"""

import json
import requests

url = "https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/chuck_smith.json"

print("Fetching:", url)
response = requests.get(url, timeout=30)
response.raise_for_status()

data = response.json()

print("\n=== API Response Analysis ===")
print(f"Response type: {type(data)}")
print(f"Length: {len(data)}")

if data:
    print(f"\nFirst item type: {type(data[0])}")
    print(f"\nFirst item:")
    print(json.dumps(data[0], indent=2) if isinstance(data[0], dict) else data[0])

    print(f"\nAll items (first 5):")
    for i, item in enumerate(data[:5], 1):
        print(f"{i}. Type: {type(item).__name__}, Value: {item if not isinstance(item, dict) else json.dumps(item, indent=2)[:100] + '...'}")
