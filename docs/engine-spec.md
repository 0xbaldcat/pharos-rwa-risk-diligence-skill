# Risk Engine Specification

## Constraints

- Read-only by default.
- Fixture demo runs without network access.
- Live chain access must go through an injected EVM JSON-RPC provider.
- Explorer or indexer data must go through an optional adapter that is disabled by default.
- No shell execution, hidden file writes, telemetry, or dynamic code evaluation.
- Same address plus same block should produce the same memo.

## Signals

- S1 existence and address type.
- S2 proxy and upgradeability status.
- S3 owner, admin, and holder classification.
- S4 privileged function presence.
- S5 token economics and optional holder concentration.
- S6 timelock on privileged actions.
- S7 source verification from an optional explorer adapter.

## Red Flags

- RF-01 CRITICAL: upgradeable proxy controlled by a single EOA without multisig or timelock.
- RF-02 CRITICAL: mint capability without a detected supply cap.
- RF-03 HIGH: blacklist and force-transfer powers both held by an EOA.
- RF-04 HIGH: upgrade path has no detected timelock.
- RF-05 HIGH: fee control has no hard upper bound.
- RF-06 HIGH: transfer allowlist requirement without a public allowlist process.
- RF-07 MEDIUM: non-standard or hidden ownership.
- RF-08 MEDIUM: proxy admin matches deployer EOA.
- RF-09 MEDIUM: withdraw or sweep capability can pull assets to an EOA.
- RF-10 INFO: source is unverified or source verification is unavailable.

RWA framing: pause, blacklist, and force-transfer powers can be normal for compliant permissioned assets. The memo scores the holder and guardrails around those powers, not just their existence.

## Memo Shape

The memo includes address, chain ID, block, asset type, risk level, confidence, raw signals, centralization powers, red flags, diligence checklist, unknowns, and data sources.
