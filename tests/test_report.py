"""Tests del cálculo de estadísticas, CSV, Markdown y alertas (sin red)."""
from fx_report.notify import build_alert
from fx_report.report import compute_stats, to_csv, to_markdown

RATES = {
    "2026-10-20": {"EUR": 0.90, "BRL": 5.00},
    "2026-10-21": {"EUR": 0.89, "BRL": 5.05},
    "2026-10-22": {"EUR": 0.88, "BRL": 5.10},
}
SYMBOLS = ["EUR", "BRL"]


def test_compute_stats_basico():
    stats = {s.symbol: s for s in compute_stats(RATES, SYMBOLS)}
    eur = stats["EUR"]
    assert eur.first == 0.90
    assert eur.last == 0.88
    assert eur.minimum == 0.88
    assert eur.maximum == 0.90
    assert round(eur.change_pct_period, 2) == round((0.88 - 0.90) / 0.90 * 100, 2)
    # Último día: 0.88 vs 0.89
    assert round(eur.change_pct_last_day, 4) == round((0.88 - 0.89) / 0.89 * 100, 4)


def test_to_csv_tiene_encabezado_y_filas():
    out = to_csv(RATES, SYMBOLS)
    lines = out.strip().splitlines()
    assert lines[0] == "date,EUR,BRL"
    assert len(lines) == 4  # encabezado + 3 días


def test_to_markdown_incluye_divisas():
    stats = compute_stats(RATES, SYMBOLS)
    md = to_markdown("USD", RATES, stats, "2026-10-22 12:00 UTC")
    assert "Reporte de tipos de cambio" in md
    assert "EUR" in md and "BRL" in md


def test_build_alert_dispara_sobre_umbral():
    stats = compute_stats(RATES, SYMBOLS)
    # BRL subió ~0.99% el último día; EUR ~1.12%. Umbral 1.0% => al menos EUR.
    alert = build_alert(stats, 1.0)
    assert alert is not None
    assert "EUR" in alert


def test_build_alert_no_dispara_con_umbral_alto():
    stats = compute_stats(RATES, SYMBOLS)
    assert build_alert(stats, 10.0) is None
