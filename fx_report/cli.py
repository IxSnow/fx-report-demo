"""CLI del pipeline fx-report."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .client import FxApiError, fetch_timeseries
from .notify import build_alert, send_alert
from .report import compute_stats, to_csv, to_markdown

DEFAULTS = {
    "base": "USD",
    "symbols": ["EUR", "BRL", "MXN", "GBP", "JPY"],
    "days": 14,
    "alert_threshold_pct": 1.0,
    "out_dir": "output",
}


def _load_config(path: str | None) -> dict:
    cfg = dict(DEFAULTS)
    if not path:
        return cfg
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"No existe el archivo de configuración: {path}")
    try:
        import yaml  # type: ignore

        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except ImportError:
        import json

        raw = json.loads(p.read_text(encoding="utf-8"))
    cfg.update({k: v for k, v in raw.items() if k in DEFAULTS})
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fx-report",
        description="Reporte de tipos de cambio (API pública) en Markdown + CSV, con alerta opcional.",
    )
    parser.add_argument("-c", "--config", help="archivo YAML/JSON de configuración")
    parser.add_argument("--no-notify", action="store_true", help="no enviar alertas")
    parser.add_argument("--version", action="version", version=f"fx-report {__version__}")
    args = parser.parse_args(argv)

    cfg = _load_config(args.config)
    base = cfg["base"]
    symbols = cfg["symbols"]
    out_dir = Path(cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"fx-report {__version__}: consultando {base} → {', '.join(symbols)} "
          f"({cfg['days']} días)...")
    try:
        rates = fetch_timeseries(base, symbols, cfg["days"])
    except FxApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    stats = compute_stats(rates, symbols)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    md = to_markdown(base, rates, stats, generated_at)
    csv_text = to_csv(rates, symbols)
    md_path = out_dir / "reporte_tipos_de_cambio.md"
    csv_path = out_dir / "serie_tipos_de_cambio.csv"
    md_path.write_text(md, encoding="utf-8")
    csv_path.write_text(csv_text, encoding="utf-8")

    print(f"  Reporte Markdown: {md_path}")
    print(f"  Serie CSV:        {csv_path}")
    print("\n" + md)

    alert = build_alert(stats, cfg["alert_threshold_pct"])
    if args.no_notify:
        return 0
    print("--- Alertas ---")
    if alert is None:
        print(f"  Sin movimientos sobre {cfg['alert_threshold_pct']:.2f}% en el último día.")
    else:
        for line in send_alert("fx-report: movimiento de divisas", alert):
            print(f"  {line}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
