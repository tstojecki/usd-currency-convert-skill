"""
ECB (European Central Bank)
Data source for EUR exchange rates.
"""

import csv
import requests
import zipfile
import io
from datetime import datetime
from typing import Dict, Optional
from .base import CentralBankSource


class ECBSource(CentralBankSource):
    """Fetch EUR rates from European Central Bank"""

    # single ZIP file with all historical data
    DATA_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"
    CSV_FILENAME = "eurofxref-hist.csv"

    def __init__(self):
        super().__init__('EUR', 'ECB')

    def get_quote_direction(self) -> str:
        """ECB quotes: 1 EUR = X USD"""
        return 'EUR_TO_USD'

    def fetch_rates(self, start_year: int, end_year: Optional[int] = None) -> Dict[str, dict]:
        """
        Fetch EUR rates from ECB.

        ECB provides:
        - Single ZIP file with all historical data (1999-present)
        - CSV inside ZIP
        - Comma-separated values
        - UTF-8 encoding
        - Date format: MM/DD/YYYY or DD-Mon-YYYY
        - USD column contains EUR→USD rate

        Args:
            start_year: Starting year (e.g., 2010)
            end_year: Ending year (defaults to current year)

        Returns:
            Dictionary of rates with direction
        """
        if end_year is None:
            end_year = datetime.now().year

        print(f"  Fetching ECB data (historical ZIP)...")

        try:
            response = requests.get(self.DATA_URL, timeout=60)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                with zf.open(self.CSV_FILENAME) as csvfile:
                    content = csvfile.read().decode('utf-8')

            rates = self._parse_csv(content, start_year, end_year)
            print(f"    OK: Got {len(rates)} rates from ECB")

            return rates

        except Exception as e:
            print(f"    ERROR: Error fetching ECB data: {e}")
            raise

    def _parse_csv(self, content: str, start_year: int, end_year: int) -> Dict[str, dict]:
        """Parse the ECB CSV content"""
        rates = {}
        lines = content.strip().split('\n')

        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            try:
                date_str = row.get('Date', '').strip()
                if not date_str:
                    continue

                date_obj = self._parse_date(date_str)
                if not date_obj:
                    continue

                if not (start_year <= date_obj.year <= end_year):
                    continue

                usd_rate_str = row.get('USD', '').strip()
                if not usd_rate_str or usd_rate_str == 'N/A':
                    continue

                rate = float(usd_rate_str)

                # Normalize date to YYYY-MM-DD
                normalized_date = date_obj.strftime('%Y-%m-%d')

                rates[normalized_date] = {
                    'rate': rate,
                    'direction': self.get_quote_direction()
                }

            except (ValueError, KeyError) as e:
                # Skip malformed rows
                continue

        return rates

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ECB date format (tries multiple formats)"""
        formats = [
            '%d/%m/%Y',  # 24/10/2025
            '%m/%d/%Y',  # 10/24/2025 (sometimes used)
            '%d-%b-%Y',  # 24-Oct-2025
            '%Y-%m-%d',  # 2025-10-24
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None


def main():
    """Test the ECB source"""
    print("Testing ECB Source...")
    print("=" * 50)

    source = ECBSource()
    print(f"Currency: {source.currency_code}")
    print(f"Bank: {source.bank_code}")
    print(f"Quote Direction: {source.get_quote_direction()}")
    print(f"Description: {source._get_description()}")
    print()

    print("Fetching 2024 rates...")
    rates = source.fetch_rates(2024, 2024)

    print(f"\nTotal rates fetched: {len(rates)}")

    sorted_dates = sorted(rates.keys())
    if sorted_dates:
        print(f"\nFirst rate: {sorted_dates[0]} = {rates[sorted_dates[0]]}")
        print(f"Last rate: {sorted_dates[-1]} = {rates[sorted_dates[-1]]}")

        print("\nSample rates (first 5):")
        for date_str in sorted_dates[:5]:
            print(f"  {date_str}: {rates[date_str]['rate']} {rates[date_str]['direction']}")


if __name__ == '__main__':
    main()
