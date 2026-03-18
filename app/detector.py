import numpy as np
from sklearn.ensemble import IsolationForest
from dataclasses import dataclass

MIN_WINDOW = 20   # need at least this many points before running ML


@dataclass
class DetectionResult:
    is_anomaly:    bool
    anomaly_score: float
    z_score:       float
    severity:      str        # "none" | "low" | "medium" | "high"
    method:        str
    mean:          float
    std:           float


def detect(window: list[float], new_value: float) -> DetectionResult:
    """
    Run two complementary methods:
      1. Z-score  — fast, catches simple statistical outliers
      2. Isolation Forest — catches complex contextual anomalies

    An anomaly is flagged when EITHER method fires.
    Severity is determined by how many standard deviations out the value is.
    """
    if len(window) < MIN_WINDOW:
        return DetectionResult(
            is_anomaly=False,
            anomaly_score=0.0,
            z_score=0.0,
            severity="none",
            method="insufficient_data",
            mean=float(np.mean(window)) if window else new_value,
            std=0.0,
        )

    arr  = np.array(window, dtype=float)
    mean = float(np.mean(arr))
    std  = float(np.std(arr))

    # ── Z-score ──────────────────────────────────────────────────────────────
    z_score  = abs((new_value - mean) / std) if std > 0 else 0.0
    z_anomaly = z_score > 3.0

    # ── Isolation Forest ─────────────────────────────────────────────────────
    train_data = arr.reshape(-1, 1)
    model      = IsolationForest(contamination=0.05, random_state=42, n_estimators=50)
    model.fit(train_data)

    iso_score  = float(model.decision_function([[new_value]])[0])
    iso_label  = model.predict([[new_value]])[0]   # -1 = anomaly, 1 = normal
    iso_anomaly = iso_label == -1

    # ── Combine ───────────────────────────────────────────────────────────────
    is_anomaly    = z_anomaly or iso_anomaly
    anomaly_score = round(abs(iso_score), 4)

    # Severity thresholds (based on z-score)
    if not is_anomaly:
        severity = "none"
    elif z_score >= 5.0:
        severity = "high"
    elif z_score >= 4.0:
        severity = "medium"
    else:
        severity = "low"

    method = []
    if z_anomaly:
        method.append("zscore")
    if iso_anomaly:
        method.append("isolation_forest")
    method_str = "+".join(method) if method else "none"

    return DetectionResult(
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        z_score=round(z_score, 3),
        severity=severity,
        method=method_str,
        mean=round(mean, 3),
        std=round(std, 3),
    )
