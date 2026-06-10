# Pharos RWA Risk Diligence Skill

Reusable skill for producing a structured risk memo for a tokenized asset or contract on Pharos.

The skill is designed for two use cases:

- Phase 1: standalone RWA and contract risk diligence skill.
- Phase 2: shared risk engine used by a treasury guardrail agent before it approves spending.

## Core Primitives

- `collect_contract_signals`: collect S1-S7 contract signals from an injected provider.
- `match_red_flags`: map contract signals to a structured red-flag list.
- `generate_due_diligence_memo`: produce a reusable diligence memo.
- `summarize_risk_level`: calculate deterministic LOW/MEDIUM/HIGH/CRITICAL risk level.
- `verdict`: map memo risk into allow/warn/block for a treasury guardrail shell.

## Reference — Code Legend

The memo uses stable codes so outputs can be cross-referenced. The codes are handles only: at runtime every red flag carries plain-language `evidence` and `explanation`, and every diligence check carries a `note`. The tables below are the legend (the same legend appears in `SKILL.md`).

Signals (S1-S7):

| Code | Signal | What it checks |
| --- | --- | --- |
| S1 | Existence / type | Whether contract bytecode exists at the address (an EOA has none). |
| S2 | Proxy / upgradeability | Whether the contract is an upgradeable proxy and which admin slot controls it. |
| S3 | Ownership / admin | Owner and admin roles, and whether they are an EOA, multisig, or timelock. |
| S4 | Privileged functions | Presence of powers such as mint, pause, blacklist, forceTransfer, setFee. |
| S5 | Token economics | Supply, mint cap presence, and fee bounds. |
| S6 | Timelock | Whether a timelock guards upgrade or owner actions, and its delay. |
| S7 | Source verification | Whether contract source is verified (via the optional explorer adapter). |

Red flags (RF-01 to RF-10):

| Code | Severity | Meaning |
| --- | --- | --- |
| RF-01 | CRITICAL | Upgradeable proxy controlled by a single EOA with no multisig or timelock. |
| RF-02 | CRITICAL | Mint function present with no supply cap. |
| RF-03 | HIGH | Blacklist and forceTransfer powers held by an EOA. |
| RF-04 | HIGH | Upgradeable path with no timelock. |
| RF-05 | HIGH | Adjustable fee with no enforceable upper bound. |
| RF-06 | HIGH | Transfers require allowlisted senders with no known public allowlist process. |
| RF-07 | MEDIUM | Admin roles exist but standard owner discovery is unavailable. |
| RF-08 | MEDIUM | Proxy admin is the same address as the deployer. |
| RF-09 | MEDIUM | Withdraw or sweep can move assets to an EOA-controlled operator. |
| RF-10 | INFO | Source verification unavailable, which lowers assessment confidence. |

Diligence checklist (DD-1 to DD-8):

| Code | Check |
| --- | --- |
| DD-1 | Issuer identity — off-chain; verify from legal and disclosure documents. |
| DD-2 | Upgrade governance — acceptable only under multisig and timelock. |
| DD-3 | Minting — requires a cap and clear governance. |
| DD-4 | Compliance powers (pause / blacklist / forceTransfer) — normal for RWA, but holder type matters. |
| DD-5 | Adjustable fees — must have an enforceable upper bound. |
| DD-6 | Source verification — via the optional explorer adapter. |
| DD-7 | Oracle or valuation dependencies — not proven on-chain by this skill. |
| DD-8 | Off-chain backing, custody, and redemption — cannot be proven on-chain. |

## Safety Scope

This is a diligence aid, not a full audit. The first version uses provider adapters so live chain access can stay narrow and explicit.

Scanner-sensitive rules:

- no shell execution
- no hidden filesystem writes
- no broad network access
- no secrets in fixtures, logs, or examples
- live RPC access should be added through a small provider adapter only

Pharos testnet parameters:

- Chain ID: `688688`
- Native token: `PHRS`
- Explorer: <https://testnet.pharosscan.xyz>
- Faucet/dashboard: <https://testnet.pharosnetwork.xyz>
- Live RPC remains injectable; the default demo uses fixtures and no network.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
rwa-risk-diligence
```

Without installing:

```bash
PYTHONPATH=src python3 -m rwa_risk_diligence.cli
```

## Output Schema

The memo is JSON and follows this shape:

```json
{
  "address": "0x...",
  "chain_id": "688688",
  "block": "123456",
  "asset_type": "ERC20",
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0.7,
  "signals": {},
  "centralization_powers": [],
  "red_flags": [],
  "dd_checklist": [],
  "unknowns": [],
  "data_sources": ["fixture", "rpc:pharos-testnet"]
}
```

The demo fixture produces visibly different memos:

- clean multisig plus timelock RWA token: LOW
- upgradeable EOA-admin token: CRITICAL

The important RWA nuance: pause, blacklist, and force-transfer powers are not automatically bugs. For compliant RWA tokens they can be expected. The risk depends on who holds those powers and whether they are guarded by multisig and timelock.

## Integration Plan

The package is intentionally small:

- `RiskDiligenceSkill` contains the primitive API.
- `RiskSignalProvider` is the boundary for Pharos RPC or explorer data.
- `FixtureRiskSignalProvider` powers tests and video demos without live network access.

After Pharos package requirements are confirmed, add a thin wrapper around this core rather than changing the core contracts.
