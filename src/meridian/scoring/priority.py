import math


def compute(relevance: float, urgency: float, effort: float) -> float:
    if effort <= 0:
        raise ValueError("effort must be > 0")
    return relevance * urgency / effort


def decay(urgency0: float, lam: float, age_days: float) -> float:
    return urgency0 * math.exp(-lam * age_days)
