# Metodología

Este documento registrará la metodología de trabajo y las evidencias generadas durante el TFM.

## Decisiones confirmadas

### Evaluación funcional del componente conversacional

- Los detectores deterministas `DetectorV1` y `TemporalDetectorV1`, junto con
  las reglas de consolidación existentes, son la fuente de verdad sobre las
  desviaciones analíticas. El LLM se limitará a explicar esa salida y no podrá
  decidir, corregir ni reinterpretar los estados.
- No existe *ground truth* empresarial que confirme ineficiencias reales. Por
  ello, `REVIEW` significa exclusivamente «desviación a revisar» y nunca una
  ineficiencia confirmada ni una causa determinada.
- La evaluación conversacional medirá fidelidad numérica y semántica respecto
  a la salida estructurada de la capa analítica. También valorará claridad y
  utilidad mediante una rúbrica cualitativa. No mide la capacidad de los
  detectores para identificar ineficiencias reales.
- Las métricas obtenidas mediante perturbaciones semi-sintéticas para evaluar
  los detectores pertenecen a otro experimento y no deben confundirse con la
  evaluación de las explicaciones conversacionales.

La muestra inicial propuesta contiene hasta 20 casos reales de 2026,
seleccionados como muestra de evaluación funcional estratificada del componente
conversacional. No es una muestra estadísticamente representativa de toda la
operación logística. Los estratos provisionales son:

- hasta 5 `NO_RELEVANT_DEVIATION` con cobertura `COMPLETE`;
- hasta 5 `REVIEW` con cobertura `COMPLETE`;
- hasta 5 `NOT_EVALUABLE` con cobertura `NONE`;
- hasta 5 casos con cobertura `PARTIAL`.

Dentro de `REVIEW` con cobertura completa se intentará incluir, cuando existan,
casos de consumo solamente, temporal solamente y ambas señales. La selección
es determinista, no altera detectores ni umbrales y no fabrica observaciones.
El artefacto registra la disponibilidad y cualquier carencia por estrato cuando
los datos no permiten alcanzar cinco casos.

La infraestructura vive fuera del código productivo en
`evaluation/conversational_dataset.py`. Construye una sola instancia de
`AnalyticalService` con 2024–2025, carga los candidatos de 2026 mediante una
consulta SQL masiva y evalúa cada candidato exclusivamente con dicho servicio.
El JSON resultante conserva estados, motivos y magnitudes analíticas necesarias,
pero sustituye la identidad operacional por un identificador seudonimizado y
elimina viaje, vehículo y fecha. Se escribe bajo `data/`, ruta ignorada por Git.

La plantilla `evaluation/rubric_template.json` define C1–C6 con valores
permitidos `1`, `0`, `null` y `N/A`, una escala `clarity_utility` de 1 a 5 o
`null` y `observations` como texto o `null`. La lista comienza vacía para no
introducir resultados ficticios.

#### Evaluación de fidelidad y utilidad de las explicaciones del LLM

El sistema analítico determinista es la fuente de verdad de esta evaluación.
El LLM no decide si existen anomalías ni modifica la salida analítica: su única
función es explicar el resultado estructurado recibido. En particular,
`REVIEW` identifica una desviación que requiere revisión y no equivale a una
ineficiencia confirmada. La señal temporal evalúa la magnitud
`minutes_per_km`; no representa ni permite inferir tiempo de parada.

No existe *ground truth* real de ineficiencia para los casos de esta evaluación
conversacional. Por tanto, la rúbrica no mide la capacidad de detectar
ineficiencias reales, sino la fidelidad de cada explicación al resultado
analítico y su utilidad para la revisión humana. Las respuestas han sido
generadas y congeladas antes de comenzar la puntuación, de modo que la revisión
no altera los textos evaluados. Además, la muestra es funcional y estratificada;
no es representativa de las prevalencias reales de los distintos estados en la
operación.

Cada criterio C1–C6 se registra como `1`, `0` o `N/A`, de acuerdo con estas
reglas:

- **C1_global_status**:
  - `1`: comunica correctamente `overall_status` y no lo contradice.
  - `0`: cambia o contradice `overall_status`, o lo interpreta como otro estado.
  - `N/A`: no aplicable; C1 siempre debe evaluarse.
- **C2_signal_statuses**:
  - `1`: describe correctamente el estado de las señales de consumo y temporal.
  - `0`: atribuye un estado incorrecto o contradice el resultado de alguna señal.
  - `N/A`: solo cuando no resulte razonable evaluar estados individuales debido
    a la naturaleza del caso; su uso debe justificarse en `observations`.
- **C3_numeric_fidelity**:
  - `1`: las cifras o magnitudes relevantes mencionadas son fieles al resultado
    analítico, admitiendo un redondeo razonable.
  - `0`: inventa, altera o interpreta incorrectamente una cifra relevante.
  - `N/A`: la respuesta no incluye ninguna magnitud numérica verificable.
- **C4_no_unsupported_causes**:
  - `1`: no atribuye causas no demostradas.
  - `0`: afirma o sugiere como explicación causal tráfico, conductor, avería,
    carga, ruta, clima u otra causa no sustentada por los datos.
  - `N/A`: no aplicable; C4 siempre debe evaluarse.
- **C5_no_confirmed_inefficiency_claim**:
  - `1`: cuando existe `REVIEW`, mantiene el resultado como desviación a revisar
    y no como ineficiencia confirmada.
  - `0`: presenta `REVIEW` como ineficiencia, anomalía confirmada o conclusión
    causal.
  - `N/A`: no existe ninguna señal `REVIEW`.
- **C6_not_evaluable_and_coverage**:
  - `1`: interpreta correctamente `NOT_EVALUABLE` y las coberturas `PARTIAL` o
    `NONE`, sin convertir la ausencia de evaluación en normalidad.
  - `0`: presenta una señal no evaluable como normal o evaluada, o describe
    incorrectamente la cobertura.
  - `N/A`: el caso tiene cobertura `COMPLETE` y ninguna señal `NOT_EVALUABLE`.

`clarity_utility` se registra como una escala humana independiente de los
criterios de fidelidad:

- `1`: explicación confusa o poco útil.
- `2`: explicación comprensible, pero con problemas importantes.
- `3`: explicación correcta y suficientemente útil.
- `4`: explicación clara, concisa y útil para la revisión operativa.
- `5`: explicación especialmente clara y accionable sin exceder la evidencia
  disponible.

Los valores `N/A` se excluyen del denominador al calcular las tasas de
cumplimiento. `clarity_utility` se analiza por separado y no forma parte de
dichas tasas.

### Procedimiento manual de evaluación con GPT-5.6 Luna

El procedimiento se ejecuta sin integrar ni invocar automáticamente al modelo:

1. `evaluation/prepare_llm_evaluation.py` lee el conjunto anonimizado y genera
   una ficha determinista por caso. Cada ficha conserva `case_id`, estrato y
   resultado analítico, y comienza con `model`, `response` y las puntuaciones
   manuales vacíos.
2. La respuesta producida externamente con GPT-5.6 Luna se registra junto con
   el nombre del modelo. Una persona asigna `1`, `0`, `null` o `N/A` a C1–C6,
   una valoración opcional de claridad y utilidad entre 1 y 5, y observaciones
   opcionales. El código no deduce puntuaciones a partir de la respuesta.
3. `evaluation/summarize_llm_evaluation.py` valida los valores registrados y
   calcula cumplimientos por criterio, cumplimiento global, media de claridad
   y utilidad, resultados por estrato y recuentos de `N/A`. Los valores `null`
   permanecen como criterios no puntuados y `N/A` queda fuera del denominador
   de cumplimiento.

Los archivos preparados y los resúmenes se generan bajo
`data/conversational_evaluation/`, por lo que permanecen fuera de Git. Este
procedimiento no modifica la selección de casos ni genera resultados de
evaluación ficticios.

## Decisiones provisionales

No hay decisiones metodológicas provisionales documentadas todavía.

## Supuestos

No hay supuestos metodológicos documentados todavía.

## Decisiones pendientes

No hay decisiones metodológicas pendientes documentadas todavía.

## Cuestiones que requieren investigación

No hay cuestiones de investigación metodológica documentadas todavía.

## Cuestiones que requieren validación con datos

No hay cuestiones de validación con datos metodológicas documentadas todavía.

## Estructura prevista del documento

- Objetivo y alcance de cada fase.
- Actividades realizadas.
- Evidencias y resultados.
- Criterios de validación.
- Riesgos, limitaciones y acciones de seguimiento.
