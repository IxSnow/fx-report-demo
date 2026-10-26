"""Procesa la serie de tipos de cambio y genera estadísticas, CSV y Markdown."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO


@dataclass
class SymbolStats:
    symbol: str
    first: float
    last: float
    minimum: float
    maximum: float
    average: float
    change_pct_period: float      # variación % del período completo
    change_pct_last_day: float    # variación % del último día vs el anterior
    n_points: int


def _sorted_dates(rates: dict[str, dict[str, float]]) -> list[str]:
    return sorted(rates.keys())


def compute_stats(rates: dict[str, dict[str, float]], symbols: list[str]) -> list[SymbolStats]:
    dates = _sorted_dates(rates)
    stats: list[SymbolStats] = []
    for sym in symbols:
        series = [(d, rates[d][sym]) for d in dates if sym in rates[d]]
        if not series:
            continue
        values = [v for _, v in series]
        first, last = values[0], values[-1]
        change_period = (last - first) / first * 100 if first else 0.0
        if len(values) >= 2 and values[-2]:
            change_day = (values[-1] - values[-2]) / values[-2] * 100
        else:
            change_day = 0.0
        stats.append(
            SymbolStats(
                symbol=sym,
                first=first,
                last=last,
                minimum=min(values),
                maximum=max(values),
                average=sum(values) / len(values),
                change_pct_period=change_period,
                change_pct_last_day=change_day,
                n_points=len(values),
            )
        )
    return stats


def to_csv(rates: dict[str, dict[str, float]], symbols: list[str]) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", *symbols])
    for d in _sorted_dates(rates):
        writer.writerow([d, *[rates[d].get(s, "") for s in symbols]])
    return buf.getvalue()


def _spark(values: list[float], width: int = 20) -> str:
    """Mini sparkline en bloques unicode."""
    blocks = "▁▂▃▄▅▆▇█"
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo or 1.0
    step = max(1, len(values) // width)
    sampled = values[::step]
    return "".join(blocks[min(len(blocks) - 1, int((v - lo) / span * (len(blocks) - 1)))] for v in sampled)


def to_markdown(
    base: str,
    rates: dict[str, dict[str, float]],
    stats: list[SymbolStats],
    generated_at: str,
) -> str:
    dates = _sorted_dates(rates)
    period = f"{dates[0]} → {dates[-1]}" if dates else "sin datos"
    lines = [
        f"# Reporte de tipos de cambio — base {base}",
        "",
        f"- Generado: {generated_at}",
        f"- Período: {period} ({len(dates)} días hábiles)",
        "- Fuente: Banco Central Europeo vía API pública Frankfurter (sin API key).",
        "",
        "## Resumen por divisa",
        "",
        f"| Divisa | Último (1 {base} =) | Var. día | Var. período | Mín | Máx | Promedio | Tendencia |",
        "|---|---:|---:|---:|---:|---:|---:|:--|",
    ]
    for s in stats:
        series = [rates[d][s.symbol] for d in dates if s.symbol in rates[d]]
        lines.append(
            f"| {s.symbol} | {s.last:,.4f} | {s.change_pct_last_day:+.2f}% | "
            f"{s.change_pct_period:+.2f}% | {s.minimum:,.4f} | {s.maximum:,.4f} | "
            f"{s.average:,.4f} | `{_spark(series)}` |"
        )
    lines += [
        "",
        "## Lectura",
        "",
        f"1 {base} compra hoy:",
    ]
    for s in stats:
        arrow = "▲" if s.change_pct_period > 0 else ("▼" if s.change_pct_period < 0 else "=")
        lines.append(
            f"- **{s.last:,.4f} {s.symbol}** {arrow} ({s.change_pct_period:+.2f}% en el período)."
        )
    lines.append("")
    return "\n".join(lines)
