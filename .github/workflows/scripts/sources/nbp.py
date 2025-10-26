"""
NBP (Narodowy Bank Polski) - National Bank of Poland
Data source for PLN exchange rates.
"""

import csv
import requests
from datetime import datetime
from typing import Dict, Optional
from .base import CentralBankSource


class NBPSource(CentralBankSource):
    """Fetch PLN rates from National Bank of Poland"""

    BASE_URL = "https://static.nbp.pl/dane/kursy/Archiwum/archiwum_tab_a_{year}.csv"

    def __init__(self):
        super().__init__('PLN', 'NBP')

    def get_quote_direction(self) -> str:
        """NBP quotes: 1 USD = X PLN"""
        return 'USD_TO_PLN'

    def fetch_rates(self, start_year: int, end_year: Optional[int] = None) -> Dict[str, dict]:
        """
        Fetch PLN rates from NBP.

        NBP provides:
        - Annual CSV files
        - Semicolon-separated values
        - Windows-1250 encoding
        - Date format: YYYYMMDD
        - Decimal separator: comma (Polish style)
        - Column 2: 1USD rate

        Args:
            start_year: Starting year (e.g., 2010)
            end_year: Ending year (defaults to current year)

        Returns:
            Dictionary of rates with direction
        """
        if end_year is None:
            end_year = datetime.now().year

        # historical data available from 2012 onwards
        if start_year < 2012:
            start_year = 2012

        all_rates = {}

        for year in range(start_year, end_year + 1):
            print(f"  Fetching NBP data for {year}...")
            try:
                year_rates = self._fetch_year(year)
                all_rates.update(year_rates)
                print(f"    OK: Got {len(year_rates)} rates for {year}")
            except Exception as e:
                print(f"    WARNING: Failed to fetch {year}: {e}")

        return all_rates

    def _fetch_year(self, year: int) -> Dict[str, dict]:
        """Fetch rates for a single year"""
        url = self.BASE_URL.format(year=year)

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Decode with Windows-1250 encoding
        content = response.content.decode('windows-1250')

        rates = {}
        lines = content.strip().split('\n')

        # Parse CSV (semicolon-separated)
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue

            parts = line.split(';')
            if len(parts) < 3:
                continue

            try:
                # Column 0: date (YYYYMMDD)
                # Column 2: 1USD rate (with comma as decimal separator)
                date_str = parts[0].strip()
                rate_str = parts[2].strip()

                # Convert date format: YYYYMMDD -> YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                normalized_date = date_obj.strftime('%Y-%m-%d')

                # Convert Polish comma to period for decimal
                rate_str = rate_str.replace(',', '.')
                rate = float(rate_str)

                rates[normalized_date] = {
                    'rate': rate,
                    'direction': self.get_quote_direction()
                }

            except (ValueError, IndexError) as e:
                # Skip malformed rows
                continue

        return rates


def main():
    """Test the NBP source"""
    print("Testing NBP Source...")
    print("=" * 50)

    source = NBPSource()
    print(f"Currency: {source.currency_code}")
    print(f"Bank: {source.bank_code}")
    print(f"Quote Direction: {source.get_quote_direction()}")
    print(f"Description: {source._get_description()}")
    print()

    print("Fetching 2024 rates...")
    rates = source.fetch_rates(2024, 2024)

    print(f"\nTotal rates fetched: {len(rates)}")

    # Show first 5 and last 5 rates
    sorted_dates = sorted(rates.keys())
    if sorted_dates:
        print(f"\nFirst rate: {sorted_dates[0]} = {rates[sorted_dates[0]]}")
        print(f"Last rate: {sorted_dates[-1]} = {rates[sorted_dates[-1]]}")

        print("\nSample rates (first 5):")
        for date_str in sorted_dates[:5]:
            print(f"  {date_str}: {rates[date_str]['rate']} {rates[date_str]['direction']}")


if __name__ == '__main__':
    main()
