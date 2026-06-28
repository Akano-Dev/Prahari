"""Deterministic multilingual red-flag rule engine (reused from Prahari)."""
from .red_flags import MAX_WEIGHT, RULES, RULES_BY_ID, FiredFlag, RedFlag, rule_score, scan

__all__ = ["RULES", "RULES_BY_ID", "MAX_WEIGHT", "RedFlag", "FiredFlag", "scan", "rule_score"]
