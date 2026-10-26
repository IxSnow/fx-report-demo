"""Alerta opcional por webhook o ntfy, configurada por variables de entorno."""
from __future__ import annotations

import os

import requests

from .report import SymbolStats


def build_alert(stats: list[SymbolStats], threshold_pct: float) -> str | None:
    """Devuelve el texto de alerta si alguna divisa superó el umbral diario."""
    movers = [s for s in stats if abs(s.change_pct_last_day) >= threshold_pct]
    if not movers:
        return None
    lines = [f"Divisas que se movieron más de {threshold_pct:.2f}% en el último día:"]
    for s in movers:
        lines.append(f"- {s.symbol}: {s.change_pct_last_day:+.2f}% (ahora {s.last:,.4f})")
    return "\n".join(lines)


def send_alert(title: str, body: str) -> list[str]:
    """Envía por WEBHOOK_URL y/o ntfy si están configurados."""
    status: list[str] = []
    webhook = os.getenv("WEBHOOK_URL")
    if webhook:
        try:
            requests.post(webhook, json={"title": title, "message": body}, timeout=20).raise_for_status()
            status.append("webhook: enviado")
        except requests.RequestException as exc:
            status.append(f"webhook falló: {exc}")

    topic = os.getenv("NTFY_TOPIC")
    if topic:
        server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        try:
            requests.post(
                f"{server}/{topic}",
                data=body.encode("utf-8"),
                headers={"Title": title},
                timeout=20,
            ).raise_for_status()
            status.append("ntfy: enviado")
        except requests.RequestException as exc:
            status.append(f"ntfy falló: {exc}")

    if not webhook and not topic:
        status.append("alerta omitida (faltan WEBHOOK_URL o NTFY_TOPIC)")
    return status
