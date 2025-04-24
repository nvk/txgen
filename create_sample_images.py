#!/usr/bin/env python3
"""
Create sample visualization images for README
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# Create screenshots directory if it doesn't exist
os.makedirs('screenshots', exist_ok=True)

# Sample data
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
x = np.arange(len(months))
y1 = np.random.rand(len(months)) * 2  # Wallet A
y2 = np.cumsum(np.random.rand(len(months)) * 0.5)  # Wallet B
y3 = np.random.rand(len(months)) * 0.3  # Wallet C

# 1. Sankey Diagram (simplified as a bar chart showing flows)
plt.figure(figsize=(10, 6))
plt.bar(x, y1, label='Invoicing -> Treasury', color='#1f77b4')
plt.bar(x, y2, bottom=y1, label='Treasury -> Checking', color='#ff7f0e')
plt.bar(x, y3, bottom=y1+y2, label='Checking -> External', color='#2ca02c')
plt.xlabel('Month')
plt.ylabel('Bitcoin Flow')
plt.title('Sankey Flow Diagram Example')
plt.xticks(x, months)
plt.legend()
plt.tight_layout()
plt.savefig('screenshots/sankey_flow.png', dpi=300)
plt.close()

# 2. Transaction Timeline
plt.figure(figsize=(10, 6))
sizes = np.random.rand(50) * 50 + 10
plt.scatter(np.random.rand(50) * 12, np.random.rand(50) * 3, 
           s=sizes, alpha=0.6, c=np.random.rand(50), cmap='viridis')
plt.xlabel('Month')
plt.ylabel('BTC Amount')
plt.title('Transaction Timeline Example')
plt.colorbar(label='Transaction Type')
plt.tight_layout()
plt.savefig('screenshots/transaction_timeline.png', dpi=300)
plt.close()

# 3. Wallet Balance Waterfall
plt.figure(figsize=(10, 6))
plt.fill_between(x, y1, label='Wallet A', alpha=0.7, color='#1f77b4')
plt.fill_between(x, y2, label='Wallet B', alpha=0.7, color='#ff7f0e')
plt.fill_between(x, y3, label='Wallet C', alpha=0.7, color='#2ca02c')
plt.xlabel('Month')
plt.ylabel('Balance (BTC)')
plt.title('Wallet Balance Waterfall Example')
plt.xticks(x, months)
plt.legend()
plt.tight_layout()
plt.savefig('screenshots/wallet_balance_waterfall.png', dpi=300)
plt.close()

# 4. Total Balance Chart
plt.figure(figsize=(10, 6))
total_balance = y1 + y2 + y3
plt.plot(x, total_balance, 'o-', linewidth=2)
plt.xlabel('Month')
plt.ylabel('Total BTC Balance')
plt.title('Total Bitcoin Balance Over Time')
plt.xticks(x, months)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('screenshots/total_balance.png', dpi=300)
plt.close()

# 5. Transaction Network
plt.figure(figsize=(8, 6))
# Create a simple network diagram
pos = {
    'A': (0, 1),
    'B': (1, 0),
    'C': (2, 1),
    'E': (1, 2)
}
labels = {
    'A': 'Invoicing',
    'B': 'Treasury',
    'C': 'Checking',
    'E': 'External'
}
edges = [
    ('A', 'B', 3.5),
    ('B', 'C', 1.0),
    ('C', 'E', 0.7),
    ('B', 'E', 2.1)
]

# Draw nodes
for node, position in pos.items():
    plt.scatter(position[0], position[1], s=800, alpha=0.8)
    plt.text(position[0], position[1], labels[node], 
            horizontalalignment='center', verticalalignment='center')

# Draw edges
for edge in edges:
    plt.arrow(pos[edge[0]][0], pos[edge[0]][1], 
             pos[edge[1]][0] - pos[edge[0]][0], 
             pos[edge[1]][1] - pos[edge[0]][1],
             head_width=0.1, head_length=0.2, fc='black', ec='black',
             length_includes_head=True, alpha=0.6, linewidth=edge[2])

plt.title('Transaction Network Example')
plt.axis('off')
plt.tight_layout()
plt.savefig('screenshots/transaction_network.png', dpi=300)
plt.close()

# 6. True Waterfall Chart (showing incremental balance changes)
plt.figure(figsize=(10, 6))

# Create some example change data
initial_balance = 5.0
changes = np.random.uniform(-1, 2, len(months))
changes[0] = initial_balance  # First bar is the starting balance

# Calculate cumulative sums
cumulative = np.cumsum(changes)

# Create lists to store the bars
bottoms = np.zeros(len(changes))
bottoms[1:] = cumulative[:-1]  # Bottom of each bar is the previous cumulative value

# Colors based on whether change is positive or negative
colors = ['green' if x >= 0 else 'red' for x in changes]
colors[0] = 'blue'  # Make initial balance blue

# Create the bars
plt.bar(x, changes, bottom=bottoms, color=colors, alpha=0.7)

# Add a line showing cumulative balance
plt.plot(x, cumulative, 'o-', color='black', linewidth=2)

# Add labels and styling
labels = ['Starting Balance'] + [f'Change in {month}' for month in months[1:]]
plt.xticks(x, labels, rotation=45, ha='right')
plt.ylabel('Balance Change (BTC)')
plt.title('Bitcoin Balance Waterfall Chart')

# Annotate each bar with its value
for i, (change, cum) in enumerate(zip(changes, cumulative)):
    plt.annotate(f'{change:.2f}', xy=(i, bottoms[i] + max(0, change/2)),
                 xytext=(0, 5), textcoords='offset points',
                 ha='center', va='bottom')
    
    # Add cumulative value at each point
    plt.annotate(f'{cum:.2f}', xy=(i, cum),
                 xytext=(0, 10), textcoords='offset points',
                 ha='center', va='bottom', fontweight='bold')

plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('screenshots/true_waterfall.png', dpi=300)
plt.close()

print("Sample visualization images created in the screenshots directory") 