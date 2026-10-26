"""fx-report: pipeline de una API pública a un reporte + alerta.

Toma tipos de cambio del Banco Central Europeo vía la API pública Frankfurter
(sin API key), calcula estadísticas del período, arma un reporte en Markdown y
CSV, y manda una alerta opcional cuando una divisa se mueve más que un umbral.

Pensado como ejemplo del Servicio 2 (automatización e integraciones): "de una
fuente pública a un reporte/alerta".
"""

__version__ = "1.0.0"
__user_agent__ = (
    "fx-report-demo/1.0 "
    "(+https://github.com/IxSnow/fx-report-demo; reporte de portafolio)"
)
