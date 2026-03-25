# BTC Address Activity Checker

This is a simple Python script that checks recent on-chain activity for a list of Bitcoin addresses.

Given a CSV file with one BTC address per line, the script:
- Reads all addresses from the CSV (skipping an optional header row)
- Queries the mempool.space API for each address
- Looks at transactions from the last 30 days
- For each address, finds **the most recent transaction in that 30-day window** where the address appears as an output
- Classifies addresses as **active** (at least one transaction in the last 30 days) or **inactive**
- Saves summary results to text and CSV files

## How it works

- Input file: `adress_list.csv` in the **same folder** as `btc30days.py`
  - The file should contain one Bitcoin address per line
  - The first row may be a header; if it is a valid address, it will be used normally
- The script removes duplicate addresses before querying the API
- For each address, it calls:
  - `https://mempool.space/api/address/<ADDRESS>/txs`
- It checks each transaction from **newest to oldest** and stops scanning as soon as it reaches transactions older than 30 days.
- When it finds a matching output (`scriptpubkey_address == ADDRESS`) within the last 30 days, it records:
  - Address
  - Timestamp of the transaction
  - Transaction ID (txid)

## Output files

After running, the script produces:

- `ACTIVE_ADDRESSES_LAST30DAYS.txt`
  - Human-readable list of active addresses
  - Includes check time, source CSV path, total active addresses, and for each address:
    - Address | last transaction date | txid
- `ACTIVE_ADDRESSES_LAST30DAYS.csv`
  - Same data in CSV format, with columns:
    - `Address`, `Last_Transaction_Date`, `TxId`
- `ADDRESSES_WITH_ERRORS.txt` (only if there were errors)
  - Addresses for which the API request failed or returned invalid data
  - Includes a short error description for each address

Addresses with no transactions in the last 30 days are printed to the console as "No recent txs" but are not written to a separate file.

## Requirements

- Python 3.8+
- Internet connection (to reach mempool.space)

Python dependencies (also listed in `requirements.txt`):

- `requests`

## Installation

1. Clone or download this repository.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Prepare your input CSV in the same folder as `btc30days.py`:
   - File name: `adress_list.csv`
   - One BTC address per line.

## Usage

From the project folder, run:

```bash
python btc30days.py
```

or, specifying Python explicitly:

```bash
python3 btc30days.py
```

The script will:
- Read `adress_list.csv`
- Print progress for each address
- Save the results to the output files listed above

If you run the script from a different working directory, it will still correctly locate `adress_list.csv` as long as it is in the **same folder as `btc30days.py`**, because the script builds an absolute path based on its own location.

## Notes

- The script includes a configurable delay (`REQUEST_DELAY`) between requests to avoid hitting mempool.space rate limits.
- If the API returns HTTP 429 (rate limited), the script automatically waits 60 seconds and continues.
- You can tune `REQUEST_DELAY` inside `btc30days.py` if you want to speed it up or be more conservative with requests.
