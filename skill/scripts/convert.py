#!/usr/bin/env python3
"""
Currency conversion script using historical exchange rates.
Simplified from MCP server for general currency conversion use.
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple


class CurrencyConverter:
    """Handles currency conversion using historical exchange rates"""

    # Mapping of central bank codes to currency codes
    BANK_TO_CURRENCY = {
        'ECB': 'EUR',  # European Central Bank
        'NBP': 'PLN',  # Narodowy Bank Polski (National Bank of Poland)
        'RBA': 'AUD',  # Reserve Bank of Australia
    }

    def __init__(self, rates_dir: str = None):
        """
        Initialize the converter with exchange rate data.

        Args:
            rates_dir: Directory containing exchange rate CSV files (default: ../rates)
        """
        if rates_dir is None:
            # Default to rates directory relative to script location
            script_dir = Path(__file__).parent
            rates_dir = script_dir.parent / "rates"

        self.rates_dir = Path(rates_dir)
        self.exchange_rates: Dict[str, Dict[date, float]] = {}
        self._load_all_rates()

    def _load_all_rates(self):
        """Load all exchange rate files from the rates directory."""
        if not self.rates_dir.exists():
            return

        # Discover currencies by scanning directory (using bank codes)
        for bank_dir in self.rates_dir.iterdir():
            if bank_dir.is_dir():
                bank_code = bank_dir.name.upper()
                # Map bank code to currency code
                currency = self.BANK_TO_CURRENCY.get(bank_code, bank_code)
                self.exchange_rates[currency] = {}

                # Load all CSV files in all year subdirectories
                for year_dir in bank_dir.iterdir():
                    if year_dir.is_dir():
                        for csv_file in year_dir.glob("*.csv"):
                            self._load_rate_file(currency, csv_file)

    def _load_rate_file(self, currency: str, file_path: Path):
        """Load a single exchange rate CSV file."""
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row

                for row in reader:
                    if len(row) >= 2:
                        try:
                            rate_date = datetime.strptime(row[0], "%Y-%m-%d").date()
                            rate = float(row[1])
                            self.exchange_rates[currency][rate_date] = rate
                        except (ValueError, IndexError):
                            # Skip malformed rows
                            continue
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}", file=sys.stderr)

    def get_available_currencies(self) -> Dict[str, dict]:
        """
        Get information about all available currencies.

        Returns:
            Dictionary with currency codes and their date ranges
        """
        currencies = {}

        for currency, rates in self.exchange_rates.items():
            if rates:
                dates = sorted(rates.keys())
                currencies[currency] = {
                    "earliest_date": dates[0].isoformat(),
                    "latest_date": dates[-1].isoformat(),
                    "total_days": len(dates)
                }

        return currencies

    def _find_rate_for_date(self, currency: str, target_date: date) -> Tuple[Optional[float], Optional[date]]:
        """
        Find exchange rate for the given date or closest earlier date.
        Searches backwards up to 30 days.

        Args:
            currency: Currency code (e.g., 'PLN')
            target_date: Requested date

        Returns:
            Tuple of (rate, date_used) or (None, None) if not found
        """
        if currency not in self.exchange_rates:
            return None, None

        rates = self.exchange_rates[currency]

        if not rates:
            return None, None

        # Try exact date first
        if target_date in rates:
            return rates[target_date], target_date

        # Search backwards up to 30 days
        for days_back in range(1, 31):
            check_date = target_date - timedelta(days=days_back)
            if check_date in rates:
                return rates[check_date], check_date

        return None, None

    def convert(self, amount_usd: float, target_currency: str, conversion_date: date) -> dict:
        """
        Convert USD amount to target currency.

        Args:
            amount_usd: Amount in USD
            target_currency: Target currency code
            conversion_date: Date for conversion

        Returns:
            Dictionary with conversion result or error
        """
        currency = target_currency.upper()

        # Check if currency is supported
        if currency not in self.exchange_rates:
            available = sorted(self.exchange_rates.keys())
            return {
                "status": "error",
                "error": f"Currency {target_currency} not supported. Available currencies: {', '.join(available)}",
                "available_currencies": available,
                "requested_currency": target_currency
            }

        # Check if currency has any rates
        if not self.exchange_rates[currency]:
            # Find bank code for this currency
            bank_code = next((k for k, v in self.BANK_TO_CURRENCY.items() if v == currency), currency)
            return {
                "status": "error",
                "error": f"Currency {currency} is configured but has no rate data. Please check rates/{bank_code}/ directory",
                "currency": currency
            }

        # Find appropriate rate
        rate, rate_date = self._find_rate_for_date(currency, conversion_date)

        if rate is None:
            # Determine if date is too early or too late
            all_dates = sorted(self.exchange_rates[currency].keys())
            earliest = all_dates[0]
            latest = all_dates[-1]

            if conversion_date < earliest:
                return {
                    "status": "error",
                    "error": f"No exchange rate found for {currency} on {conversion_date.isoformat()}. Earliest available rate: {earliest.isoformat()}",
                    "requested_date": conversion_date.isoformat(),
                    "earliest_date": earliest.isoformat(),
                    "currency": currency
                }
            else:
                return {
                    "status": "error",
                    "error": f"No exchange rate found for {currency} on or before {conversion_date.isoformat()}. Latest available rate: {latest.isoformat()}",
                    "requested_date": conversion_date.isoformat(),
                    "latest_date": latest.isoformat(),
                    "currency": currency
                }

        # Successful conversion
        converted_amount = amount_usd * rate

        return {
            "status": "success",
            "amount_usd": amount_usd,
            "converted_amount": round(converted_amount, 2),
            "currency": currency,
            "rate": rate,
            "rate_date": rate_date.isoformat(),
            "requested_date": conversion_date.isoformat()
        }


def parse_date(date_string: str) -> date:
    """
    Parse date string in various formats.

    Supported formats:
    - YYYY-MM-DD (ISO format)
    - MM/DD/YYYY (US format)
    - DD-MM-YYYY (EU format)

    Args:
        date_string: Date string to parse

    Returns:
        date object

    Raises:
        ValueError: If date format is not recognized
    """
    formats = [
        "%Y-%m-%d",      # 2025-01-15
        "%m/%d/%Y",      # 01/15/2025
        "%d-%m-%Y",      # 15-01-2025
        "%Y/%m/%d",      # 2025/01/15
        "%d/%m/%Y",      # 15/01/2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: '{date_string}'. Expected formats: YYYY-MM-DD, MM/DD/YYYY, or DD-MM-YYYY")


def main():
    parser = argparse.ArgumentParser(
        description="Convert USD to foreign currencies using historical exchange rates"
    )
    parser.add_argument(
        "amount",
        nargs="?",
        type=float,
        help="Amount in USD to convert"
    )
    parser.add_argument(
        "currency",
        nargs="?",
        type=str,
        help="Target currency code (e.g., PLN, EUR, GBP)"
    )
    parser.add_argument(
        "date",
        nargs="?",
        type=str,
        help="Date for conversion (YYYY-MM-DD, MM/DD/YYYY, or DD-MM-YYYY)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available currencies and their date ranges"
    )
    parser.add_argument(
        "--rates-dir",
        type=str,
        help="Custom directory containing exchange rate files"
    )

    args = parser.parse_args()

    # Initialize converter
    converter = CurrencyConverter(rates_dir=args.rates_dir)

    # Handle --list command
    if args.list:
        currencies = converter.get_available_currencies()
        result = {
            "status": "success",
            "currencies": currencies
        }
        print(json.dumps(result, indent=2))
        return 0

    # Validate required arguments
    if not all([args.amount, args.currency, args.date]):
        parser.print_help()
        return 1

    # Parse date
    try:
        conversion_date = parse_date(args.date)
    except ValueError as e:
        result = {
            "status": "error",
            "error": str(e),
            "requested_date": args.date
        }
        print(json.dumps(result, indent=2))
        return 1

    # Perform conversion
    result = converter.convert(args.amount, args.currency, conversion_date)
    print(json.dumps(result, indent=2))

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
