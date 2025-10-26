"""
RBA (Reserve Bank of Australia)
Data source for AUD exchange rates.
"""

import requests
import pandas as pd
import io
from datetime import datetime
from typing import Dict, Optional
from .base import CentralBankSource


class RBASource(CentralBankSource):
    """Fetch AUD rates from Reserve Bank of Australia"""

    # data in 4-year intervals
    BASE_URL = "https://www.rba.gov.au/statistics/tables/xls-hist/{range}.xls"

    URL_RANGES = [
        {'range': '2010-2013', 'years': (2010, 2013)},
        {'range': '2014-2017', 'years': (2014, 2017)},
        {'range': '2018-2022', 'years': (2018, 2022)},
        {'range': '2023-current', 'years': (2023, 9999)},  # 9999 for "current"
    ]

    def __init__(self):
        super().__init__('AUD', 'RBA')

    def get_quote_direction(self) -> str:
        """RBA quotes: 1 AUD = X USD"""
        return 'AUD_TO_USD'

    def fetch_rates(self, start_year: int, end_year: Optional[int] = None) -> Dict[str, dict]:
        """
        Fetch AUD rates from RBA.

        RBA provides:
        - Excel files (.xls) in 4-year intervals
        - Skip first 10 header rows
        - Date format: DD-Mon-YYYY (e.g., 03-Jan-2023)
        - Column "A$1=USD" contains AUD→USD rate

        Args:
            start_year: Starting year (e.g., 2010)
            end_year: Ending year (defaults to current year)

        Returns:
            Dictionary of rates with direction
        """
        if end_year is None:
            end_year = datetime.now().year

        all_rates = {}

        for url_info in self.URL_RANGES:
            range_start, range_end = url_info['years']

            if range_end < start_year or range_start > end_year:
                continue

            print(f"  Fetching RBA data for {url_info['range']}...")

            try:
                range_rates = self._fetch_range(url_info['range'], start_year, end_year)
                all_rates.update(range_rates)
                print(f"    OK: Got {len(range_rates)} rates from {url_info['range']}")
            except Exception as e:
                print(f"    WARNING: Failed to fetch {url_info['range']}: {e}")

        return all_rates

    def _fetch_range(self, range_str: str, start_year: int, end_year: int) -> Dict[str, dict]:
        """Fetch rates for a specific URL range"""
        url = self.BASE_URL.format(range=range_str)

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Skip first 10 header rows as per RBA format
        df = pd.read_excel(
            io.BytesIO(response.content),
            skiprows=10,
            engine='xlrd'  # For .xls files
        )

        rates = {}

        date_col = None
        usd_col = None

        for col in df.columns:
            col_str = str(col).strip()
            if 'date' in col_str.lower() or df[col].dtype == 'datetime64[ns]':
                date_col = col
            elif 'a$1=usd' in col_str.lower() or 'aud/usd' in col_str.lower():
                usd_col = col

        if date_col is None or usd_col is None:
            if len(df.columns) >= 2:
                date_col = df.columns[0]
                usd_col = df.columns[1]  # Usually second column
            else:
                raise ValueError(f"Could not identify date and USD rate columns in {range_str}")

        for _, row in df.iterrows():
            try:
                date_val = row[date_col]

                if pd.isna(date_val):
                    continue

                if isinstance(date_val, str):
                    date_obj = datetime.strptime(date_val, '%d-%b-%Y')
                elif isinstance(date_val, pd.Timestamp):
                    date_obj = date_val.to_pydatetime()
                else:
                    date_obj = pd.to_datetime(date_val).to_pydatetime()

                if not (start_year <= date_obj.year <= end_year):
                    continue

                rate_val = row[usd_col]
                if pd.isna(rate_val):
                    continue

                rate = float(rate_val)

                # Normalize date to YYYY-MM-DD
                normalized_date = date_obj.strftime('%Y-%m-%d')

                rates[normalized_date] = {
                    'rate': rate,
                    'direction': self.get_quote_direction()
                }

            except (ValueError, KeyError, TypeError) as e:
                # Skip malformed rows
                continue

        return rates


def main():
    """Test the RBA source"""
    print("Testing RBA Source...")
    print("=" * 50)

    source = RBASource()
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
