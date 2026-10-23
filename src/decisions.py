"""Illustrative risk tiers and transparent alert evaluation."""
import math

import numpy as np
import pandas as pd

from src.config import TIERS


def risk(value: float) -> str:
    """Assign inclusive lower-bound tiers; unknown or negative values are unavailable."""
    if not math.isfinite(value) or value < 0:
        return "Unavailable"
    return next(label for bound, label, _ in TIERS if value < bound)


def action(tier: str) -> str:
    """Give operational planning suggestions; official AQHI guides health advice."""
    return {"Good": "Maintain routine monitoring and check official AQHI.",
            "Moderate": "Prepare sensitive-group communications; review official AQHI.",
            "High": "Review an advisory with public health; prepare respiratory capacity.",
            "Very High": "Escalate public-health review and outdoor-activity contingency plans.",
            "Unavailable": "Check official ECCC AQHI; model guidance is unavailable."}[tier]


def confusion(actual: pd.Series, predicted: pd.Series, threshold: float) -> dict:
    """Alert metrics; undefined ratios remain NaN, never misleading zeroes."""
    a, p = np.asarray(actual) >= threshold, np.asarray(predicted) >= threshold
    tp, tn = int((a & p).sum()), int((~a & ~p).sum())
    fp, fn = int((~a & p).sum()), int((a & ~p).sum())
    def divide(n: int, d: int) -> float:
        """Return missing when the denominator has no support."""
        return n / d if d else float("nan")
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "Precision": divide(tp, tp + fp), "Recall": divide(tp, tp + fn),
            "False-alarm rate (FPR)": divide(fp, fp + tn),
            "Missed-event rate": divide(fn, fn + tp)}


def matrix() -> pd.DataFrame:
    """Map risk signals to accountable planning decisions and measurable outcomes."""
    rows = [
        ("Moderate", "Public health", "Prepare multilingual sensitive-group messages", "Message reach"),
        ("High", "Hospitals", "Review respiratory staffing and surge plans", "ER waiting time"),
        ("High", "Schools / daycares", "Plan indoor alternatives using official AQHI", "Exposure hours avoided"),
        ("High", "Outdoor employers", "Review breaks and rescheduling options", "Worker exposure hours"),
        ("Very High", "City operations", "Coordinate transit messaging and anti-idling", "Idling minutes"),
        ("Moderate", "Pharmacies", "Review inhaler stock with clinical leadership", "Stock-out rate"),
    ]
    lower = {TIERS[i + 1][1]: bound for i, (bound, _, _) in enumerate(TIERS[:-1])}
    return pd.DataFrame([{"Risk Tier": tier, "Trigger": f"Predicted ≥{lower[tier]} ppb; review heat, calm wind and sunlight",
                          "Action": act, "Decision-Maker": owner, "Success Metric": metric}
                         for tier, owner, act, metric in rows])
