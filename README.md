# USD Currency Convert - Claude Skill

A Claude skill that converts US Dollar amounts to foreign currencies using historical exchange rates from official central banks.

## Supported Currencies

- **EUR** (Euro) - from ECB (2010-present)
- **PLN** (Polish Zloty) - from NBP (2012-present)
- **AUD** (Australian Dollar) - from RBA (2010-present)

Coverage: 11,500+ daily exchange rates from 2010-2025

## Download

**[Download usd-currency-convert.zip](releases/usd-currency-convert.zip)**

See [releases/README.md](releases/README.md) for version history.

## Installation

### For Claude Desktop

1. Download the latest release from [releases/](releases/)
2. Upload the ZIP file through Claude Desktop, or extract to:
   - **Windows**: `%USERPROFILE%\.claude\skills\usd-currency-convert`
   - **macOS/Linux**: `~/.claude/skills/usd-currency-convert`

### For Claude Web/API

Upload the ZIP file from [releases/](releases/) through the Claude interface.

## Usage

Once installed, Claude will automatically use this skill when you ask questions like:

- "Convert $250 to EUR on March 20, 2024"
- "What's the exchange rate for EUR on March 20, 2024?"
- "Convert $1500 to Polish złoty on January 15, 2025"
- "Convert $1000 USD to AUD as of December 1, 2024"

### Requirements

- Python 3.7 or higher
- No external dependencies for conversion (uses only Python standard library)

## Data Sources & Attributions

Exchange rate data is sourced from official central banks and is public data:

- **ECB rates**: © European Central Bank
  - Source: https://www.ecb.europa.eu/stats/eurofxref/
  - Coverage: 2010-present

- **NBP rates**: © Narodowy Bank Polski (Polish National Bank)
  - Source: https://api.nbp.pl/
  - Coverage: 2012-present

- **RBA rates**: © Reserve Bank of Australia
  - Source: https://www.rba.gov.au/statistics/historical-data.html
  - Coverage: 2010-present

All central bank data is provided as public information for reference purposes. This skill redistributes publicly available exchange rate data under the terms provided by each central bank.

## Disclaimer

This skill provides historical exchange rate data for informational purposes only. Exchange rates are sourced from official central banks but:

- Rates may have a 1-2 business day delay
- Weekend/holiday dates use the most recent available rate
- This is not financial advice - consult appropriate professionals for financial decisions
- Always verify critical conversions with official sources

## License

Apache License 2.0

Copyright 2025

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

See [skill/LICENSE.txt](skill/LICENSE.txt) for complete license text and data source attributions.

## For Developers

### Manual Testing

Test the conversion script directly:

```bash
# Show available currencies
cd skill
python scripts/convert.py --list

# Convert USD to EUR
python scripts/convert.py 250 EUR 2024-03-20

# Convert USD to PLN
python scripts/convert.py 1500 PLN 2025-01-15

# Convert USD to AUD
python scripts/convert.py 1000 AUD 2024-12-01

```
### Rates Automation

See scripts workflow and scripts in `.github/workflows/scripts/`.
Requirements: `pip install pandas requests openpyxl xlrd`

### Adding New Rates

To manually add or update exchange rates:

1. Create a CSV file with the format:
   ```csv
   date,rate,direction
   2024-01-01,3.931235,USD_TO_PLN
   2024-01-02,3.928765,USD_TO_PLN
   ```

2. Place it in the appropriate directory:
   - For EUR: `skill/rates/ECB/{YEAR}/rates.csv`
   - For PLN: `skill/rates/NBP/{YEAR}/rates.csv`
   - For AUD: `skill/rates/RBA/{YEAR}/rates.csv`

3. The skill will automatically detect and use the new rates

**Quote Directions:**
- `EUR_TO_USD` - 1 EUR = X USD (ECB quotes this way)
- `USD_TO_PLN` - 1 USD = X PLN (NBP quotes this way)
- `AUD_TO_USD` - 1 AUD = X USD (RBA quotes this way)