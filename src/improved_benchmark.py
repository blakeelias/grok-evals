"""Wrapper for revised protocols to standardize output reporting."""
from typing import Dict, Any

def describe_protocol(name: str) -> str:
    if name == "RobustMC":
        return (
            "RobustMC: MCQ accuracy averaged across K option permutations, "
            "with per-position accuracy, variance, and worst-case reported."
        )
    if name == "GSM8K-Format-Strict":
        return (
            "GSM8K-Format-Strict: require outputs to end with 'Final Answer: <int>'; "
            "answers failing schema are marked incorrect; report accuracy & reject rate."
        )
    if name == "GSM8K-SelfConsistency":
        return (
            "GSM8K-SelfConsistency: n-sample majority vote over parsed final answers; "
            "report accuracy vs n and marginal cost."
        )
    return name
