# Configuración congelada tras la validación 2024 → 2025

> Nota de nomenclatura revisada (04/10/2026): las menciones históricas a
> «especificidad»/`specificity` y «recall» describen respectivamente tasa de no
> marcado en controles y tasa de marcado tras perturbación, sin ground truth
> real. Se conservan como trazabilidad; para resultados finales y detección
> incremental véase [Métricas finales](metricas-finales-benchmark.md). El término
> «sensibilidad» en análisis de parámetros conserva su sentido metodológico.


Fecha de congelación: **2 de octubre de 2026**, Europe/Madrid.

Propósito: registrar la decisión técnica adoptada por el responsable del TFM
exclusivamente a partir de la validación 2025, antes de ejecutar de nuevo la
evaluación final 2026. Esta configuración coincide con el motor actual: no se
modifica código productivo. La congelación y sus evidencias se versionan antes
de ejecutar la evaluación final.

## Configuración completa

- Baseline B30: mediana y MAD por vehículo y rango de distancia; fallback a la
  referencia general del vehículo cuando el contexto no alcanza el mínimo.
- Mínimo por vehículo: **100 observaciones históricas válidas**, para cada señal.
- Mínimo contextual: **30 observaciones históricas válidas**.
- Escala robusta: `1.4826 * MAD`;
  `robust_z = (valor - mediana) / (1.4826 * MAD)`.
- Regla estricta para ambas señales:
  `relative_deviation > 0.50 AND robust_z > 2`.
- Consumo: L/100 km, distancia positiva y consumo positivo disponible, sin
  exclusión adicional de distancia corta.
- Temporal: minutos/km, duración positiva y **distancia >1 km**, tanto en el
  histórico como en la evaluación. La duración no se interpreta como parada.
- Se mantienen los rangos, normalizaciones y políticas del motor actual.
  Ausencia de referencia o MAD cero implica `NOT_EVALUABLE`.
- `REVIEW` significa desviación a revisar; no confirma ineficiencia ni causalidad.

Selección: referencias 2024 y validación 2025. Evaluación final posterior al
commit: reconstruir referencias con **2024 + 2025** y evaluar **2026**, sin
seleccionar candidatos ni cambiar parámetros después de observar resultados.
Perturbaciones finales: +25 %, +50 %, +100 %, +200 % y +500 %, exclusivamente
sobre copias de los registros de evaluación, conservando las referencias.

## Evidencia de 2025 y compromisos aceptados

| Decisión | Evidencia 2024 → 2025 | Compromiso aceptado | Nivel |
| --- | --- | --- | --- |
| B30 | 23.849 evaluables; cobertura 96,959 %. Uso contextual 92,943 % frente a 85,479 % con B50. P99 de desviación 3,628 frente a 6,215 con B50 y 13,283 con A. | Favorecer contexto y menores colas observadas; no equivale a probar detección real superior. | fuerte |
| Contexto ≥30 | 119 contextos frente a 100 con mínimo 50; igual cobertura total y mayor uso contextual. | Más contexto con muestras menores. | razonable |
| Vehículo ≥100 | 22/23 vehículos de consumo; 14.837/14.886 registros históricos; 22 evaluables menos que en la exploración sin ese mínimo. Temporal >1 conserva 30 vehículos históricos elegibles. | Requisito conservador de diseño frente a pérdida de cobertura; no hubo barrido de mínimos. | decisión de diseño con evidencia limitada |
| AND | Control marcado 7,204 % consumo y 12,454 % temporal, frente a 12,663 % y 19,414 % con OR 0,50/2. | Exigir simultáneamente magnitud relativa y rareza respecto a variabilidad histórica; menor recall de perturbaciones pequeñas. | razonable |
| Desviación >0,50 | Recall de la regla conjunta en consumo: 19,112/47,289/87,081/96,474/99,291 %; temporal: 23,876/39,379/66,223/88,503/98,683 %, en las cinco perturbaciones. | Mantener un compromiso de diseño; otros cortes también presentan compromisos no dominados. | razonable |
| Robust z >2 | Los comparadores individuales y combinados muestran el compromiso entre marcado y recall; ningún candidato con benchmark completo domina a todos los demás. | Mantener respuesta a perturbaciones con el coste de marcado observado; no optimización de un objetivo nuevo. | razonable |
| Temporal >1 km | 30.506 válidos restantes, 29.381 evaluables, cobertura restante 96,312 %. P99 del KPI 15,040 min/km frente a 113,333 sin corte y 23,286 con >0,5. | Descartar 6.584 válidos (17,751 %); conservar más población que >2, aceptando mayor dispersión. | razonable |

El mínimo 100 **es un requisito conservador de diseño y no se ha demostrado
que sea el valor óptimo**. No se afirma que ningún parámetro sea óptimo ni que
>1 km sea el único corte válido. Las prioridades y compromisos anteriores son
una decisión técnica explícita del responsable del TFM, no una función de
puntuación inferida retrospectivamente. Las tasas de controles marcados y la
especificidad son experimentales; no hay ground truth real de ineficiencia.

## Evidencias y límites

- [Protocolo previo](protocolo-validacion-2025.md).
- [Auditoría y tablas completas](auditoria-validacion-2025.md).
- [Resultados agregados 2025](resultados-validacion-2025/validation_2025.json)
  y sus CSV asociados.

**Históricamente hubo exposición exploratoria previa a 2026. Esta
reconstrucción metodológica no puede convertir 2026 retroactivamente en un
conjunto nunca observado.** La corrección consiste en explicitar la selección
con 2025, congelar sus decisiones antes de la nueva ejecución y mantenerlas
durante la evaluación final. No se reclama una evaluación prospectiva intacta.

Los resultados anteriores se conservan como evidencia histórica. Si los nuevos
resultados coinciden, se informará la coincidencia sin atribuirla a una mejora
numérica de la metodología. Si difieren, se informarán sin ajustar parámetros.

## Condición de ejecución final

La suite completa debe pasar antes del commit de trazabilidad y de la nueva
ejecución. El commit incluye solo código experimental, tests, documentos y
resultados agregados sin identificadores operacionales. Los datos originales y
los artefactos bajo `data/` permanecen fuera de Git. El tag `v1.0-tfm` permanece
intacto y no se crea ningún tag nuevo.
