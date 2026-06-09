from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.config import Settings


@dataclass
class AuditPlan:
    vulnerability: str
    severity: str
    reasoning: str
    patch_strategy: str
    test_strategy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vulnerability": self.vulnerability,
            "severity": self.severity,
            "reasoning": self.reasoning,
            "patch_strategy": self.patch_strategy,
            "test_strategy": self.test_strategy,
        }


class ZaiClient:
    """Z.AI / GLM-5.1 adapter with deterministic mock fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None
        if settings.llm_mode.lower() == "real" and settings.zai_api_key:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI(api_key=settings.zai_api_key, base_url=settings.zai_base_url)
            except Exception:
                self._client = None

    def plan_audit(self, contract_source: str) -> AuditPlan:
        if self._client is None:
            return self._mock_plan(contract_source)

        prompt = (
            "You are a senior Solidity security engineer. Analyze the contract and return strict JSON with keys: "
            "vulnerability, severity, reasoning, patch_strategy, test_strategy.\n\n"
            f"Contract:\n```solidity\n{contract_source}\n```"
        )
        try:
            completion = self._client.chat.completions.create(
                model=self.settings.zai_model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON. No markdown."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content or "{}"
            data = json.loads(content)
            return AuditPlan(
                vulnerability=str(data.get("vulnerability", "Unknown")),
                severity=str(data.get("severity", "Medium")),
                reasoning=str(data.get("reasoning", "")),
                patch_strategy=str(data.get("patch_strategy", "")),
                test_strategy=str(data.get("test_strategy", "")),
            )
        except Exception:
            return self._mock_plan(contract_source)

    @staticmethod
    def _mock_plan(contract_source: str) -> AuditPlan:
        has_external_call_before_update = "call{value: amount}" in contract_source and "balances[msg.sender] = 0" in contract_source
        if has_external_call_before_update:
            return AuditPlan(
                vulnerability="Reentrancy in withdraw(): ETH is sent before user balance is zeroed.",
                severity="High",
                reasoning="The contract performs an untrusted external call to msg.sender before updating internal accounting. A malicious receiver can re-enter withdraw() and drain funds.",
                patch_strategy="Apply checks-effects-interactions: set balance to zero before the call, and add a nonReentrant guard as defense in depth.",
                test_strategy="Run a reentrancy attacker test against the vulnerable version and verify the patched version only allows a single withdrawal.",
            )
        return AuditPlan(
            vulnerability="No deterministic issue found by mock scanner.",
            severity="Informational",
            reasoning="Mock mode only recognizes the reentrancy pattern used in the demo contract.",
            patch_strategy="Escalate to real GLM-5.1 mode for full audit coverage.",
            test_strategy="Run Foundry tests and add property checks around asset accounting.",
        )
