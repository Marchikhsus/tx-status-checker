#!/usr/bin/env python3
"""
tx_status.py — Human-readable transaction status checker for EVM chains.

Diagnoses the most common Trust Wallet support case: "my transaction is
stuck". Given a transaction hash and network, it queries a block explorer
API and reports back:

  - status: pending / confirmed / failed
  - block number (if mined)
  - a plain-language explanation of what that means for the user

Usage:
    python tx_status.py <txid> --network eth --api-key YOUR_KEY
    python tx_status.py <txid> --network bsc --api-key YOUR_KEY
    python tx_status.py <txid> --network polygon --api-key YOUR_KEY

As of August 2025, Etherscan retired the old V1 API (separate domains per
chain: api.etherscan.io/api, api.bscscan.com/api, etc.) in favor of a
single unified V2 API. One Etherscan API key now works across Ethereum,
BNB Smart Chain, Polygon, and 50+ other EVM chains — you just specify
which chain via a numeric `chainid`. A free key is required (the old
shared "YourApiKeyToken" demo key no longer works).

Get a free key at https://etherscan.io/apis — sign up, then create a new
API key from your account dashboard. Pass it via --api-key or the
EXPLORER_API_KEY environment variable.
"""

import argparse
import os
import sys
import requests

V2_BASE_URL = "https://api.etherscan.io/v2/api"

NETWORKS = {
    "eth": {"name": "Ethereum", "chainid": 1},
    "bsc": {"name": "BNB Smart Chain", "chainid": 56},
    "polygon": {"name": "Polygon", "chainid": 137},
}


def get_transaction_status(txid: str, network_key: str, api_key: str) -> dict:
    network = NETWORKS[network_key]
    chainid = network["chainid"]

    # Step 1: check if the transaction has a receipt (i.e. was mined) and
    # whether execution succeeded or reverted.
    receipt_resp = requests.get(
        V2_BASE_URL,
        params={
            "chainid": chainid,
            "module": "transaction",
            "action": "gettxreceiptstatus",
            "txhash": txid,
            "apikey": api_key,
        },
        timeout=10,
    ).json()

    # Step 2: pull full transaction details (block number, etc.)
    tx_resp = requests.get(
        V2_BASE_URL,
        params={
            "chainid": chainid,
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": txid,
            "apikey": api_key,
        },
        timeout=10,
    ).json()

    tx = tx_resp.get("result")

    # The API returns an error message as a plain string (not a dict) when
    # the request itself failed — e.g. bad/missing API key, rate limit hit.
    if isinstance(tx, str):
        return {
            "network": network["name"],
            "status": "error",
            "explanation": f"The explorer API returned an error: {tx}",
        }

    if tx is None:
        return {
            "network": network["name"],
            "status": "not_found",
            "explanation": (
                "The transaction was not found by the explorer. Either it was "
                "never broadcast to this network, the hash is incorrect, or it "
                "belongs to a different network than the one specified."
            ),
        }

    block_number_hex = tx.get("blockNumber")

    if block_number_hex is None:
        return {
            "network": network["name"],
            "status": "pending",
            "explanation": (
                "The transaction is known to the network but has not been "
                "included in a block yet. This usually means the gas price "
                "offered is too low for current network conditions, or the "
                "network is congested."
            ),
        }

    block_number = int(block_number_hex, 16)

    receipt_result = receipt_resp.get("result")
    receipt_status = receipt_result.get("status") if isinstance(receipt_result, dict) else None

    if receipt_status == "1":
        status = "confirmed"
        explanation = (
            "The transaction was successfully mined and executed without errors."
        )
    elif receipt_status == "0":
        status = "failed"
        explanation = (
            "The transaction was mined but reverted during execution. Gas is "
            "typically still deducted from the sender even though the "
            "transaction failed. Common causes: insufficient gas limit, "
            "slippage on a swap, or a smart contract rejecting the call."
        )
    else:
        status = "unknown"
        explanation = "Could not determine execution status from the explorer response."

    return {
        "network": network["name"],
        "status": status,
        "block_number": block_number,
        "explanation": explanation,
    }


def main():
    parser = argparse.ArgumentParser(description="Check an EVM transaction's status in plain language.")
    parser.add_argument("txid", help="Transaction hash (0x...)")
    parser.add_argument(
        "--network",
        choices=NETWORKS.keys(),
        default="eth",
        help="Which network to query (default: eth)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("EXPLORER_API_KEY"),
        help="Etherscan V2 API key (or set EXPLORER_API_KEY env var). Get one free at https://etherscan.io/apis",
    )
    args = parser.parse_args()

    if not args.api_key:
        print(
            "Error: an API key is required. Get a free one at https://etherscan.io/apis "
            "and pass it with --api-key, or set the EXPLORER_API_KEY environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = get_transaction_status(args.txid, args.network, args.api_key)
    except requests.RequestException as e:
        print(f"Network error while contacting the explorer: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Network:  {result['network']}")
    print(f"Status:   {result['status']}")
    if "block_number" in result:
        print(f"Block:    {result['block_number']}")
    print(f"Details:  {result['explanation']}")


if __name__ == "__main__":
    main()
