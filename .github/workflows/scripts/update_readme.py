#!/usr/bin/env python3
"""
Update README.md with version info (currently disabled - README managed manually).
"""

import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent  # .github/workflows/scripts/
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # repository root
SKILL_DIR = REPO_ROOT / "skill"  # skill/
METADATA_FILE = SKILL_DIR / "metadata.json"  # skill/metadata.json


def update_readme():
    """Update README with latest version info"""

    # Load metadata
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    version = metadata['version']

    # Currently README is managed manually
    # This script is here for future automation if needed
    print(f"SUCCESS: README.md check complete (v{version})")
    print("NOTE: README.md is currently managed manually")


if __name__ == '__main__':
    update_readme()
