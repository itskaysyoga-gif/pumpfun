# Assumptions register

Every on-chain value or external dependency the code relies on. Re-verify before
Phase 4 results are trusted and again before Phase 7.

| Item | Value | Source | Verified |
| --- | --- | --- | --- |
| Pump bonding-curve program | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | `docs/idl/pump.json`, [pump-public-docs @ 639b87f](https://github.com/pump-fun/pump-public-docs) | 2026-10-20 |
| PumpSwap AMM program | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | `idl/pump_amm.json`, same commit | 2026-10-20 |
| Pump Fees program | `pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ` | `idl/pump_fees.json`, same commit | 2026-10-20 |
| Fee model | Dynamic tiers by market cap (since 2025-09-01), read from on-chain `FeeConfig` | pump-public-docs README, fee program section | 2026-10-20 |
| Fees in our data | Taken per trade from `TradeEvent.fee` + `creator_fee` (+ `buyback_fee`, `holder_rewards`), never a flat % | IDL `TradeEvent` fields | 2026-10-20 |
| Event discriminators | TradeEvent `bddb 7fd3 4ee6 61ee`; CreateEvent `1b72 a94d deeb 6376`; CompleteEvent `5f72 619c d42e 9808` | IDL `events` | 2026-10-20 |
| Event layout changes | Fields are appended over time; decoder tolerates shorter (older) events | IDL + `tests/test_decode.py` | 2026-10-20 |
| Quote mints | Coins can now be paired with SOL, USDC or another pump coin (depth 2 since 2026-10-13). Research uses SOL-quoted coins only | pump-public-docs README | 2026-10-20 |
| Graduation | Curve completes when `real_token_reserves` hits 0; new "synthetic migration" lets the crossing buy overfill at pool price | `docs/SYNTHETIC_MIGRATION.md` | 2026-10-20 |
| Cashback | Deprecated for new coins; "holder rewards coins" added | README | 2026-10-20 |
| Data path | Solana `logsSubscribe` (mentions pump program), decode `Program data:` lines | Design choice | **UNVERIFIED: probe on VM** |
| Event emission via logs | Expected `Program data:` lines; program also has `event_authority` (self-CPI). Decoder accepts both forms | IDL accounts | **UNVERIFIED: probe on VM** |
| PumpPortal data API | `subscribeNewToken`/`subscribeMigration` free; per-token/account trade streams metered at 0.01 SOL per 10k events, need API key + funded wallet. **Rejected as main feed on cost** | [pumpportal.fun/data-api/real-time](https://pumpportal.fun/data-api/real-time) | 2026-10-20 |
| Helius free tier | $0, 1M credits/month, 10 RPS, standard WSS only | [helius.dev/pricing](https://helius.dev/pricing) | 2026-10-20 |

## Open questions
- Probe result: events in logs, volume (tx/s, GB/day), public-RPC stability.
- Whether free RPC tiers can sustain full-volume streaming for 14+ days.
