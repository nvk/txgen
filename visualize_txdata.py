#!/usr/bin/env python3
"""
Transaction Visualization Tool - Using Actual Transaction Data

Creates visualizations based on the generated transaction data from txgen.py
"""

import os
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_transaction_data(data_dir='data'):
    """Load the generated transaction data"""
    with open(os.path.join(data_dir, 'all_transactions.json'), 'r') as f:
        transactions = json.load(f)
    print(f"Loaded {len(transactions)} transactions")
    
    # Load summary
    with open(os.path.join(data_dir, 'summary.json'), 'r') as f:
        summary = json.load(f)
    print(f"Transaction types: {summary['transaction_types']}")
    
    return transactions, summary

def create_sankey_diagram(transactions, output_file='visualizations/sankey_flow.html'):
    """Create a Sankey diagram showing the flow of funds between wallets"""
    # Extract source, target, and value from transactions
    wallet_map = {
        'A': 0,  # Invoice wallet
        'B': 1,  # Treasury wallet
        'C': 2,  # Checking wallet
        'external_in': 3,  # External sources (funds coming in)
        'external_out': 4,  # External destinations (funds going out)
        'unknown': 5   # Unknown sources (should be empty now)
    }
    
    # Map wallet names for visualization
    wallet_names = {
        'A': 'Invoicing Wallet',
        'B': 'Treasury Wallet',
        'C': 'Checking Wallet',
        'external_in': 'External Sources',
        'external_out': 'External Destinations',
        'unknown': 'Unknown'
    }
    
    # Count flows between wallets
    flows = {}
    for tx in transactions:
        # Get the transaction type
        tx_type = tx.get('type', '')
        
        # Properly extract source and target based on transaction type
        if tx_type == 'invoice':
            # For invoices, external_in -> A (invoicing wallet)
            source = 'external_in'
            target = 'A'
        elif tx_type == 'treasury_incoming':
            # For treasury incoming, typically A -> B
            source = 'A'
            target = 'B'
        elif tx_type == 'treasury_outgoing':
            # For treasury outgoing, typically B -> external_out or B -> C
            source = 'B'
            target_orig = tx.get('wallet_to', 'external_out')
            target = target_orig if target_orig != 'external' else 'external_out'
        elif tx_type == 'consolidation':
            # For consolidation, use the specified source and target
            source_orig = tx.get('wallet_from', tx.get('wallet', 'unknown'))
            source = source_orig if source_orig != 'external' else 'external_in'
            target_orig = tx.get('wallet_to', 'unknown')
            target = target_orig if target_orig != 'external' else 'external_out'
        elif tx_type == 'vendor_payment':
            # For vendor payments, typically from C to external_out
            source = tx.get('wallet_from', 'C')
            target = 'external_out'
        else:
            # For other transactions, use the specified source and target but map external
            source_orig = tx.get('wallet_from', tx.get('wallet', 'unknown'))
            source = source_orig if source_orig != 'external' else 'external_in'
            target_orig = tx.get('wallet_to', 'unknown')
            target = target_orig if target_orig != 'external' else 'external_out'
        
        # Get the amount
        amount = tx.get('btc_amount', tx.get('satoshis', 0) / 100000000)
        
        # Skip if source or target is unknown or not in our wallet map
        if source not in wallet_map or target not in wallet_map:
            continue
        
        flow_key = (source, target)
        if flow_key in flows:
            flows[flow_key] += amount
        else:
            flows[flow_key] = amount
    
    # Create source, target, and value arrays for Sankey
    sources = []
    targets = []
    values = []
    labels = []
    
    for (source, target), amount in flows.items():
        sources.append(wallet_map[source])
        targets.append(wallet_map[target])
        values.append(amount)
        labels.append(f"{wallet_names[source]} → {wallet_names[target]}: {amount:.8f} BTC")
    
    # Create nodes
    nodes = ['Invoicing Wallet', 'Treasury Wallet', 'Checking Wallet', 'External Sources', 'External Destinations']
    node_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            label=labels,
            color=['rgba(31, 119, 180, 0.4)'] * len(sources)  # Blue with transparency
        )
    )])
    
    fig.update_layout(
        title_text="Bitcoin Flow Between Wallets (Actual Data)",
        font_size=12
    )
    
    # Save to HTML file
    fig.write_html(output_file)
    print(f"Sankey diagram saved to {output_file}")
    return fig

def create_transaction_timeline(transactions, output_file='visualizations/transaction_timeline.html'):
    """Create a timeline visualization of transactions"""
    # Extract data for timeline
    df_data = []
    
    for tx in transactions:
        df_data.append({
            'date': tx.get('date', ''),
            'block_height': tx.get('block_height', 0),
            'type': tx.get('type', 'unknown'),
            'from': tx.get('wallet_from', tx.get('wallet', 'unknown')),
            'to': tx.get('wallet_to', 'unknown'),
            'amount_btc': tx.get('btc_amount', tx.get('satoshis', 0) / 100000000),
            'amount_usd': tx.get('usd_amount', 0)
        })
    
    df = pd.DataFrame(df_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create a timeline visualization
    fig = px.scatter(
        df, 
        x='date', 
        y='amount_btc',
        color='type',
        size='amount_btc',
        hover_data=['from', 'to', 'block_height', 'amount_usd'],
        title='Transaction Timeline (Actual Data)',
        labels={'amount_btc': 'Amount (BTC)', 'date': 'Date', 'type': 'Transaction Type'}
    )
    
    fig.update_layout(height=600)
    fig.write_html(output_file)
    
    print(f"Transaction timeline saved to {output_file}")
    return fig

def create_wallet_balance_waterfall(transactions, output_file='visualizations/wallet_balance_waterfall.html'):
    """Create a waterfall chart showing wallet balances over time"""
    # Sort transactions by date and block height
    sorted_txs = sorted(transactions, key=lambda x: (x.get('date', ''), x.get('block_height', 0)))
    
    # Track balances over time
    balances = {'A': [], 'B': [], 'C': []}
    dates = []
    block_heights = []
    current_balances = {'A': 0, 'B': 0, 'C': 0}
    
    for tx in sorted_txs:
        source = tx.get('wallet_from', tx.get('wallet', 'unknown'))
        target = tx.get('wallet_to', 'unknown')
        amount = tx.get('btc_amount', tx.get('satoshis', 0) / 100000000)
        date = tx.get('date', '')
        block_height = tx.get('block_height', 0)
        
        # Update balances based on transaction
        if source in current_balances:
            current_balances[source] -= amount
        
        if target in current_balances:
            current_balances[target] += amount
        
        # Save the state
        for wallet in current_balances:
            balances[wallet].append(current_balances[wallet])
        
        dates.append(date)
        block_heights.append(block_height)
    
    # Create DataFrame for plotting
    df_data = {
        'date': pd.to_datetime(dates),
        'block_height': block_heights
    }
    
    for wallet in balances:
        df_data[f'Wallet {wallet}'] = balances[wallet]
    
    df = pd.DataFrame(df_data)
    
    # Group by date and get the last balance for each day (to avoid duplicate dates issue)
    df = df.sort_values(['date', 'block_height'])
    
    # Create stacked area chart
    fig = px.area(
        df, 
        x='date', 
        y=[f'Wallet {w}' for w in balances.keys()],
        title='Wallet Balances Over Time (Actual Data)',
        labels={'value': 'Balance (BTC)', 'date': 'Date', 'variable': 'Wallet'}
    )
    
    fig.update_layout(height=600)
    fig.write_html(output_file)
    
    print(f"Wallet balance waterfall saved to {output_file}")
    
    # Also create a cumulative balance chart
    total_balance = []
    for i in range(len(dates)):
        total = sum(balances[wallet][i] for wallet in balances)
        total_balance.append(total)
    
    df_total = pd.DataFrame({
        'date': pd.to_datetime(dates),
        'block_height': block_heights,
        'total_balance': total_balance
    })
    
    df_total = df_total.sort_values(['date', 'block_height'])
    
    fig_total = px.line(
        df_total,
        x='date',
        y='total_balance',
        title='Total Bitcoin Balance Over Time (Actual Data)',
        labels={'total_balance': 'Total Balance (BTC)', 'date': 'Date'}
    )
    
    total_output_file = output_file.replace('wallet_balance_waterfall', 'total_balance')
    fig_total.write_html(total_output_file)
    print(f"Total balance chart saved to {total_output_file}")
    
    return fig

def create_transaction_network(transactions, output_file='visualizations/transaction_network.html'):
    """Create a network graph visualization of transactions"""
    import networkx as nx
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes for all wallets and external entities
    wallet_nodes = {'A': 'Invoicing', 'B': 'Treasury', 'C': 'Checking', 'external': 'External'}
    for wallet_id, name in wallet_nodes.items():
        G.add_node(wallet_id, label=name, size=30)
    
    # Add transaction edges
    for tx in transactions:
        source = tx.get('wallet_from', tx.get('wallet', 'unknown'))
        target = tx.get('wallet_to', 'unknown')
        tx_type = tx.get('type', 'unknown')
        amount = tx.get('btc_amount', tx.get('satoshis', 0) / 100000000)
        
        # Skip if source or target is unknown or not in our wallet nodes
        if source not in wallet_nodes or target not in wallet_nodes:
            continue
        
        # Add or update edge
        if G.has_edge(source, target):
            G[source][target]['weight'] += amount
            G[source][target]['count'] += 1
        else:
            G.add_edge(source, target, weight=amount, count=1, type=tx_type)
    
    # Convert to a format Plotly can use
    edge_x = []
    edge_y = []
    edge_text = []
    
    pos = {
        'A': (0, 1), 
        'B': (1, 0), 
        'C': (2, 1), 
        'external': (1, 2)
    }
    
    for edge in G.edges(data=True):
        source, target, data = edge
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        
        # Add curved edges
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        
        edge_text.append(f"{data['weight']:.8f} BTC ({data['count']} transactions)")
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_text = []
    
    # Calculate node sizes based on transaction volume
    node_sizes = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{wallet_nodes[node]} Wallet")
        
        # Calculate node size based on transaction volume
        total_in = sum(data['weight'] for u, v, data in G.in_edges(node, data=True) if u in wallet_nodes)
        total_out = sum(data['weight'] for u, v, data in G.out_edges(node, data=True) if v in wallet_nodes)
        node_sizes.append(30 + 10 * (total_in + total_out))  # Base size + volume-based increase
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[wallet_nodes[node] for node in G.nodes()],
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=node_sizes,
            color=[i for i in range(len(node_sizes))],  # Color by index
            colorbar=dict(
                thickness=15,
                title='Node Index'
            ),
            line_width=2
        )
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                  layout=go.Layout(
                      title='Transaction Network (Actual Data)',
                      showlegend=False,
                      hovermode='closest',
                      margin=dict(b=20, l=5, r=5, t=40),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                  ))
    
    fig.write_html(output_file)
    print(f"Transaction network visualization saved to {output_file}")
    return fig

def create_true_waterfall(transactions, output_file='visualizations/true_waterfall.html'):
    """Create a waterfall chart showing balance changes over time"""
    # Group transactions by month
    tx_by_month = {}
    
    for tx in transactions:
        date = tx.get('date', '')
        if not date:
            continue
        
        # Extract year and month
        year_month = date[:7]  # Gets "YYYY-MM" part
        
        if year_month not in tx_by_month:
            tx_by_month[year_month] = []
        
        tx_by_month[year_month].append(tx)
    
    # Calculate net change per month
    months = sorted(tx_by_month.keys())
    net_changes = []
    
    # Start with zero (conceptually the balance before transactions)
    total_balance = 0
    data = []
    
    # Add starting balance entry
    data.append({
        'month': 'Start',
        'change': 0,
        'balance': 0,
        'type': 'start'
    })
    
    # Calculate net changes for each month
    for month in months:
        txs = tx_by_month[month]
        
        # Calculate net inflows (external to our system) and outflows
        inflow = sum(tx.get('btc_amount', tx.get('satoshis', 0) / 100000000) 
                    for tx in txs 
                    if tx.get('wallet_from') == 'external')
        
        outflow = sum(tx.get('btc_amount', tx.get('satoshis', 0) / 100000000) 
                     for tx in txs 
                     if tx.get('wallet_to') == 'external')
        
        # Net change for the month
        net_change = inflow - outflow
        total_balance += net_change
        
        data.append({
            'month': month,
            'change': net_change,
            'balance': total_balance,
            'type': 'increase' if net_change >= 0 else 'decrease'
        })
    
    # Create a dataframe
    df = pd.DataFrame(data)
    
    # Set colors based on increase/decrease
    colors = ['blue' if x == 'start' else ('green' if x == 'increase' else 'red') 
             for x in df['type']]
    
    # Create the waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Bitcoin Balance", 
        orientation="v",
        measure=["absolute"] + ["relative"] * (len(df) - 1),
        x=df['month'],
        textposition="outside",
        text=[f"{val:.4f}" for val in df['change']],
        y=df['change'],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}}
    ))
    
    fig.update_layout(
        title="Bitcoin Balance Waterfall Chart (Actual Data)",
        yaxis_title="BTC",
        showlegend=False
    )
    
    fig.write_html(output_file)
    print(f"True waterfall chart saved to {output_file}")
    return fig

def main():
    """Main function to create all visualizations"""
    print("Bitcoin Transaction Visualization Tool")
    print("-------------------------------------")
    
    # Load transaction data
    transactions, summary = load_transaction_data()
    
    # Create directory for visualizations
    os.makedirs('visualizations', exist_ok=True)
    
    # Create various visualizations
    create_sankey_diagram(transactions)
    create_transaction_timeline(transactions)
    create_wallet_balance_waterfall(transactions)
    create_transaction_network(transactions)
    create_true_waterfall(transactions)
    
    print("\nAll visualizations have been created in the 'visualizations' directory.")

if __name__ == "__main__":
    main() 