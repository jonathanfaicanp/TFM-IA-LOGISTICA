# Delimitación del año 2026: limitación conservada

Revisión documental del 5 de octubre de 2026. No se generaliza el detector,
no se cambian referencias, reglas ni resultados experimentales.

## Clasificación de apariciones

| Tipo | Localización | Significado |
|---|---|---|
| A. Evaluación formal | scripts/analyze_b30_2026_deviations.py; scripts/evaluate_2026_baseline_strategies.py; scripts/profile_dataset.py | Selección, agregación y nombres de salidas del snapshot 2026; no política productiva dinámica |
| A. Evaluación formal | evaluation/conversational_dataset.py: EVALUATION_START y source_period | Ventana de selección conversacional [2026-01-01, 2027-01-01); no modifica la evaluación del detector |
| A. Trazabilidad | scripts/validate_methodology_2025.py: final_2026_executed | Indicador de que la validación 2025 no ejecuta evaluación final; el año forma parte del nombre del campo |
| B. Fixtures/tests | tests/: fechas, límites, registros inventados y expectativas de separación temporal | Pruebas del alcance formal, contratos de periodo y exclusión de otras fechas; no datos empresariales |
| C. Configuración experimental | scripts/analyze_b30_mad.py, analyze_temporal_robustness.py, analyze_distance_threshold_sensitivity.py, evaluate_detector_candidates.py, evaluate_synthetic_benchmark.py, evaluate_temporal_synthetic_benchmark.py | evaluation_year=2026 y/o --evaluation-year; valores por defecto de experimentos, con particiones configurables donde existe ese argumento |
| D. Lógica del detector | src/detector.py: EVALUATION_YEAR=2026; DetectorV1.evaluate_normalized | Rechaza años distintos antes de evaluar validez, referencia y umbrales |
| D. Lógica temporal | src/temporal_detector.py: importación de EVALUATION_YEAR y evaluate_normalized | La misma delimitación anual para temporal; no literal duplicado |
| D. Preparación histórica SQL/API | src/sql_repository.py: load_historical_rows | Consulta historia desde 2024-01-01 hasta 2026-01-01 exclusivo: años 2024–2025 |

La búsqueda relevante abarcó src/, scripts/, evaluation/ y tests/. Las
menciones en docstrings, nombres de salidas y mensajes de resumen son
descriptivas de esos mismos experimentos. Los ejemplos sintéticos de examples/
y README usan 2026 para respetar el alcance vigente. No se alteran scripts o
artefactos privados bajo data/.

## Por qué un viaje de 2027 no es evaluable

Ambos detectores comparan `trip.year != EVALUATION_YEAR` y devuelven
`NOT_EVALUABLE` con motivo `OUTSIDE_EVALUATION_PERIOD`. La API convierte el
timestamp en fila analítica y delega en estos detectores; no hay un bug técnico
independiente que permita eliminar esa restricción sin cambiar el alcance.
Los endpoints por periodo pueden consultar otras fechas, pero eso no amplía
la evaluabilidad. El cargador SQL conserva asimismo la ventana histórica fija.

Para generalizar correctamente habría que decidir qué años se evalúan y qué
referencias les corresponden: histórico fijo, todos los años anteriores, dos
años anteriores o ventana móvil, además de cómo prevenir fuga temporal,
actualizar mínimos/MAD y tratar incidencias de comparabilidad. Ninguna de
esas políticas está definida por la evaluación actual.

## Impacto de una posible generalización

Cambiar la guarda anual cambiaría los resultados de viajes de 2027 aunque
se mantuvieran umbrales. Cambiar los años históricos podría modificar mediana,
MAD, vehículos/contextos elegibles y los estados de viajes actualmente
evaluados. Habría que actualizar las expectativas de OUTSIDE_EVALUATION_PERIOD
en tests/test_detector_v1.py y tests/test_temporal_detector_v1.py, las pruebas
de ventana histórica SQL en tests/test_sql_repository.py y, si se ampliara la
selección, tests/test_conversational_dataset.py. También habría que añadir
tests de separación temporal y reproducibilidad de referencias por periodo.

Los benchmarks y resultados publicados siguen referidos a las referencias
y población congeladas; una nueva política no queda validada por esos
resultados. No se ha ejecutado esa generalización ni evaluado su efecto.

**Recomendación: LIMITACIÓN, conservar 2026.** Ampliarlo requiere una nueva
decisión metodológica y su validación, no una corrección de instalación o API.
