"""
Base class for central bank data sources.
Defines the interface that all sources must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import date


class CentralBankSource(ABC):
    """Abstract base class for central bank exchange rate sources"""

    def __init__(self, currency_code: str, bank_code: str):
        """
        Initialize the source.

        Args:
            currency_code: ISO currency code (e.g., 'PLN', 'EUR')
            bank_code: Central bank code (e.g., 'NBP', 'ECB')
        """
        self.currency_code = currency_code
        self.bank_code = bank_code

    @abstractmethod
    def get_quote_direction(self) -> str:
        """
        Get the quote direction for this source.

        Returns:
            Direction string: 'USD_TO_XXX' or 'XXX_TO_USD'

        Examples:
            'USD_TO_PLN' means: 1 USD = X PLN
            'EUR_TO_USD' means: 1 EUR = X USD
        """
        pass

    @abstractmethod
    def fetch_rates(self, start_year: int, end_year: Optional[int] = None) -> Dict[str, dict]:
        """
        Fetch exchange rates for the specified year range.

        Args:
            start_year: First year to fetch (e.g., 2010)
            end_year: Last year to fetch (defaults to current year)

        Returns:
            Dictionary mapping date strings to rate data:
            {
                '2024-01-01': {
                    'rate': 4.0015,
                    'direction': 'USD_TO_PLN'
                },
                '2024-01-02': {
                    'rate': 4.0123,
                    'direction': 'USD_TO_PLN'
                }
            }
        """
        pass

    def get_source_info(self) -> dict:
        """
        Get metadata about this source.

        Returns:
            Dictionary with source information
        """
        return {
            'currency': self.currency_code,
            'bank': self.bank_code,
            'quote_direction': self.get_quote_direction(),
            'description': self._get_description()
        }

    def _get_description(self) -> str:
        """Get human-readable description of quote direction"""
        direction = self.get_quote_direction()
        base, quote = direction.split('_TO_')
        return f"1 {base} = X {quote}"
