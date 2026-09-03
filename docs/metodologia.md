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
