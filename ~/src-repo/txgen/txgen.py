#!/usr/bin/env python3
"""
Bitcoin Transaction Generator for Test Data

This script generates a series of interdependent Bitcoin transactions on regtest
for testing multi-wallet accounting reconciliation.
"""

import os
import json
import random
import datetime
import numpy as np
from decimal import Decimal, getcontext
from collections import defaultdict

# Bitcoin-related imports
import bitcoin
from bitcoin.core import (
    b2x, lx, COIN, COutPoint, CTxIn, CTxOut, CTransaction, CMutableTransaction
)
from bitcoin.core.script import CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret
from bitcoin.rpc import Proxy

# Set the network to regtest
bitcoin.SelectParams('regtest')

# Configure decimal precision
getcontext().prec = 8

class WalletSimulator:
    """Class to simulate Bitcoin wallets and transactions"""
    
    def __init__(self, data_dir='data', start_date=None, end_date=None, seed=42):
        """Initialize the wallet simulator"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Set date range (default: 2024 full year)
        self.start_date = start_date or datetime.date(2024, 1, 1)
        self.end_date = end_date or datetime.date(2024, 12, 31)
        
        # Set random seed for reproducibility
        random.seed(seed)
        np.random.seed(seed)
        
        # Initialize wallets and transactions
        self.wallets = {}
        self.transactions = []
        self.block_heights = {}
        self.utxos = defaultdict(list)
        self.exchange_rates = {}
        
        # Bitcoin RPC connection (will be initialized later)
        self.rpc = None
        
        # Generate exchange rates for the year
        self._generate_exchange_rates()
    
    def _generate_exchange_rates(self):
        """Generate simulated BTC/USD exchange rates for the date range"""
        # Start with a base rate around $59,000 (early 2024)
        base_rate = 59000
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Add some random fluctuation (between -5% and +5%)
            fluctuation = random.uniform(-0.05, 0.05)
            rate = base_rate * (1 + fluctuation)
            
            # Update base rate gradually over time (trend)
            trend_factor = random.uniform(-0.02, 0.03)  # Slight upward bias
            base_rate = base_rate * (1 + trend_factor)
            
            # Save the rate for this date
            self.exchange_rates[current_date.isoformat()] = round(rate, 2)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        # Save exchange rates to file
        with open(os.path.join(self.data_dir, 'exchange_rates.json'), 'w') as f:
            json.dump(self.exchange_rates, f, indent=2)
    
    def generate_wallets(self):
        """Generate the three required wallets"""
        # Wallet A: Invoicing wallet
        self.wallets['A'] = {
            'name': 'Invoicing',
            'privkey': CBitcoinSecret.from_secret_bytes(random.randbytes(32)),
            'addresses': []
        }
        
        # Wallet B: Treasury wallet
        self.wallets['B'] = {
            'name': 'Treasury',
            'privkey': CBitcoinSecret.from_secret_bytes(random.randbytes(32)),
            'addresses': []
        }
        
        # Wallet C: Checking wallet
        self.wallets['C'] = {
            'name': 'Checking',
            'privkey': CBitcoinSecret.from_secret_bytes(random.randbytes(32)),
            'addresses': []
        }
        
        # Generate multiple addresses for each wallet
        for wallet_id in self.wallets:
            wallet = self.wallets[wallet_id]
            # Generate derived addresses
            num_addresses = 10000 if wallet_id == 'A' else 100
            for _ in range(num_addresses):
                # In a real implementation, we would derive from xpub
                # For simplicity, we're just generating random keys here
                key = CBitcoinSecret.from_secret_bytes(random.randbytes(32))
                address = CBitcoinAddress.from_pubkey(key.pub)
                wallet['addresses'].append({
                    'address': str(address),
                    'privkey': key
                })
        
        # Save wallet data
        self._save_wallet_data()
    
    def _save_wallet_data(self):
        """Save wallet data to a JSON file"""
        wallet_data = {}
        for wallet_id, wallet in self.wallets.items():
            wallet_data[wallet_id] = {
                'name': wallet['name'],
                'addresses': [addr['address'] for addr in wallet['addresses']]
            }
        
        with open(os.path.join(self.data_dir, 'wallets.json'), 'w') as f:
            json.dump(wallet_data, f, indent=2)
    
    def usd_to_btc(self, usd_amount, date):
        """Convert USD amount to BTC based on the exchange rate for the given date"""
        # Get the exchange rate for the date
        date_str = date.isoformat()
        rate = self.exchange_rates.get(date_str)
        if not rate:
            # Use closest date if exact date not found
            closest_date = min(self.exchange_rates.keys(), key=lambda x: abs(datetime.date.fromisoformat(x) - date))
            rate = self.exchange_rates[closest_date]
        
        # Convert USD to BTC
        btc_amount = Decimal(usd_amount) / Decimal(rate)
        return btc_amount
    
    def btc_to_satoshis(self, btc_amount):
        """Convert BTC amount to satoshis"""
        return int(btc_amount * COIN)
    
    def generate_invoice_transactions(self):
        """Generate 10,000 transactions for Wallet A (invoicing wallet)"""
        print("Generating invoicing transactions...")
        
        # Get addresses from wallet A
        wallet_a_addresses = [addr['address'] for addr in self.wallets['A']['addresses']]
        
        # Set up date distribution to spread over the year
        start_ordinal = self.start_date.toordinal()
        end_ordinal = self.end_date.toordinal()
        days_range = end_ordinal - start_ordinal + 1
        
        txs = []
        block_height = 1  # Start block height
        
        # Generate 10,000 transactions
        for i in range(10000):
            # Randomly select a date
            tx_date_ordinal = random.randint(start_ordinal, end_ordinal)
            tx_date = datetime.date.fromordinal(tx_date_ordinal)
            
            # Randomly select a USD amount between $100-$2000
            usd_amount = random.uniform(100, 2000)
            
            # Convert to BTC
            btc_amount = self.usd_to_btc(usd_amount, tx_date)
            satoshis = self.btc_to_satoshis(btc_amount)
            
            # Pick a random address from wallet A
            recipient_address = random.choice(wallet_a_addresses)
            
            # Create transaction data
            tx = {
                'txid': f'invoice_{i}',  # Placeholder; in reality, would be the actual txid
                'date': tx_date.isoformat(),
                'block_height': block_height,
                'usd_amount': round(usd_amount, 2),
                'btc_amount': float(btc_amount),
                'satoshis': satoshis,
                'to_address': recipient_address,
                'wallet': 'A',
                'type': 'invoice'
            }
            
            # Add to UTXO list for wallet A
            self.utxos['A'].append({
                'txid': tx['txid'],
                'vout': 0,
                'amount': satoshis,
                'address': recipient_address,
                'block_height': block_height
            })
            
            txs.append(tx)
            
            # Increment block height (could be variable to simulate real-world block times)
            block_height += random.randint(1, 6)
        
        # Sort transactions by date and adjust block heights accordingly
        txs.sort(key=lambda x: x['date'])
        for i, tx in enumerate(txs):
            tx['block_height'] = 100 + i  # Start at block 100 and increment
            # Update the corresponding UTXO block height
            for utxo in self.utxos['A']:
                if utxo['txid'] == tx['txid']:
                    utxo['block_height'] = tx['block_height']
        
        # Add transactions to the main list
        self.transactions.extend(txs)
        
        # Save invoicing transactions to file
        with open(os.path.join(self.data_dir, 'invoice_transactions.json'), 'w') as f:
            json.dump(txs, f, indent=2)
        
        print(f"Generated {len(txs)} invoice transactions")
    
    def generate_consolidation_transactions(self):
        """Generate bi-monthly consolidation transactions from Wallet A to Wallet B"""
        print("Generating consolidation transactions...")
        
        # Group UTXOs by 2-month periods
        consolidated_txs = []
        curr_block_height = max(utxo['block_height'] for utxo in self.utxos['A']) + 1
        
        # Get addresses from wallet B
        wallet_b_addresses = [addr['address'] for addr in self.wallets['B']['addresses']]
        
        # Organize UTXOs by date
        utxos_by_date = {}
        for tx in self.transactions:
            if tx['wallet'] == 'A':
                month = datetime.date.fromisoformat(tx['date']).month
                period = (month - 1) // 2  # 0 = Jan-Feb, 1 = Mar-Apr, etc.
                if period not in utxos_by_date:
                    utxos_by_date[period] = []
                utxos_by_date[period].append({
                    'txid': tx['txid'],
                    'vout': 0,
                    'amount': tx['satoshis'],
                    'address': tx['to_address']
                })
        
        # Create bi-monthly consolidation transactions
        for period, period_utxos in utxos_by_date.items():
            # Calculate consolidation date (end of bi-monthly period)
            month = period * 2 + 2  # 2 = Feb, 4 = Apr, etc.
            year = self.start_date.year
            last_day = 28 if month == 2 else (30 if month in [4, 6, 9, 11] else 31)
            consolidation_date = datetime.date(year, month, last_day)
            
            # How many consolidation transactions to make per period
            # Target is 100 total, so about 16-17 per bi-monthly period
            num_consolidations = 16 if period < 5 else 17
            
            # Split UTXOs into groups for each consolidation transaction
            utxo_chunks = np.array_split(period_utxos, num_consolidations)
            
            for i, chunk in enumerate(utxo_chunks):
                # Skip empty chunks
                if len(chunk) == 0:
                    continue
                
                # Calculate total amount in this consolidation
                total_satoshis = sum(utxo['amount'] for utxo in chunk)
                
                # Pick a random Treasury address
                treasury_address = random.choice(wallet_b_addresses)
                
                # Create consolidation transaction
                tx = {
                    'txid': f'consolidation_{period}_{i}',
                    'date': consolidation_date.isoformat(),
                    'block_height': curr_block_height,
                    'inputs': [{'txid': utxo['txid'], 'vout': utxo['vout']} for utxo in chunk],
                    'satoshis': total_satoshis,
                    'btc_amount': total_satoshis / COIN,
                    'to_address': treasury_address,
                    'wallet_from': 'A',
                    'wallet_to': 'B',
                    'type': 'consolidation'
                }
                
                # Add to transactions list
                consolidated_txs.append(tx)
                
                # Add to UTXO list for wallet B
                self.utxos['B'].append({
                    'txid': tx['txid'],
                    'vout': 0,
                    'amount': total_satoshis,
                    'address': treasury_address,
                    'block_height': curr_block_height
                })
                
                # Remove spent UTXOs from wallet A
                for spent_utxo in chunk:
                    self.utxos['A'] = [u for u in self.utxos['A'] if u['txid'] != spent_utxo['txid']]
                
                # Increment block height
                curr_block_height += random.randint(5, 15)
        
        # Add transactions to the main list
        self.transactions.extend(consolidated_txs)
        
        # Save consolidation transactions to file
        with open(os.path.join(self.data_dir, 'consolidation_transactions.json'), 'w') as f:
            json.dump(consolidated_txs, f, indent=2)
        
        print(f"Generated {len(consolidated_txs)} consolidation transactions")
    
    def generate_checking_account_transactions(self):
        """Generate transactions for the checking account (Wallet C)"""
        print("Generating checking account transactions...")
        
        transactions = []
        curr_block_height = max(utxo['block_height'] for utxo in self.utxos['B']) + 1
        
        # 1. Transfer 1 BTC from treasury to checking in January
        checking_address = self.wallets['C']['addresses'][0]['address']
        one_btc_satoshis = COIN  # 1 BTC = 100,000,000 satoshis
        
        # Find a suitable UTXO from wallet B to spend
        treasury_utxo = None
        for utxo in self.utxos['B']:
            if utxo['amount'] >= one_btc_satoshis:
                treasury_utxo = utxo
                break
        
        if not treasury_utxo:
            # If no single UTXO is large enough, we would need to combine multiple UTXOs
            # For simplicity, we'll just create a fake one for demonstration purposes
            print("No single UTXO large enough for 1 BTC transfer; creating dummy UTXO")
            treasury_utxo = {
                'txid': 'dummy_large_treasury_utxo',
                'vout': 0,
                'amount': one_btc_satoshis * 2,  # 2 BTC
                'address': self.wallets['B']['addresses'][0]['address'],
                'block_height': curr_block_height - 10
            }
            self.utxos['B'].append(treasury_utxo)
        
        # Create transfer transaction
        transfer_date = datetime.date(self.start_date.year, 1, 15)  # January 15
        transfer_tx = {
            'txid': 'treasury_to_checking',
            'date': transfer_date.isoformat(),
            'block_height': curr_block_height,
            'inputs': [{'txid': treasury_utxo['txid'], 'vout': treasury_utxo['vout']}],
            'satoshis': one_btc_satoshis,
            'btc_amount': 1.0,
            'to_address': checking_address,
            'wallet_from': 'B',
            'wallet_to': 'C',
            'type': 'transfer'
        }
        
        # Add to transactions list
        transactions.append(transfer_tx)
        
        # Add to UTXOs for Wallet C
        self.utxos['C'].append({
            'txid': transfer_tx['txid'],
            'vout': 0,
            'amount': one_btc_satoshis,
            'address': checking_address,
            'block_height': curr_block_height
        })
        
        # Add change back to Wallet B (if applicable)
        change_amount = treasury_utxo['amount'] - one_btc_satoshis
        if change_amount > 0:
            self.utxos['B'].append({
                'txid': transfer_tx['txid'],
                'vout': 1,
                'amount': change_amount,
                'address': treasury_utxo['address'],
                'block_height': curr_block_height
            })
        
        # Remove spent UTXO from Wallet B
        self.utxos['B'] = [u for u in self.utxos['B'] if u['txid'] != treasury_utxo['txid']]
        
        # Increment block height
        curr_block_height += random.randint(5, 15)
        
        # 2. Generate 20 outgoing transactions from checking to vendors ($50-$5000 USD)
        for i in range(20):
            # Random date after the transfer date
            tx_date_ordinal = random.randint(
                transfer_date.toordinal() + 1, 
                self.end_date.toordinal()
            )
            tx_date = datetime.date.fromordinal(tx_date_ordinal)
            
            # Random USD amount between $50-$5000
            usd_amount = random.uniform(50, 5000)
            
            # Convert to BTC
            btc_amount = self.usd_to_btc(usd_amount, tx_date)
            satoshis = self.btc_to_satoshis(btc_amount)
            
            # Create a random vendor address (external to our wallets)
            vendor_address = f"vendor_{i}"
            
            # Create vendor payment transaction
            vendor_tx = {
                'txid': f'vendor_payment_{i}',
                'date': tx_date.isoformat(),
                'block_height': curr_block_height,
                'inputs': [{'txid': self.utxos['C'][0]['txid'], 'vout': 0}], # Use the 1 BTC input
                'usd_amount': round(usd_amount, 2),
                'btc_amount': float(btc_amount),
                'satoshis': satoshis,
                'to_address': vendor_address,
                'wallet_from': 'C',
                'wallet_to': 'external',
                'type': 'vendor_payment'
            }
            
            # Add to transactions list
            transactions.append(vendor_tx)
            
            # Update the UTXO for wallet C (subtract the amount spent)
            self.utxos['C'][0]['amount'] -= satoshis
            
            # Add change UTXO back to wallet C
            change_tx = {
                'txid': vendor_tx['txid'],
                'vout': 1,
                'amount': self.utxos['C'][0]['amount'],
                'address': checking_address,
                'block_height': curr_block_height
            }
            
            # Replace the original UTXO with the change UTXO
            self.utxos['C'][0] = change_tx
            
            # Increment block height
            curr_block_height += random.randint(5, 15)
        
        # Add transactions to the main list
        self.transactions.extend(transactions)
        
        # Save checking transactions to file
        with open(os.path.join(self.data_dir, 'checking_transactions.json'), 'w') as f:
            json.dump(transactions, f, indent=2)
        
        print(f"Generated {len(transactions)} checking account transactions")
    
    def generate_special_treasury_transactions(self):
        """Generate special transactions in/out of the treasury wallet"""
        print("Generating special treasury transactions...")
        
        transactions = []
        curr_block_height = max(
            max(utxo['block_height'] for utxo in self.utxos['B']),
            max(utxo['block_height'] for utxo in self.utxos['C'])
        ) + 1
        
        # 1. 5 outgoing transactions from treasury (50K-300K USD)
        # Distribute evenly through the year
        for i in range(5):
            # Set date spread across the year
            month = i * 2 + 2  # Feb, Apr, Jun, Aug, Oct
            day = random.randint(1, 28)
            tx_date = datetime.date(self.start_date.year, month, day)
            
            # Random USD amount between $50K-$300K
            usd_amount = random.uniform(50000, 300000)
            
            # Convert to BTC
            btc_amount = self.usd_to_btc(usd_amount, tx_date)
            satoshis = self.btc_to_satoshis(btc_amount)
            
            # Create a random external address
            external_address = f"external_recipient_{i}"
            
            # Find sufficient UTXOs from treasury to spend
            utxos_to_spend = []
            total_input = 0
            
            for utxo in sorted(self.utxos['B'], key=lambda u: u['amount'], reverse=True):
                utxos_to_spend.append(utxo)
                total_input += utxo['amount']
                if total_input >= satoshis:
                    break
            
            if total_input < satoshis:
                print(f"Warning: Not enough funds in treasury for {btc_amount} BTC outgoing transaction")
                continue
            
            # Create outgoing transaction
            outgoing_tx = {
                'txid': f'treasury_outgoing_{i}',
                'date': tx_date.isoformat(),
                'block_height': curr_block_height,
                'inputs': [{'txid': utxo['txid'], 'vout': utxo['vout']} for utxo in utxos_to_spend],
                'usd_amount': round(usd_amount, 2),
                'btc_amount': float(btc_amount),
                'satoshis': satoshis,
                'to_address': external_address,
                'wallet_from': 'B',
                'wallet_to': 'external',
                'type': 'treasury_outgoing'
            }
            
            # Add to transactions list
            transactions.append(outgoing_tx)
            
            # Remove spent UTXOs from wallet B
            for spent_utxo in utxos_to_spend:
                self.utxos['B'] = [u for u in self.utxos['B'] if u['txid'] != spent_utxo['txid']]
            
            # Add change back to treasury if any
            change_amount = total_input - satoshis
            if change_amount > 0:
                treasury_address = random.choice([addr['address'] for addr in self.wallets['B']['addresses']])
                self.utxos['B'].append({
                    'txid': outgoing_tx['txid'],
                    'vout': 1,
                    'amount': change_amount,
                    'address': treasury_address,
                    'block_height': curr_block_height
                })
            
            # Increment block height
            curr_block_height += random.randint(5, 15)
        
        # 2. 2 incoming transactions to treasury (100K & 200K USD)
        # One in Q1, one in Q3
        for i, (quarter, usd_amount) in enumerate([(1, 100000), (3, 200000)]):
            # Set date in the appropriate quarter
            month = quarter * 3 - 1  # Q1 = Feb, Q3 = Aug
            day = random.randint(1, 28)
            tx_date = datetime.date(self.start_date.year, month, day)
            
            # Convert to BTC
            btc_amount = self.usd_to_btc(usd_amount, tx_date)
            satoshis = self.btc_to_satoshis(btc_amount)
            
            # Pick a treasury address
            treasury_address = random.choice([addr['address'] for addr in self.wallets['B']['addresses']])
            
            # Create incoming transaction
            incoming_tx = {
                'txid': f'treasury_incoming_{i}',
                'date': tx_date.isoformat(),
                'block_height': curr_block_height,
                'inputs': [{'txid': f'external_source_{i}', 'vout': 0}],
                'usd_amount': round(usd_amount, 2),
                'btc_amount': float(btc_amount),
                'satoshis': satoshis,
                'to_address': treasury_address,
                'wallet_from': 'external',
                'wallet_to': 'B',
                'type': 'treasury_incoming'
            }
            
            # Add to transactions list
            transactions.append(incoming_tx)
            
            # Add to UTXOs for wallet B
            self.utxos['B'].append({
                'txid': incoming_tx['txid'],
                'vout': 0,
                'amount': satoshis,
                'address': treasury_address,
                'block_height': curr_block_height
            })
            
            # Increment block height
            curr_block_height += random.randint(5, 15)
        
        # Add transactions to the main list
        self.transactions.extend(transactions)
        
        # Save special treasury transactions to file
        with open(os.path.join(self.data_dir, 'special_treasury_transactions.json'), 'w') as f:
            json.dump(transactions, f, indent=2)
        
        print(f"Generated {len(transactions)} special treasury transactions")
    
    def save_all_transactions(self):
        """Save all transactions to a single file"""
        # Sort all transactions by block height
        self.transactions.sort(key=lambda x: x['block_height'])
        
        # Save to file
        with open(os.path.join(self.data_dir, 'all_transactions.json'), 'w') as f:
            json.dump(self.transactions, f, indent=2)
        
        # Generate summary statistics
        summary = {
            'total_transactions': len(self.transactions),
            'transaction_types': {},
            'wallets': {}
        }
        
        for tx in self.transactions:
            tx_type = tx.get('type', 'unknown')
            if tx_type not in summary['transaction_types']:
                summary['transaction_types'][tx_type] = 0
            summary['transaction_types'][tx_type] += 1
            
            # Count by wallet
            wallet_from = tx.get('wallet_from', tx.get('wallet', 'unknown'))
            if wallet_from not in summary['wallets']:
                summary['wallets'][wallet_from] = {'incoming': 0, 'outgoing': 0}
            summary['wallets'][wallet_from]['outgoing'] += 1
            
            wallet_to = tx.get('wallet_to', 'unknown')
            if wallet_to not in summary['wallets']:
                summary['wallets'][wallet_to] = {'incoming': 0, 'outgoing': 0}
            summary['wallets'][wallet_to]['incoming'] += 1
        
        # Save summary
        with open(os.path.join(self.data_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Saved {len(self.transactions)} transactions to all_transactions.json")
        print("Transaction generation complete!")

def main():
    """Main function to run the transaction generator"""
    print("Bitcoin Transaction Generator for Test Data")
    print("-------------------------------------------")
    
    # Create the wallet simulator
    simulator = WalletSimulator()
    
    # Generate wallets
    simulator.generate_wallets()
    
    # Generate transactions
    simulator.generate_invoice_transactions()
    simulator.generate_consolidation_transactions()
    simulator.generate_checking_account_transactions()
    simulator.generate_special_treasury_transactions()
    
    # Save all transactions
    simulator.save_all_transactions()
    
    print("\nAll done! Transaction data saved to the 'data' directory.")

if __name__ == "__main__":
    main() 