---
name: pharos-rwa-risk-diligence-skill
description: Reviews a Pharos RWA token or contract before allowlisting, accepting collateral, routing treasury activity, or producing a structured risk memo.
version: 1.0.0
---

# Pharos RWA Risk Diligence Skill

## What It Does
This skill produces a deterministic risk memo for a Pharos tokenized asset or contract. It turns contract signals into red flags, diligence checks, a risk level, confidence score, and an allow/warn/block verdict.

It is designed for RWA and contract review workflows where compliance powers must be interpreted in context rather than treated as automatic failures.

## When To Use / Triggers
- A request asks whether a Pharos RWA token or contract is safe enough to trust.
- A workflow needs a structured diligence memo for a tokenized asset.
- A treasury or policy layer needs a destination risk verdict before approving activity.
- A reviewer needs to distinguish compliant RWA controls from unsafe centralized control.

## Required Inputs
- `chain_id`: Pharos testnet is `688688`.
- `address`: contract or token address to review.
- Optional `block`: block tag or height. Use `latest` when not specified.
- Optional provider data: contract code, proxy/admin fields, owner type, privileged functions, source verification, mint/fee constraints, timelock, and holder concentration.

## Workflow
1. Collect contract signals S1-S7 through a read-only provider.
2. Classify ownership and admin control as EOA, multisig, timelock, or unknown.
3. Match the signal set against red flags RF-01 through RF-10.
4. Build diligence checks DD-1 through DD-8.
5. Compute `risk_level`, `confidence`, and `guardrail_verdict`.
6. Return the memo as JSON-friendly structured data.

RWA review rule: do not treat `pause`, `blacklist`, or `forceTransfer` as automatic failures. These controls can be normal for compliant RWA tokens. The key judgment is who holds the power and whether it is protected by multisig and timelock controls.

## Primitives / API
- `collect_contract_signals(chain_id: str, address: str, block: str = "latest") -> ContractSignalSet`: collects S1-S7 signals through the injected provider.
- `match_red_flags(signals: ContractSignalSet) -> list[RedFlag]`: maps contract signals to RF-01 through RF-10.
- `generate_due_diligence_memo(chain_id: str, address: str, block: str = "latest") -> RiskMemo`: returns the structured risk memo.
- `summarize_risk_level(flags: list[RedFlag]) -> str`: converts red flags into LOW, MEDIUM, HIGH, or CRITICAL.
- `verdict(memo: RiskMemo, block_level: str = "CRITICAL", warn_level: str = "HIGH") -> str`: maps risk into allow, warn, or block.

## Install & Run
Install locally:

```bash
pip install -e .
```

Run the local demo:

```bash
python3 examples/agent_demo.py
```

Run the CLI demo:

```bash
rwa-risk-diligence
```

## Output
Return a JSON object containing:
- contract identity and chain
- S1-S7 signals
- centralization powers
- red flags with severity and evidence
- DD-1 through DD-8 checklist
- unknowns and data sources
- `risk_level`
- `confidence`
- `guardrail_verdict`

## Security (CertiK-Clean)
- Read-only by default.
- Provider access is injectable.
- Default demos are offline and deterministic.
- No shell execution.
- No hidden file writes.
- No broad network access.
- Live chain access must be explicit through a narrow injected provider.

## Demo
- Agent-style scenario demo: `examples/agent_demo.py`.
- CLI demo and package details: `README.md`.
