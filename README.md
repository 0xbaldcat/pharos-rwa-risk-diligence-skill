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
