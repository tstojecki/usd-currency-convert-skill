#!/usr/bin/env python3
"""
Update metadata.json with version, coverage, and quote directions.
"""

import json
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent  # .github/workflows/scripts/
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # repository root
SKILL_DIR = REPO_ROOT / "skill"  # skill/
RATES_DIR = SKILL_DIR / "rates"  # skill/rates/
METADATA_FILE = SKILL_DIR / "metadata.json"  # skill/metadata.json

# Bank to currency mapping
BANK_TO_CURRENCY = {
    'NBP': 'PLN',
    'ECB': 'EUR',
    'RBA': 'AUD',
}

QUOTE_DIRECTIONS = {
    'NBP': 'USD_TO_PLN',
    'ECB': 'EUR_TO_USD',
    'RBA': 'AUD_TO_USD',
}

BANK_NAMES = {
    'NBP': 'Narodowy Bank Polski (National Bank of Poland)',
    'ECB': 'European Central Bank',
    'RBA': 'Reserve Bank of Australia',
}


def scan_rates_coverage(bank_code: str) -> dict:
    """Scan rates directory for coverage info"""
    bank_dir = RATES_DIR / bank_code

    if not bank_dir.exists():
        return None

    all_dates = []

    for year_dir in bank_dir.glob('*/'):
        if not year_dir.is_dir():
            continue

        rates_file = year_dir / 'rates.csv'
        if rates_file.exists():
            with open(rates_file, 'r') as f:
                next(f)  # Skip header
                for line in f:
                    parts = line.strip().split(',')
                    if parts:
                        all_dates.append(parts[0])

    if not all_dates:
        return None

    sorted_dates = sorted(all_dates)

    return {
        'coverage_start': sorted_dates[0],
        'coverage_end': sorted_dates[-1],
        'total_days': len(sorted_dates)
    }


def update_metadata():
    """Update metadata.json in skill/ directory"""

    # Load existing metadata or create new
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)

        # Increment minor version
        version_parts = metadata.get('version', '1.0').split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        new_version = f"{major}.{minor + 1}"
    else:
        metadata = {}
        new_version = "1.0"

    # Update version and release date
    metadata['version'] = new_version
    metadata['release_date'] = datetime.utcnow().isoformat() + 'Z'

    # Update currency info
    if 'currencies' not in metadata:
        metadata['currencies'] = {}

    for bank_code, currency_code in BANK_TO_CURRENCY.items():
        coverage = scan_rates_coverage(bank_code)

        if coverage:
            metadata['currencies'][currency_code] = {
                'source': BANK_NAMES[bank_code],
                'source_code': bank_code,
                'quote_direction': QUOTE_DIRECTIONS[bank_code],
                'supports': [f"USD⇄{currency_code}"],
                **coverage,
                'last_fetched': datetime.utcnow().isoformat() + 'Z'
            }

    # Write updated metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"SUCCESS: Updated metadata to version {new_version}")
    print(f"File: {METADATA_FILE}")

    return new_version


if __name__ == '__main__':
    update_metadata()
