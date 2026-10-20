"""On-chain constants. Every value here must also appear in docs/assumptions.md
with its source and the date it was verified."""

# Source: docs/idl/pump.json (pump-fun/pump-public-docs @ 639b87f, 2026-10-13)
PUMP_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
# Source: pump_amm.json, same commit
PUMPSWAP_PROGRAM_ID = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
# Source: pump_fees.json, same commit
PUMP_FEES_PROGRAM_ID = "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ"

# Wrapped SOL mint. Coins whose quote_mint is not this are paired with USDC or
# another pump coin and are excluded from Phase 1-4 research.
WSOL_MINT = "So11111111111111111111111111111111111111112"

# Anchor self-CPI event instructions are prefixed with this 8-byte tag.
ANCHOR_EVENT_IX_TAG = bytes.fromhex("e445a52e51cb9a1d")

LAMPORTS_PER_SOL = 1_000_000_000
