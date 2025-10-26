#!/usr/bin/env python3
"""
Main orchestrator for fetching exchange rates from all sources.
Runs weekly via GitHub Actions to update rate data in rates/ directory.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent))

from sources import NBPSource, ECBSource, RBASource

# Configuration
START_YEAR = 2010  # Historical coverage from 2010
SCRIPT_DIR = Path(__file__).parent  # .github/workflows/scripts/
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # repository root
SKILL_DIR = REPO_ROOT / "skill"  # skill/
RATES_DIR = SKILL_DIR / "rates"  # skill/rates/

# Define all sources (ordered by priority: EUR, PLN, AUD)
SOURCES = {
    'EUR': ECBSource(),
    'PLN': NBPSource(),
    'AUD': RBASource(),
}


def load_existing_rates(currency: str) -> dict:
    """Load existing rates for a currency from CSV files in rates/"""
    existing = {}
    bank_code = SOURCES[currency].bank_code
    currency_dir = RATES_DIR / bank_code

    if not currency_dir.exists():
        return existing

    # Read all year directories
    for year_dir in currency_dir.glob('*/'):
        if not year_dir.is_dir():
            continue

        rates_file = year_dir / 'rates.csv'
        if rates_file.exists():
            with open(rates_file, 'r') as f:
                # Skip header
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        date_str, rate_str, direction = parts[0], parts[1], parts[2]
                        existing[date_str] = {
                            'rate': float(rate_str),
                            'direction': direction
                        }

    return existing


def save_rates_by_year(currency: str, rates: dict):
    """Save rates organized by year with direction to skill/rates/{BANK}/{YEAR}/"""
    bank_code = SOURCES[currency].bank_code
    rates_by_year = {}

    # Group by year
    for date_str, rate_data in rates.items():
        year = date_str[:4]
        if year not in rates_by_year:
            rates_by_year[year] = {}
        rates_by_year[year][date_str] = rate_data

    # Save each year
    for year, year_rates in rates_by_year.items():
        year_dir = RATES_DIR / bank_code / year
        year_dir.mkdir(parents=True, exist_ok=True)

        rates_file = year_dir / 'rates.csv'
        with open(rates_file, 'w') as f:
            f.write("date,rate,direction\n")
            for date in sorted(year_rates.keys()):
                rate = year_rates[date]['rate']
                direction = year_rates[date]['direction']
                f.write(f"{date},{rate},{direction}\n")

        print(f"    Saved {len(year_rates)} rates to {rates_file}")


def main():
    """Main execution"""
    print("=" * 60)
    print("Exchange Rate Fetcher")
    print("=" * 60)
    print(f"Skill directory: {SKILL_DIR}")
    print(f"Rates directory: {RATES_DIR}")
    print()

    changes_made = False
    summary = {}

    for currency, source in SOURCES.items():
        print(f"[{currency}] Processing {currency} ({source.bank_code})...")
        print(f"   Quote Direction: {source.get_quote_direction()}")

        try:
            # Fetch new rates
            current_year = datetime.now().year
            new_rates = source.fetch_rates(START_YEAR, current_year)

            # Load existing rates from skill/rates/
            existing_rates = load_existing_rates(currency)

            # Find new dates
            new_dates = set(new_rates.keys()) - set(existing_rates.keys())

            summary[currency] = {
                'fetched': len(new_rates),
                'existing': len(existing_rates),
                'new': len(new_dates),
                'bank': source.bank_code,
                'direction': source.get_quote_direction()
            }

            if new_dates:
                # Merge rates
                all_rates = {**existing_rates, **new_rates}
                save_rates_by_year(currency, all_rates)
                changes_made = True
                print(f"   SUCCESS: Added {len(new_dates)} new rates")
            else:
                print(f"   INFO: No new rates (all up to date)")

            print()

        except Exception as e:
            print(f"   ERROR: {e}")
            print()
            summary[currency] = {'error': str(e)}

    # Print summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for currency, info in summary.items():
        if 'error' in info:
            print(f"{currency}: ERROR - {info['error']}")
        else:
            print(f"{currency} ({info['bank']} - {info['direction']}): {info['new']} new rates")

    print()
    print(f"Changes made: {'YES' if changes_made else 'NO'}")
    print(f"Output location: {RATES_DIR}/")

    # Exit with appropriate code for GitHub Actions
    # 0 = no changes, 1 = changes made
    return 0 if not changes_made else 1


if __name__ == '__main__':
    sys.exit(main())
