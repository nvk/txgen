# Bitcoin Transaction Generation Plan

## Overview
Create a Python script to generate Bitcoin regtest transactions that simulate real-world wallet behavior for testing accounting reconciliation.

## Wallets
1. **xpub A (Invoicing Wallet)**
   - 10,000 incoming transactions at different block heights over 12 months
   - USD values: $100-2,000 using historical rates

2. **xpub B (Treasury Wallet)**
   - 100 UTXOs from bi-monthly consolidations of xpub A's transactions
   - 5 outgoing transactions to random addresses (values: $50K-300K USD)
   - 2 incoming transactions from outside sources ($100K & $200K USD)

3. **xpub C (Checking Wallet)**
   - 1 transaction from treasury (1 BTC) in January
   - 20 outgoing transactions to vendors ($50-5,000 USD)

## Implementation Steps
1. Set up Bitcoin regtest environment
2. Generate xpriv/xpub key pairs for the three wallets
3. Create dummy BTC/USD rate data for the year
4. Generate transactions for xpub A (invoicing)
5. Create consolidation transactions to xpub B (treasury)
6. Create transactions from treasury to checking wallet
7. Generate vendor payments from checking wallet
8. Add the special transactions in/out of treasury
9. Export transaction data for analysis

## Technical Approach
- Use Bitcoin regtest for simulation
- Use python-bitcoinlib for transaction creation
- Generate JSON output with all transaction details
- Create proper dependencies between transactions
- Include block heights and timestamps 