# Auditoría de corrección de escala y reevaluación conversacional cerrada

Fecha de cierre histórico: 3 de octubre de 2026 (Europe/Madrid).
Actualización de trazabilidad: 5 de octubre de 2026.

**Las cifras definitivas corresponden a la evaluación 3**, realizada sobre
una nueva muestra tras la política de calidad: 95/95 = 100 %, claridad 4,00/5.
La repetición SQL descrita originalmente aquí es la **evaluación 2 histórica**,
con resultado registrado 95/96 = 98,96 % y una salvedad en el artefacto de
case_006. Se conservan sus puntuaciones sin reinterpretarlas retrospectivamente.

## Reconstrucción de los casos y corrección analítica

El problema detectado fue un antiguo error de escala ×1000 en el adaptador
SQL: la conversión `float(Consumo) * 1000` introducía un factor adicional
antes de la normalización. La corrección usa `float(Consumo)`, conservando
NULL. Las magnitudes absolutas históricas de consumo eran incorrectas.
Esta auditoría aborda su efecto sobre la evaluación conversacional histórica
de 20 casos. Archivo/función: `src/sql_repository.py`, `_to_analytical_row()`.
La transformación antigua era `float(consumption_liters) * 1000`; la corrección
elimina esa multiplicación adicional, conservando la normalización posterior.
Commit: `77e4bb54efc6827713ef3ce7123f29f9241e92d4` (25/09/2026).

La herramienta `scripts/audit_conversational_sql_correction.py` se ejecutó
contra SQL en el servidor remoto. Los artefactos recuperados en
`data/conversational_evaluation_corrected_audit/` acreditan **20/20
UNIQUE_MATCH y 20 viajes distintos**, sin casos ambiguos ni ausentes.
Se reconstruyeron inequívocamente los mismos 20 viajes originales, manteniendo
los mismos case_id, orden, cuatro estratos de cinco casos y procedimiento
de anonimización. No se seleccionó una muestra nueva.

La selección determinista sobre la fuente actual no coincide con la original;
la identidad de la muestra repetida se sustenta en la correspondencia única
de cada caso, no en volver a ejecutar esa selección. El mapping de identidades
permanece privado, bajo data/ y fuera de Git.

Los **11 casos con consumo evaluable** presentan un factor original/corregido
de aproximadamente **1000** en las magnitudes absolutas de consumo:
`consumo_litros`, `consumo_l_100km`, `baseline` y `mad`. No se observaron
cambios absolutos inesperados. El dataset corregido se obtuvo mediante el
motor y el adaptador corregidos sobre SQL, no mediante una división manual
del dataset histórico.

| Comparación original frente a corregido | Resultado |
| --- | --- |
| overall_status | 0 cambios |
| analysis_coverage (cobertura) | 0 cambios |
| review_signals | 0 cambios |
| relative_deviation | 0 cambios relevantes |
| robust_z | 0 cambios relevantes |
| Métricas temporales | Exactamente iguales |

La invariancia numérica se verifica con `rel_tol=1e-9` y `abs_tol=1e-9`:
las pequeñas diferencias de coma flotante no representan cambios analíticos.
Estados y métricas invariantes también forman parte del criterio de matching;
esta evidencia corresponde a los 20 casos reconstruidos y no constituye una
prueba universal para cualquier viaje.

El detector determinista calcula las señales, los estados y la cobertura;
el componente generativo interpreta esos resultados y redacta las respuestas.
La invariancia comprobada del detector en esta muestra no implica ausencia
general de efectos del error de escala sobre las respuestas generadas ni
sobre otros usos de las magnitudes absolutas.

Con un factor común positivo k, `(kx−km)/(km) = (x−m)/m` y
`(kx−km)/(1,4826·k·MAD) = (x−m)/(1,4826·MAD)`: el factor cancela en
relative_deviation y robust_z. Esto explica los estados invariantes en los
casos auditados, aunque las magnitudes entregadas al componente generativo
eran incorrectas. No debe confundirse este bug con la discontinuidad posterior
observada en el campo fuente Consumo desde el 20/08/2026, de causa y unidad
no confirmadas.

## Repetición formal y evaluación humana

La plantilla corregida se preparó desde
`data/conversational_evaluation_corrected_audit/corrected_cases.json` mediante
las utilidades existentes. Toda la repetición quedó separada bajo
`data/conversational_evaluation_corrected/`.

Se repitió la evaluación mediante n8n con **GPT-5.6-LUNA**, el mismo prompt
original y el workflow documentado en `n8n/conversational_evaluation_v1.json`.
Se conservaron la entrada `JSON.stringify($json.analytical_result)`, el formato
de salida y el procesamiento de los 20 casos; las rutas se adaptaron para
separar los artefactos corregidos. El prompt conservado está en
`data/conversational_evaluation_corrected/prompt_original.txt`.

El archivo real `luna_responses.json` contiene 20 respuestas nuevas, 20
case_id únicos, ninguna respuesta vacía y los mismos identificadores de la
plantilla; los registros indican GPT-5.6-LUNA. No se simularon respuestas ni
se reutilizaron textos históricos.

Se realizó una **nueva evaluación humana de los 20 casos**, aceptada como
final, con la misma rúbrica C1–C6 y claridad/utilidad de 1 a 5. La hoja se
preparó con puntuaciones vacías; no se copiaron las puntuaciones históricas.
Las puntuaciones aceptadas se validaron e importaron mediante
`evaluation.import_llm_review_scores`, y el resumen se calculó mediante
`evaluation.summarize_llm_evaluation`.

## Resultados históricos registrados: evaluaciones 1 y 2

Fuente: `data/conversational_evaluation_corrected/luna_evaluation_summary.json`,
calculada desde `luna_evaluation_scored.json` de la misma carpeta.

| Métrica | Evaluación 1 original | Evaluación 2, corrección SQL |
| --- | ---: | ---: |
| Casos evaluados | 20 | 20 |
| C1: estado global | 100 % | 100 % |
| C2: estados de señales | 100 % | 100 % |
| C3: fidelidad numérica | 95 % | 95 % |
| C4: ausencia de causas no sustentadas | 100 % | 100 % |
| C5: ausencia de afirmación de ineficiencia confirmada | 100 % (6 aplicables) | 100 % (6 aplicables) |
| C6: no evaluabilidad y cobertura | 100 % (10 aplicables) | 100 % (10 aplicables) |
| Cumplimiento global | 98,96 % | 98,96 % |
| Claridad/utilidad media | 3,95/5 | 3,95/5 |
| Criterios N/A | 24 | 24 |
| Criterios sin puntuar | 0 | 0 |

El cumplimiento global corresponde a 95 criterios cumplidos de 96 aplicables;
los N/A se excluyen del denominador. El único criterio incumplido registrado
es **case_006, C3**:
la respuesta convierte incorrectamente una desviación relativa extrema a
porcentaje. Una desviación relativa de 1189.597 equivale aproximadamente a
**118959.7 %**, no a 1189.6 %. Su claridad es 3/5; los otros 19 casos tienen
claridad 4/5. El viaje histórico tiene fecha **25/08/2026** y distancia
**12,782 km**, rango >10 y ≤20 km: **no era un viaje corto**.
El valor corregido de relative_deviation es `1189.5972035437394`; el porcentaje
correcto es aproximadamente **118959,72 %**. El fallo es de verbalización del
componente generativo, no del estado REVIEW calculado por el detector.

### Salvedad del artefacto conservado de case_006

La revisión documental posterior detectó que, en
`data/conversational_evaluation_corrected/luna_evaluation_scored.json`, el
analytical_result de case_006 contiene consumo total 0,905 L, observado
7,080269128461899 L/100 km y baseline 0,005946821567687135 L/100 km.
Sin embargo, su respuesta conservada, también presente en luna_responses.json,
verbaliza **905 litros**, **7080,27 L/100 km** y **5,95 L/100 km**: magnitudes
absolutas antiguas. La corrección de la entrada analítica no acredita una
regeneración completamente limpia de la explicación conservada.

El resultado 95/96 y el único criterio C3 incumplido son los **registrados**;
no se cambian puntuaciones, respuestas ni artefactos históricos. Esta salvedad
debe acompañar cualquier presentación de la evaluación 2.

Si se presenta un intervalo para 95/96, el Wilson bilateral 95 % es
aproximadamente **[94,33 %, 99,82 %]**, descriptivo sobre criterios aplicables.
Estos criterios proceden de 20 casos y no se consideran observaciones
independientes para generalizar el rendimiento del modelo.

La comparación completa de los resúmenes histórico y corregido no presenta
diferencias agregadas, tampoco por estrato. Esta coincidencia procede de
las nuevas puntuaciones humanas aceptadas y del cálculo del script; no se
adaptaron los resultados para reproducir las cifras históricas. Tampoco
implica que las respuestas sean textualmente idénticas o que la corrección
de las magnitudes absolutas fuese innecesaria.

## Cronología y evaluación 3 final

| Evaluación | Muestra | Cambio respecto a anterior | Resultado | Incidencia/limitación | Motivo de la siguiente evaluación |
|---|---|---|---|---|---|
| 1. Original; documentada 04/09/2026 | 20 casos, cuatro estratos de cinco; GPT-5.6-LUNA | Primera evaluación; adaptador SQL con ×1000 adicional | 95/96 = 98,96 %; C3 19/20; claridad 3,95/5 | Magnitudes absolutas incorrectas; fallo porcentual de case_006 | Corregir SQL y repetir sobre los mismos viajes |
| 2. Corrección SQL; cierre 03/10/2026 | Exactamente los mismos 20 viajes; GPT-5.6-LUNA, mismo prompt/workflow | Adaptador e inputs corregidos; repetición registrada | 95/96 = 98,96 %; claridad 3,95/5 | Único criterio incumplido registrado: C3 de case_006; su respuesta conservada usa absolutos antiguos | Política de calidad cambia la población comparable y exige reconstruir la muestra |
| 3. Final; documentada 04/10/2026 | 20 viajes nuevos, cero solapamientos; todos anteriores al 20/08; cuatro estratos de cinco; GPT-5.6-LUNA | Nueva población válida y selección determinista tras la política de calidad | 95/95 = 100 %; claridad 4,00/5; 25 N/A; 0 fallos registrados; 170 expresiones comprobadas y 0 discrepancias materiales | Muestra funcional; revisión con apoyo de ChatGPT, aceptación del autor y comprobación numérica con Codex; no evaluación humana independiente | No consta otra evaluación pendiente |

La discontinuidad de Consumo desde el 20/08 hace que el viaje histórico
case_006 deje de ser comparable para consumo bajo la política final. Temporal
se conserva; ese viaje no pertenece a la nueva muestra. Los case_id se reutilizan
como etiquetas locales: el case_006 final corresponde a otro viaje.

**La evaluación 3 no demuestra una mejora cuantitativa del modelo respecto
a la 2.** Cambian muestra, población válida y procedimiento de revisión.
La muestra final se reconstruyó por el cambio de política de calidad,
**no para mejorar la puntuación**. Wilson descriptivo de 95/95:
**[96,11 %, 100 %]**, sin interpretar los 95 criterios de 20 casos como
observaciones independientes.

Fuentes finales: `data/final_evaluation_2026_quality_exclusion_20261004/`,
`final_evaluation_quality_exclusion.json` y, en `conversational_sample/`,
cases.json, case_mapping_private.json, luna_evaluation_summary.json y
numeric_fidelity_verification.json. Véase también el
[informe de trazabilidad para memoria](informe-trazabilidad-para-memoria.md).

## Limitaciones y conservación de evidencia

**Temperatura, seed y snapshot exacto del modelo no están documentados.**
El export conservado tiene `options` y `builtInTools` vacíos; no permite
reconstruir todos los valores efectivos por defecto del proveedor. La
etiqueta GPT-5.6-LUNA de la salida es fija y no acredita por sí sola el
snapshot servido. Por ello, la repetición conserva el modelo, prompt y
workflow documentados, pero no demuestra reproducibilidad exacta del
servicio ni garantiza textos idénticos. La identidad del evaluador humano
no queda registrada en los artefactos disponibles.

Los ocho artefactos históricos de `data/conversational_evaluation/` permanecen
intactos, verificados mediante hashes durante la preparación y la importación.
La auditoría remota y la reevaluación corregida se conservan en sus carpetas
separadas bajo data/, fuera de Git. Este documento no incluye identificadores
reales de viajes, credenciales ni datos empresariales privados.

El cierre documental no modifica el motor, los scripts, el workflow ni los
artefactos bajo data/. La verificación del repositorio utiliza
`python -B -m unittest discover -s tests -v` y `git diff --check`.
