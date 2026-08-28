# tx-status-checker

A small command-line tool that answers the #1 support question for any EVM wallet: **"Where is my transaction?"**

Give it a transaction hash and a network, and it queries the network's public block explorer API and translates the raw response into a plain-language status: `pending`, `confirmed`, `failed`, or `not_found` — along with a short explanation of what happened and why.

This is a companion project to [`trust-wallet-transaction-troubleshooting`](../trust-wallet-transaction-troubleshooting), which documents the *diagnostic reasoning* behind common wallet support cases. This repo implements one of those diagnostic steps as working code.

## Why

Sections 1 and 2 of the troubleshooting guide ("Pending" and "Failed" transactions) describe manually checking a block explorer to determine transaction status. This script automates that first diagnostic step, so a support agent — or a user — can get an answer in one command instead of manually reading raw explorer output.

## Supported networks

- Ethereum (`eth`)
- BNB Smart Chain (`bsc`)
- Polygon (`polygon`)

## Usage

```bash
pip install requests

python tx_status.py 0xYOUR_TX_HASH --network eth --api-key YOUR_KEY
python tx_status.py 0xYOUR_TX_HASH --network bsc --api-key YOUR_KEY
python tx_status.py 0xYOUR_TX_HASH --network polygon --api-key YOUR_KEY
```

Example output:

```
Network:  Ethereum
Status:   failed
Block:    19824213
Details:  The transaction was mined but reverted during execution. Gas is
          typically still deducted from the sender even though the
          transaction failed. Common causes: insufficient gas limit,
          slippage on a swap, or a smart contract rejecting the call.
```

## API key

As of August 2025, Etherscan retired the old V1 API in favor of a unified V2 API covering 50+ EVM chains through a single key. Get a free key at [etherscan.io/apis](https://etherscan.io/apis) (sign up, then create an API key from your dashboard). The same key works for Ethereum, BNB Smart Chain, and Polygon — no separate BscScan/Polygonscan key needed.

Pass it directly:

```bash
python tx_status.py 0xYOUR_TX_HASH --network eth --api-key YOUR_KEY
```

or set it as an environment variable so you don't have to repeat it:

```bash
export EXPLORER_API_KEY=YOUR_KEY
python tx_status.py 0xYOUR_TX_HASH --network eth
```

A key is required — there is no working demo/shared key anymore.

## How it works

1. Calls `eth_getTransactionByHash` to check whether the transaction exists and whether it's been included in a block yet (`pending` if no block number).
2. If it's been mined, calls `gettxreceiptstatus` to check whether execution succeeded (`confirmed`) or reverted (`failed`).
3. Maps the result to a plain-language explanation matching the patterns described in the troubleshooting guide.

## Possible extensions

- Add more networks (Avalanche, Arbitrum, Optimism, etc.)
- Detect `network mismatch` automatically by checking the same hash across multiple networks
- Wrap this in a tiny web UI or Telegram bot for non-technical users
