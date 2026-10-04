# Métricas finales del benchmark y carga operativa

Actualización: 4 de octubre de 2026. Esta nota sustituye la nomenclatura de
métricas en presentaciones finales; conserva los experimentos históricos.
No cambia el detector ni los parámetros congelados.

## API vigente

El benchmark está en `scripts/evaluate_synthetic_benchmark.py`, no en
`evaluation/evaluate_synthetic_benchmark.py`. Ambas señales usan el cálculo
compartido `evaluation/benchmark_metrics.py`. Cada registro se empareja con
su propia copia perturbada mediante identificador, o posición estable cuando
un registro histórico en memoria no conserva identificadores. Los cargadores
actuales conservan `Codigo Viaje` como clave de emparejamiento. No se restan porcentajes
agregados para reconstruir transiciones.

| Salida | Interpretación / fórmula |
|---|---|
| n_total | N: controles evaluables de la señal |
| review_before | B: controles REVIEW antes |
| non_review_before | N−B: controles NO REVIEW antes |
| review_after | P: casos REVIEW después |
| new_reviews | I: transiciones NO REVIEW → REVIEW |
| review_lost | L: transiciones REVIEW → NO REVIEW |
| baseline_review_rate | Tasa de marcado basal: B/N |
| baseline_non_review_rate | Tasa de no marcado en controles: (N−B)/N |
| post_perturbation_review_rate | Tasa de marcado tras perturbación: P/N |
| incremental_detection_rate | Tasa de detección incremental: I/(N−B) |

Las tasas de la API son **fracciones de 0 a 1**, sin redondeo; multiplicar por
100 al presentar porcentajes. Una tasa sin denominador es `None` (celda vacía
en CSV), no cero. Se verifica la misma población antes/después; P=B+I−L.
Los ya REVIEW no cuentan como nuevos. La ausencia observada de pérdidas no
se impone como regla: `review_lost` contabiliza también escenarios con pérdidas.
Las comparaciones exportan tasas y conteos por nivel con sufijo `_plus_25`, etc.

Los adaptadores agregados `rates` y `aggregate_rates` se mantienen únicamente
por compatibilidad histórica: están **deprecated**, emiten `DeprecationWarning`
y no se usan en las salidas vigentes. Sus claves antiguas `specificity`/`recall`
no acreditan ground truth: eran no marcado basal y marcado tras perturbación.
El comparador de consumo acepta encabezados históricos solo como entrada.
Cuando faltan transiciones emparejadas, deja vacía la tasa incremental; no la
infiere. Nuevas tablas no exportan esas claves ni balanced accuracy/Youden.
Los artefactos ya generados no se sobrescriben como parte de esta revisión.

## Resultados finales vigentes del snapshot 2026

Consumo: únicamente antes del 20/08/2026; lote posterior no comparable por
calidad en la capa de evaluación. Temporal conserva sus resultados evaluables.
Referencias 2024–2025 y configuración congelada intactas.

| Señal | N | REVIEW basal | Tasa de marcado basal | Tasa de no marcado |
|---|---:|---:|---:|---:|
| Consumo comparable | 6230 | 455 | 7,30 % | 92,70 % |
| Temporal | 9644 | 1257 | 13,03 % | 86,97 % |

| Perturbación | Consumo: marcado tras perturbación | Consumo: incremental | Temporal: marcado tras perturbación | Temporal: incremental |
|---|---:|---:|---:|---:|
| +25 % | 18,96 % | 12,57 % | 24,83 % | 13,57 % |
| +50 % | 47,26 % | 43,10 % | 40,18 % | 31,21 % |
| +100 % | 82,15 % | 80,74 % | 65,84 % | 60,72 % |
| +200 % | 92,73 % | 92,16 % | 87,33 % | 85,43 % |
| +500 % | 98,33 % | 98,20 % | 98,66 % | 98,46 % |

Consumo +25 %: 726 nuevos REVIEW / 5775 inicialmente NO REVIEW =
12,57142857 %. No existe ground truth de ineficiencia real; estas tasas
describen marcado y respuesta a perturbaciones artificiales.

## Trazabilidad de los parámetros

| Parámetro | Función | Evidencia 2024 → 2025 y alternativa | Limitación / decisión |
|---|---|---|---|
| r >0,50 | Magnitud relativa respecto a referencia | Regla conjunta: marcado basal 7,204 % consumo y 12,454 % temporal; comparados r>1 y r>2, reglas individuales y combinadas | Compromiso razonable validado en 2025; no óptimo ni universal |
| z >2 | Excepcionalidad respecto a dispersión robusta | Usado con r>0,50 mediante AND; comparados z>3, z>5 y OR. OR 0,50/2 marca 12,663 % consumo y 19,414 % temporal | AND exige ambas condiciones y reduce marcado, con menor respuesta a perturbaciones pequeñas; no óptimo ni universal |
| Contexto ≥30 | Soporte mínimo de referencia vehículo×rango con fallback | B30: 119 contextos, 92,943 % uso contextual; B50: 100 contextos, 85,479 %. Ambos 23849 evaluables y cobertura 96,959 %; P99 desviación 3,628 frente a 6,215 | Compromiso soporte/cobertura contextual; más contexto con muestras menores, sin optimización exhaustiva |
| Historia ≥100 | Historia válida mínima por vehículo para cada señal | Consumo: 22/23 vehículos, 14837/14886 registros históricos; 22 evaluables menos frente a exploración sin mínimo. Temporal >1 km: 30 vehículos elegibles | Requisito conservador de diseño viable; no se ha demostrado que 100 sea óptimo; no hubo barrido exhaustivo |

La configuración se congeló por decisión técnica apoyada en 2025. No se
reajustan parámetros con los resultados de 2026. Véase la
[configuración congelada](configuracion-congelada-validacion-2025.md).

## Interpretación operativa final

1507/13484 viajes = **11,18 % REVIEW global**. En **163 días con actividad**:
mediana **10 REVIEW/día**, P90 **18**, P95 **20**, máximo **27** (media 9,25).
Se usan fechas reales y se incluyen días activos sin REVIEW; percentiles por
interpolación lineal. Es un snapshot hasta 25/08/2026, sin registros de julio;
no se extrapola a un año completo.

Los tipos se excluyen mutuamente: 250 solo consumo, 1052 solo temporal y
205 ambos; suman 1507. Equivalente: 455+1257−205=1507.
El subconjunto marcado reduce el volumen potencial frente a inspeccionar
todos los viajes, pero no demuestra que los no REVIEW puedan ignorarse:
incluyen 2805 NOT_EVALUABLE. Capacidad, coste y tiempo humano de revisión
no están medidos. No se afirma que la carga sea aceptable; los picos podrían
generar fatiga si superan la capacidad disponible, sin que dicha fatiga se
haya medido aquí.

Fuente de las cifras: auditoría privada ya terminada de métricas y carga
operativa; esta revisión de coherencia no ejecuta una nueva auditoría ni
modifica los artefactos privados o históricos.
