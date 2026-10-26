# fx-report

Pequeño pipeline de **automatización**: de una API pública a un reporte y una
alerta. Toma los tipos de cambio diarios del Banco Central Europeo (vía la API
pública [Frankfurter](https://frankfurter.dev), **sin API key**), calcula
estadísticas del período, genera un reporte en **Markdown + CSV** y envía una
**alerta opcional** (webhook o ntfy) cuando una divisa se mueve más que un
umbral configurable.

Caso de uso real: un freelancer que cobra en **USD** y quiere seguir la fuerza
del dólar frente a una canasta de divisas, con un reporte diario automático.

> Demo de portafolio para el **Servicio 2 (automatización e integraciones)**.
> El mismo patrón —"fuente pública → procesar → reporte + aviso"— se adapta a
> ventas, stock, indicadores o cualquier API del cliente.

## Qué muestra

- Consumo de una **API pública** real (sin credenciales).
- Procesamiento: variación diaria y del período, mín/máx/promedio y una
  mini-tendencia (sparkline) por divisa.
- Salida doble: **reporte Markdown** legible + **CSV** para abrir en Excel/Sheets.
- **Alerta por umbral** vía webhook/ntfy, configurable por variables de entorno.
- Config por YAML/JSON, tests con `pytest`, licencia MIT, User-Agent honesto.

## Diagrama del flujo

```
config.yaml ─▶ API Frankfurter (BCE) ─▶ serie diaria
                                           │
                                 ┌─────────┴─────────┐
                                 ▼                   ▼
                        reporte.md + serie.csv   estadísticas
                                                     │
                                        ¿movió > umbral? ──sí──▶ webhook / ntfy
                                                     └──no──▶ nada
```

## Instalación y uso

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # solo si quieres alertas

python -m fx_report.cli -c config.example.yaml            # reporte + alerta
python -m fx_report.cli -c config.example.yaml --no-notify  # solo reporte
```

### Configuración (`config.example.yaml`)

```yaml
base: "USD"
symbols: ["EUR", "BRL", "MXN", "GBP", "JPY"]
days: 14
alert_threshold_pct: 1.0
out_dir: "output"
```

Divisas soportadas por el dataset gratuito del BCE: AUD, BRL, CAD, CHF, CNY,
CZK, DKK, EUR, GBP, HKD, HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN, MYR, NOK, NZD,
PHP, PLN, RON, SEK, SGD, THB, TRY, USD, ZAR.
(Nota honesta: **CLP no está** en el dataset gratuito del BCE; por eso la demo
sigue la fuerza del USD frente a una canasta. Para CLP se usaría otra fuente.)

### Alertas (variables de entorno)

- `WEBHOOK_URL` — recibe un `POST` JSON `{title, message}` (Slack/Discord/n8n/Make).
- `NTFY_SERVER` + `NTFY_TOPIC` — push al celular con ntfy.

### Programación (cron)

```cron
0 9 * * 1-5 cd /ruta/a/fx-report && .venv/bin/python -m fx_report.cli -c config.example.yaml >> output/cron.log 2>&1
```

## Salida de ejemplo (corrida real)

Reporte generado contra la API el 2026-10-23 (ver
[`examples/sample_reporte.md`](examples/sample_reporte.md) y
[`examples/sample_serie.csv`](examples/sample_serie.csv)):

```
# Reporte de tipos de cambio — base USD

- Período: 2026-10-09 → 2026-10-23 (11 días hábiles)
- Fuente: Banco Central Europeo vía API pública Frankfurter (sin API key).

| Divisa | Último (1 USD =) | Var. día | Var. período | Mín | Máx | Promedio | Tendencia |
|---|---:|---:|---:|---:|---:|---:|:--|
| EUR | 0.8934 | +0.11% | +0.12% | 0.8887 | 0.8944 | 0.8921 | ▅█▇▆▅▁▃▄▂▅▆ |
| MXN | 18.7823 | +0.11% | +3.20% | 18.2001 | 18.7823 | 18.4708 | ▁▂▂▂▄▃▄▄▄▇█ |
```

Alerta real enviada a un webhook (umbral 0.1 %):

```json
{
  "title": "fx-report: movimiento de divisas",
  "message": "Divisas que se movieron más de 0.10% en el último día:\n- EUR: +0.11% (ahora 0.8934)\n- JPY: -0.16% (ahora 156.8000)"
}
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 5 tests (estadísticas, CSV, Markdown, alertas)
```

## Licencia

MIT — ver [LICENSE](LICENSE).
