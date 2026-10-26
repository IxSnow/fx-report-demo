"""Cliente de la API pública Frankfurter (tipos de cambio del BCE, sin key)."""
from __future__ import annotations

from datetime import date, timedelta

import requests

from . import __user_agent__

BASE_URL = "https://api.frankfurter.dev/v1"


class FxApiError(RuntimeError):
    """Error al consultar la API de tipos de cambio."""


def _get(path: str, params: dict) -> dict:
    try:
        resp = requests.get(
            f"{BASE_URL}/{path}",
            params=params,
            headers={"User-Agent": __user_agent__},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise FxApiError(f"fallo de red al consultar la API: {exc}") from exc
    except ValueError as exc:
        raise FxApiError("la API no devolvió JSON válido") from exc
    if "rates" not in data:
        raise FxApiError(f"respuesta inesperada de la API: {data}")
    return data


def supported_currencies() -> dict[str, str]:
    try:
        resp = requests.get(
            f"{BASE_URL}/currencies",
            headers={"User-Agent": __user_agent__},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise FxApiError(f"no se pudo obtener la lista de divisas: {exc}") from exc


def fetch_timeseries(
    base: str, symbols: list[str], days: int, today: date | None = None
) -> dict[str, dict[str, float]]:
    """Serie diaria de los últimos `days` días. Devuelve {fecha: {símbolo: valor}}."""
    today = today or date.today()
    start = today - timedelta(days=days)
    data = _get(
        f"{start.isoformat()}..{today.isoformat()}",
        {"base": base, "symbols": ",".join(symbols)},
    )
    return data["rates"]
