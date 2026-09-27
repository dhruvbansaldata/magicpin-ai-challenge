"""
Vera Bot Module — magicpin AI Challenge Submission
Supports both:
1. Direct Python import: `from bot import compose` (challenge-brief.md §7.1)
2. ASGI HTTP Server: `uvicorn bot:app --host 0.0.0.0 --port 8080` (challenge-testing-brief.md §8)
"""

from typing import Optional
from precision_composer import compose_precision_action
from server import app

__all__ = ["compose", "app"]


def compose(
    category: dict,
    merchant: dict,
    trigger: dict,
    customer: Optional[dict] = None,
) -> dict:
    """
    Deterministic context-aware composition entry point (challenge-brief.md §7.1).

    Inputs:
        category: dict loaded from dataset/categories_seed.json or pushed via /v1/context
        merchant: dict loaded from dataset/merchants_seed.json or pushed via /v1/context
        trigger:  dict loaded from dataset/triggers_seed.json or pushed via /v1/context
        customer: optional dict loaded from dataset/customers_seed.json or pushed via /v1/context

    Returns:
        dict with keys:
            body, cta, send_as, template_name, template_params, suppression_key, rationale
    """
    result = compose_precision_action(
        category=category or {},
        merchant=merchant or {},
        trigger=trigger or {},
        customer=customer,
    )
    return {
        "body": result.get("body", ""),
        "cta": result.get("cta", "binary_choice"),
        "send_as": result.get("send_as", "vera"),
        "template_name": result.get("template_name", "vera_precision_v1"),
        "template_params": result.get("template_params", []),
        "suppression_key": result.get("suppression_key", (trigger or {}).get("suppression_key", "")),
        "rationale": result.get("rationale", ""),
    }
