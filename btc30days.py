import requests
import time
from datetime import datetime, timedelta
import csv
from pathlib import Path

 # CSV file path (same folder as this script, regardless of where Python is executed from)
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "adress_list.csv"

 # Delay between requests (in seconds) to avoid overloading the API.
 # Decrease to speed up (e.g.: 0.2) or increase if you start getting many HTTP 429 responses.
REQUEST_DELAY = 0.3

print("=" * 80)
print("BTC CHECKER - READING ADDRESSES FROM CSV")
print("=" * 80)
print(f"File: {CSV_PATH}")
print()

# Lê endereços do CSV
 # Read addresses from CSV
addresses = []
try:
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        
        # Skip header if present
        first_row = next(csv_reader, None)
        if first_row:
            # If the first row already looks like an address, keep it
            if first_row[0].startswith(('1', '3', 'bc1')):
                addresses.append(first_row[0].strip())
            
            # Read the rest of the file
            for row in csv_reader:
                if row and len(row) > 0:
                    address = row[0].strip()
                    if address:  # Ignore empty lines
                        addresses.append(address)
    
    print(f"✅ {len(addresses)} addresses loaded from CSV")
    
except FileNotFoundError:
    print(f"❌ ERROR: File not found: {CSV_PATH}")
    print("   Please check if the path is correct.")
    exit()
except Exception as e:
    print(f"❌ ERROR reading CSV: {e}")
    exit()

if len(addresses) == 0:
    print("❌ ERROR: No addresses found in the CSV file")
    exit()

# Remove duplicatas
 # Remove duplicates
addresses = list(set(addresses))
print(f"   ({len(addresses)} unique addresses after removing duplicates)")
print()
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

thirty_days_ago = datetime.now() - timedelta(days=30)
thirty_days_timestamp = int(thirty_days_ago.timestamp())

active_addresses = []  # (endereco, data_ultima_tx, txid)
active_addresses = []  # (address, last_tx_date, txid)
inactive_addresses = []
error_addresses = []

for idx, address in enumerate(addresses, 1):
    try:
        print(f"[{idx}/{len(addresses)}] {address[:35]}...", end=" ", flush=True)
        
        url = f"https://mempool.space/api/address/{address}/txs"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 429:
            print("❌ Rate limit. Waiting 60s...")
            time.sleep(60)
            continue
            
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            error_addresses.append((address, f"HTTP {response.status_code}"))
            time.sleep(REQUEST_DELAY)
            continue
        
        try:
            transactions = response.json()
        except:
            print("❌ Invalid response")
            error_addresses.append((address, "Invalid JSON"))
            time.sleep(REQUEST_DELAY)
            continue
        
        if not transactions or len(transactions) == 0:
            print("⚪ No transactions")
            inactive_addresses.append(address)
            time.sleep(REQUEST_DELAY)
            continue
        
        found = False
        last_tx_date = None
        last_txid = None
        
        # A API normalmente retorna da transação mais recente para a mais antiga
        # The API usually returns transactions from newest to oldest
        for tx in transactions:
            if 'status' in tx and 'block_time' in tx['status']:
                tx_timestamp = tx['status']['block_time']
                
                # If the transaction is already older than 30 days, the next ones
                # are likely even older, so we can stop here
                if tx_timestamp < thirty_days_timestamp:
                    break

                for vout in tx.get('vout', []):
                    if vout.get('scriptpubkey_address') == address:
                        found = True
                        last_tx_date = datetime.fromtimestamp(tx_timestamp)
                        last_txid = tx.get('txid')
                        break
                
                if found:
                    break
        
        if found and last_tx_date:
            # More complete alert: address, date and tx hash of the last relevant tx
            if last_txid:
                print(f"✅ ACTIVE ({last_tx_date.strftime('%d/%m/%Y')}) | TX: {last_txid}")
            else:
                print(f"✅ ACTIVE ({last_tx_date.strftime('%d/%m/%Y')})")

            active_addresses.append((address, last_tx_date, last_txid))
        else:
            print("⚪ No recent txs")
            inactive_addresses.append(address)
        
        time.sleep(REQUEST_DELAY)
        
    except Exception as e:
        print(f"❌ {str(e)[:40]}")
        error_addresses.append((address, str(e)[:100]))

# Resultados
 # Results
print()
print("=" * 80)
print("FINAL RESULTS")
print("=" * 80)
print(f"✅ Active addresses: {len(active_addresses)}")
print(f"⚪ Inactive addresses: {len(inactive_addresses)}")
print(f"❌ Addresses with error: {len(error_addresses)}")
print()

if active_addresses:
    print("ADDRESSES THAT RECEIVED BTC IN THE LAST 30 DAYS:")
    print("-" * 80)
    
    # Sort by last transaction date (most recent first)
    active_addresses.sort(key=lambda x: x[1], reverse=True)
    
    for addr, date, txid in active_addresses:
        if txid:
            print(f"{addr} | {date.strftime('%d/%m/%Y %H:%M')} | TX: {txid}")
        else:
            print(f"{addr} | {date.strftime('%d/%m/%Y %H:%M')}")
    
    # Save to TXT
    with open('ACTIVE_ADDRESSES_LAST30DAYS.txt', 'w', encoding='utf-8') as f:
        f.write(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source file: {CSV_PATH}\n")
        f.write(f"Total: {len(active_addresses)} active addresses\n")
        f.write("=" * 80 + "\n\n")
        for addr, date, txid in active_addresses:
            if txid:
                f.write(f"{addr} | {date.strftime('%Y-%m-%d %H:%M:%S')} | TX: {txid}\n")
            else:
                f.write(f"{addr} | {date.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Also save to CSV
    with open('ACTIVE_ADDRESSES_LAST30DAYS.csv', 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['Address', 'Last_Transaction_Date', 'TxId'])
        for addr, date, txid in active_addresses:
            csv_writer.writerow([addr, date.strftime('%Y-%m-%d %H:%M:%S'), txid or ''])
    
    print()
    print("✅ SAVED:")
    print("   - ACTIVE_ADDRESSES_LAST30DAYS.txt")
    print("   - ACTIVE_ADDRESSES_LAST30DAYS.csv")
else:
    print("⚪ No addresses with recent transactions.")

if error_addresses:
    with open('ADDRESSES_WITH_ERRORS.txt', 'w', encoding='utf-8') as f:
        f.write(f"Addresses with errors during checking\n")
        f.write(f"Source file: {CSV_PATH}\n")
        f.write("=" * 80 + "\n\n")
        for addr, err in error_addresses:
            f.write(f"{addr} | {err}\n")
    
    print()
    print(f"⚠️  {len(error_addresses)} addresses with errors saved in:")
    print("   - ADDRESSES_WITH_ERRORS.txt")

print()
print("=" * 80)
print("DONE!")
print("=" * 80)
