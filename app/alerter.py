import os
import httpx
from datetime import datetime

SLACK_WEBHOOK    = os.getenv("SLACK_WEBHOOK_URL", "")
CUSTOM_WEBHOOK   = os.getenv("ALERT_WEBHOOK_URL", "")

SEVERITY_COLORS  = {
    "high":   "danger",
    "medium": "warning",
    "low":    "good",
}

SEVERITY_EMOJI   = {
    "high":   "🔴",
    "medium": "🟡",
    "low":    "🟢",
}


async def fire_alert(
    sensor_id:    str,
    metric_name:  str,
    value:        float,
    z_score:      float,
    anomaly_score: float,
    severity:     str,
    mean:         float,
    std:          float,
):
    emoji     = SEVERITY_EMOJI.get(severity, "⚠️")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # ── Slack notification ───────────────────────────────────────────────────
    if SLACK_WEBHOOK and SLACK_WEBHOOK.startswith("https://hooks.slack.com"):
        slack_payload = {
            "text": f"{emoji} *Anomaly detected on `{sensor_id}`*",
            "attachments": [
                {
                    "color": SEVERITY_COLORS.get(severity, "warning"),
                    "fields": [
                        {"title": "Sensor",        "value": sensor_id,              "short": True},
                        {"title": "Metric",        "value": metric_name,            "short": True},
                        {"title": "Value",         "value": f"{value:.2f}",         "short": True},
                        {"title": "Severity",      "value": severity.upper(),       "short": True},
                        {"title": "Z-score",       "value": f"{z_score:.2f}σ",      "short": True},
                        {"title": "Normal range",  "value": f"{mean:.1f} ± {std:.1f}", "short": True},
                    ],
                    "footer": f"Anomaly Detector • {timestamp}",
                }
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(SLACK_WEBHOOK, json=slack_payload)
        except Exception as e:
            print(f"[alerter] Slack webhook failed: {e}")

    # ── Generic webhook (e.g. custom dashboard, PagerDuty, etc.) ────────────
    if CUSTOM_WEBHOOK:
        generic_payload = {
            "sensor_id":    sensor_id,
            "metric_name":  metric_name,
            "value":        value,
            "z_score":      z_score,
            "anomaly_score": anomaly_score,
            "severity":     severity,
            "mean":         mean,
            "std":          std,
            "timestamp":    timestamp,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(CUSTOM_WEBHOOK, json=generic_payload)
        except Exception as e:
            print(f"[alerter] Custom webhook failed: {e}")
