# Informe documental de trazabilidad para la memoria del TFM

Fecha: 4 de octubre de 2026. Preparación documental para LaTeX, sin nuevos
experimentos, llamadas al modelo, cambios al detector, parámetros o `data/`.
Las transcripciones y cifras proceden de archivos existentes. Los documentos
anteriores pueden describir evaluaciones históricas, que no deben confundirse
con la muestra conversacional definitiva tras la política de calidad.

Actualización documental: 5 de octubre de 2026. La cronología y la salvedad
de la segunda evaluación se detallan en la sección 8; no se cambian resultados
ni puntuaciones históricas.

## 1. Nueve intervalos exactos de distancia

`src/data_processing.py`, función `distance_range()`, recorre los límites
1, 2, 5, 10, 20, 50, 100 y 300 y selecciona el primero que satisface `d <= límite`.
La etiqueta restante corresponde a `d >300`. Por tanto, los extremos superiores
son cerrados y los inferiores de las clases siguientes son abiertos.

| Etiqueta literal | Expresión matemática, d en km | Uso contextual |
|---|---|---|
| `<= 1` | d ≤1; para viajes válidos de consumo: 0<d≤1 | Vehículo × este rango; temporal excluye d≤1 |
| `> 1 y <= 2` | 1<d≤2 | Vehículo × este rango |
| `> 2 y <= 5` | 2<d≤5 | Vehículo × este rango |
| `> 5 y <= 10` | 5<d≤10 | Vehículo × este rango |
| `> 10 y <= 20` | 10<d≤20 | Vehículo × este rango |
| `> 20 y <= 50` | 20<d≤50 | Vehículo × este rango |
| `> 50 y <= 100` | 50<d≤100 | Vehículo × este rango |
| `> 100 y <= 300` | 100<d≤300 | Vehículo × este rango |
| `> 300` | d>300 | Vehículo × este rango |

La función de rangos por sí sola no valida positividad; la normalización
rechaza distancias no positivas antes de admitir una observación analítica.
Las referencias contextualizan mediana y MAD por `(vehículo, rango)`;
si falta soporte, se utiliza la referencia del vehículo. El mínimo histórico
por vehículo se aplica antes de admitir sus contextos, por separado para cada
señal. Fuente documental: [configuración congelada](configuracion-congelada-validacion-2025.md);
comprobación directa: `src/data_processing.py`, `src/baseline.py` y
`src/temporal_detector.py`. Los nueve rangos también aparecen en
[baseline_eligible_by_range.csv](resultados-validacion-2025/baseline_eligible_by_range.csv).

## 2. Estrategias A, B30 y B50

- **A:** referencia del vehículo, sin contexto de distancia.
- **B30:** referencia vehículo × rango con ≥30 observaciones válidas;
  fallback al vehículo cuando no existe soporte contextual suficiente.
- **B50:** igual procedimiento, con ≥50 observaciones contextuales.

La comparación principal usa `baseline_eligible` de
[validation_2025.json](resultados-validacion-2025/validation_2025.json),
que incorpora el mínimo histórico por vehículo ≥100. No confundir cobertura
de referencia con evaluabilidad posterior del detector cuando MAD es cero.
La población de esta comparación son registros válidos de consumo, no todos
los viajes de 2025. Contexto/fallback se expresan sobre los evaluables; cobertura
total, sobre la población. P95/P99 se refieren a desviación relativa, en razón,
no a porcentajes ni al KPI absoluto.

| Estrategia | Poblacion | Evaluables | Cobertura % | Contextuales (n; %) | Fallback (n; %) | Sin referencia | P95 r | P99 r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 24597 | 23849 | 96.95897874 | 0; 0.00000000 | 0; 0.00000000 | 748 | 2.47908261 | 13.28254340 |
| B30 | 24597 | 23849 | 96.95897874 | 22166; 92.94310034 | 1683; 7.05689966 | 748 | 0.80463494 | 3.62842695 |
| B50 | 24597 | 23849 | 96.95897874 | 20386; 85.47947503 | 3463; 14.52052497 | 748 | 0.95788452 | 6.21531427 |


En A, el fallback registrado es cero porque la referencia directa es siempre
la del vehículo; los 23849 evaluables no son contextuales. En B30/B50,
contextuales + fallback = evaluables. El JSON también contiene
`baseline_original`, exploración sin el filtro ≥100: se reproduce por separado
para evitar mezclar denominadores.

| Estrategia | Poblacion | Evaluables | Cobertura % | Contextuales (n; %) | Fallback (n; %) | Sin referencia | P95 r | P99 r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 24597 | 23871 | 97.04842054 | 0; 0.00000000 | 0; 0.00000000 | 726 | 2.49142942 | 13.27877472 |
| B30 | 24597 | 23871 | 97.04842054 | 22166; 92.85744208 | 1705; 7.14255792 | 726 | 0.80765106 | 3.66106735 |
| B50 | 24597 | 23871 | 97.04842054 | 20386; 85.40069540 | 3485; 14.59930460 | 726 | 0.96061073 | 6.28995622 |


B30 mantiene la cobertura de B50, utiliza más contexto y presenta menores
colas observadas. Se seleccionó como compromiso de soporte y cobertura,
no como estrategia óptima ni prueba de mejor detección de ineficiencia real.
Fuente interpretativa: [auditoría 2025](auditoria-validacion-2025.md).

## 3. Reglas realmente evaluadas en 2025

El artefacto [candidates_eligible.csv](resultados-validacion-2025/candidates_eligible.csv)
contiene 16 candidatos de consumo con mínimo histórico ≥100. Todos los
operadores son estrictos `>`; r significa `relative_deviation` y z `robust_z`.

| Candidato | Criterio r | Criterio z | Operacion | N evaluables | Marcados | Tasa de marcado basal % |
|---|---|---|---|---:|---:|---:|
| D1_relative_gt_25pct | >0.25 | - | Individual | 23849 | 4347 | 18.22717934 |
| D1_relative_gt_50pct | >0.5 | - | Individual | 23849 | 2110 | 8.84733112 |
| D1_relative_gt_100pct | >1 | - | Individual | 23849 | 953 | 3.99597467 |
| D1_relative_gt_200pct | >2 | - | Individual | 23849 | 467 | 1.95815338 |
| D1_relative_gt_500pct | >5 | - | Individual | 23849 | 175 | 0.73378339 |
| D2_robust_z_gt_2 | - | >2.0 | Individual | 23849 | 2628 | 11.01932995 |
| D2_robust_z_gt_3 | - | >3.0 | Individual | 23849 | 1418 | 5.94574196 |
| D2_robust_z_gt_4 | - | >4.0 | Individual | 23849 | 912 | 3.82405971 |
| D2_robust_z_gt_5 | - | >5.0 | Individual | 23849 | 627 | 2.62904105 |
| D2_robust_z_gt_10 | - | >10.0 | Individual | 23849 | 229 | 0.96020798 |
| D3_AND_relative_gt_50pct_z_gt_2 | >0.5 | >2.0 | AND | 23849 | 1718 | 7.20365634 |
| D3_AND_relative_gt_100pct_z_gt_3 | >1 | >3.0 | AND | 23849 | 800 | 3.35443834 |
| D3_AND_relative_gt_200pct_z_gt_5 | >2 | >5.0 | AND | 23849 | 386 | 1.6185165 |
| D3_OR_relative_gt_50pct_z_gt_2 | >0.5 | >2.0 | OR | 23849 | 3020 | 12.66300474 |
| D3_OR_relative_gt_100pct_z_gt_3 | >1 | >3.0 | OR | 23849 | 1571 | 6.58727829 |
| D3_OR_relative_gt_200pct_z_gt_5 | >2 | >5.0 | OR | 23849 | 708 | 2.96867793 |


Los benchmarks completos de perturbaciones contienen un subconjunto de
12 candidatos: D1 con r>0,50/1/2; D2 con z>2/3/5; AND y OR para las parejas
(0,50;2), (1;3) y (2;5). Esto se verifica tanto en
[comparación consumo](resultados-validacion-2025/consumption_benchmark/synthetic_benchmark_rule_comparison.csv)
como en [comparación temporal](resultados-validacion-2025/temporal_benchmark/temporal_synthetic_benchmark_rule_comparison.csv).
Los cortes r>0,25, r>5, z>4 y z>10 están en la comparación de controles
de consumo; no se afirma que cuenten con el benchmark completo ni que se
hayan ensayado todas las combinaciones cartesianas.

Las cabeceras históricas `recall` y `specificity` se interpretan como tasa de
marcado tras perturbación y tasa de no marcado en controles. La tabla anterior
usa nomenclatura vigente. No existe ground truth empresarial. La regla final
r>0,50 AND z>2 es un compromiso seleccionado y congelado, no un ganador
automático ni un óptimo.

## 4. Configuración final seleccionada

B30; historia válida por vehículo ≥100; contexto ≥30; r>0,50 AND z>2;
escala robusta 1,4826 MAD. Temporal: distancia estrictamente >1 km tanto
en historia como en evaluación. Ausencia de referencia o MAD cero implica
NOT_EVALUABLE. Referencias finales 2024+2025; snapshot evaluado 2026.

Consumo comparativo únicamente antes del 20/08/2026. Desde esa fecha, el
lote afectado se trata como no comparable/no evaluable por calidad en la capa
de evaluación; no se modifica DetectorV1, la fuente ni se infiere unidad o causa.
Temporal conserva sus resultados cuando es evaluable. La exclusión es una
decisión posterior a observar 2026, no una garantía de validación prospectiva.

Los cortes 0,50 y 2 son un compromiso razonable respaldado por 2025, no
universales. El contexto 30 mantiene más uso contextual frente a 50. El mínimo
100 es un requisito conservador de diseño y no se ha demostrado que sea el
valor óptimo. Fuentes: [congelación](configuracion-congelada-validacion-2025.md),
[métricas finales y justificación](metricas-finales-benchmark.md).

## 5. Modelo y workflow conversacional formal

**Evaluación formal definitiva: GPT-5.6-LUNA.** El workflow versionado
`n8n/conversational_evaluation_v1.json` contiene `modelId.value = gpt-5.6-luna`
y `cachedResultName = GPT-5.6-LUNA`. Las 20 respuestas y fichas puntuadas
de la carpeta final registran GPT-5.6-LUNA. La etiqueta no identifica el
snapshot efectivamente servido por el proveedor.

**Prototipo operacional actual: gpt-5-mini, según la configuración comunicada
por el autor.** No se encontró en el repositorio un export de ese workflow
operacional ni una configuración que permita verificarlo directamente.
Debe presentarse separado del experimento formal; no se le atribuyen sus
métricas. Esta diferencia de modelo no se subsana cambiando retrospectivamente
la etiqueta del experimento.

El nodo «Message a model» recibe el System Prompt y, como mensaje de usuario,
la expresión literal `={{ JSON.stringify($json.analytical_result) }}`. El contenido
efectivo de cada mensaje es el resultado analítico completo serializado a JSON;
no es una pregunta libre sobre el viaje. Se procesan los 20 casos anonimizados
de la nueva muestra, 5 por estrato, con respuestas congeladas antes de puntuar.
Los identificadores case_001…case_020 se reutilizan, pero representan viajes
distintos de las muestras anteriores y no deben servir para unir evaluaciones.

La configuración exportada muestra `options: {}` y `builtInTools: {}`.
Temperatura, seed y snapshot exacto no están documentados; no se infieren sus
valores predeterminados ni se afirma reproducibilidad bit a bit. El workflow
es evidencia del procedimiento documentado, no un registro íntegro de la
ejecución remota final. Fuentes documentales de contexto:
[metodología](metodologia.md), [estado histórico](estado-validado-v1.md),
[auditoría conversacional anterior](auditoria-correccion-conversacional.md).
Estas fuentes no certifican por sí solas las métricas de la nueva muestra.

## 6. System Prompt exacto para el anexo

Fuente literal:
`data/final_evaluation_2026_quality_exclusion_20261004/conversational_sample/prompt_original.txt`.
Coincide con el System Prompt del workflow versionado, ignorando únicamente
el salto final de archivo. Es el prompt conservado para la ejecución final y
el procedimiento confirmado por el autor. No existe un log remoto con hash
del mensaje efectivamente enviado que permita certificarlo de forma independiente.
La transcripción siguiente no se reconstruye ni se parafrasea.

```text
Eres un asistente de apoyo al análisis logístico.

Tu función es explicar resultados producidos por un sistema analítico determinista. No debes decidir por tu cuenta si existe una anomalía o ineficiencia.

Reglas obligatorias:
- Respeta exactamente overall_status y el status de cada señal.
- REVIEW significa que existe una desviación que requiere revisión, no una ineficiencia confirmada.
- NO_RELEVANT_DEVIATION significa que no se han cumplido los criterios definidos para marcar una desviación relevante.
- NOT_EVALUABLE significa que esa señal no ha podido evaluarse.
- No inventes causas.
- No atribuyas resultados a tráfico, averías, conductor, carga, ruta, clima u otros factores si los datos proporcionados no los demuestran.
- No afirmes que una desviación implica causalidad.
- Explica consumo y señal temporal por separado cuando sean evaluables.
- La señal temporal representa minutos por kilómetro respecto al histórico comparable; no la denomines "tiempo de parada".
- Utiliza lenguaje profesional, claro y breve.
- Expresa las desviaciones relativas como porcentajes comprensibles.
- Indica que las referencias corresponden al comportamiento histórico utilizado por el sistema.
```

## 7. Rúbrica exacta para el anexo

La definición operativa detallada procede literalmente de
[metodologia.md](metodologia.md), apartado «Evaluación de fidelidad y utilidad
de las explicaciones del LLM». El esquema original es
`evaluation/rubric_template.json`. Se transcriben las reglas, incluido el
matiz original de C1/C4: aunque el esquema admite N/A, la definición establece
que siempre deben evaluarse.

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

`null` significa pendiente/no puntuado; no significa N/A. El esquema permite
1, 0, null y N/A en criterios, y 1–5 o null en claridad. En la importación final
se exige puntuar cada criterio con 1/0/N/A y claridad con entero 1–5. El
resumen cuenta aplicables como 1+0, excluye N/A y cuenta null por separado.
Por criterio: 100×cumplimientos/aplicables. Global: 100×suma de cumplimientos
de todos los criterios/suma de aplicables, sin promediar porcentajes por caso
ni incorporar claridad. Claridad: media de las valoraciones no null.
Fuente de cálculo: `evaluation/summarize_llm_evaluation.py`; importación:
`evaluation/import_llm_review_scores.py`.

## 8. Resultado conversacional definitivo

| Criterio | Cumplen / aplicables | N/A | Fallos |
|---|---:|---:|---:|
| C1_global_status | 20/20 | 0 | 0 |
| C2_signal_statuses | 20/20 | 0 | 0 |
| C3_numeric_fidelity | 20/20 | 0 | 0 |
| C4_no_unsupported_causes | 20/20 | 0 | 0 |
| C5_no_confirmed_inefficiency_claim | 5/5 | 15 | 0 |
| C6_not_evaluable_and_coverage | 10/10 | 10 | 0 |

20 casos evaluados; **95/95 criterios aplicables = 100 %**; **25 N/A**; **0 fallos**; 0 criterios sin puntuar; **claridad media 4,00/5**.


La muestra definitiva contiene 20 viajes distintos anteriores al 20/08/2026,
sin coincidencias con la muestra anterior: 5 NO_RELEVANT_DEVIATION_COMPLETE,
5 REVIEW_COMPLETE, 5 NOT_EVALUABLE_NONE y 5 PARTIAL. Los valores 98,96 %,
95/96, 3,95/5 y C3=95 % son históricos y han sido sustituidos para la memoria.

La comprobación mecánica existente registra 170 expresiones numéricas
contrastadas en 20 respuestas y 0 discrepancias materiales, con redondeo
razonable y comparación de desviaciones como porcentajes. No es una medida
de detección real de ineficiencia ni una evaluación de otra población.

### Cronología de las tres evaluaciones

| Evaluación | Muestra | Cambio respecto a anterior | Resultado | Incidencia/limitación | Motivo de la siguiente evaluación |
|---|---|---|---|---|---|
| 1. Original; documentada 04/09/2026, commit 42b6a7e | 20 casos, cuatro estratos de cinco; GPT-5.6-LUNA | Primera evaluación con adaptador SQL que multiplicaba adicionalmente ×1000 | 95/96 = 98,96 %; C3 19/20; claridad 3,95/5 | Absolutos de consumo incorrectos; un criterio incumplido registrado en case_006 | Corrección del adaptador y repetición sobre los mismos viajes |
| 2. Corrección SQL; cierre documental 03/10/2026, commit 64d1079 | Exactamente los mismos 20 viajes; GPT-5.6-LUNA, mismo prompt/workflow | Adaptador corregido y resultados analíticos reconstruidos | 95/96 = 98,96 %; claridad 3,95/5 | C3 de case_006: único criterio incumplido registrado; respuesta conservada con magnitudes absolutas antiguas pese a analytical_result corregido | Cambio posterior de política de calidad y reconstrucción de la muestra sobre población comparable |
| 3. Final; documentada 04/10/2026, ejecución sin commit inequívocamente registrado | 20 viajes completamente nuevos; cero solapamientos; anteriores al 20/08; cuatro estratos de cinco | Nueva población válida, nueva muestra y procedimiento de revisión | 95/95 = 100 %; claridad 4,00/5; 25 N/A; 0 fallos registrados; 170 expresiones comprobadas; 0 discrepancias materiales | Apoyo de ChatGPT, validación/aceptación del autor y comprobación mecánica numérica con Codex; no evaluador humano independiente | No consta repetición pendiente |

La evidencia de reconstrucción de las evaluaciones 1–2 es la auditoría SQL:
20/20 UNIQUE_MATCH, 20 viajes distintos, mismos estratos y orden. Las métricas
relativas y estados permanecieron invariantes en los casos reconstruidos,
aunque el bug alteraba magnitudes absolutas de consumo en 11 casos evaluables.

### case_006 histórico y salvedad de la evaluación 2

Fecha: **25/08/2026**; distancia: **12,782 km**, rango >10 y ≤20 km.
**No era un viaje corto.** Relative_deviation corregida:
`1189.5972035437394`; porcentaje correcto ≈**118959,72 %**.
Luna expresó ≈**1189,6 %**; puntuación registrada C3=0 y claridad=3/5.
Es un fallo de verbalización generativa, no del estado calculado por el detector.

Además, la respuesta de case_006 conservada en
`data/conversational_evaluation_corrected/luna_responses.json` y
`luna_evaluation_scored.json` expresa 905 litros, 7080,27 L/100 km y baseline
5,95 L/100 km. El analytical_result asociado registra respectivamente
0,905 litros, 7,080269128461899 y 0,005946821567687135 L/100 km.
Por eso **no se describe la evaluación 2 como regeneración completamente
limpia**. Se preservan su resultado histórico y puntuaciones, con esta salvedad.

El viaje deja de ser comparable para consumo bajo la política final por
pertenecer al lote desde el 20/08, cuya discontinuidad no debe confundirse con
el bug del adaptador. No pertenece a la muestra 3; el case_006 final es otro viaje.

### Bug del adaptador y alcance de la invariancia

`src/sql_repository.py`, `_to_analytical_row()`: la transformación antigua
`float(consumption_liters) * 1000` se corrigió eliminando la multiplicación
adicional antes de la normalización. Commit:
`77e4bb54efc6827713ef3ce7123f29f9241e92d4`.
Un factor positivo común k cancela en `(kx−km)/(km)` y en
`(kx−km)/(1,4826·k·MAD)`, conservando relative_deviation y robust_z y,
en los casos auditados, estados, cobertura y señales de revisión. Las magnitudes
absolutas entregadas al componente conversacional eran incorrectas; esta
invariancia no equivale a ausencia general de efecto.

**La evaluación 3 no demuestra una mejora cuantitativa del modelo respecto
a la 2.** Cambian la muestra, la población válida y el procedimiento de revisión.
La selección final se reconstruyó por la política de calidad, **no para mejorar
la puntuación**.

Fuentes: [auditoría histórica y salvedad](auditoria-correccion-conversacional.md);
los resúmenes luna_evaluation_summary.json en las carpetas original y corregida;
comparison.json y case_mapping_private.json de la auditoría SQL; y los
artefactos finales citados en la sección 14. Las fechas de documentación no
acreditan el instante exacto de ejecución remota.

## 9. Wilson bilateral descriptivo al 95 %

Para x=95, n=95 y z=1,95996398454, p=x/n:

`centro = (p + z^2/(2n))/(1 + z^2/n)`

`semiancho = z*sqrt(p*(1-p)/n + z^2/(4n^2))/(1 + z^2/n)`

Intervalo [centro-semiancho, centro+semiancho], es decir **96.11351465 % a 100.00000000 %**, aproximadamente **96,1 % a 100 %**.

Se denomina **«intervalo descriptivo calculado sobre los criterios aplicables»**.
Redondeado a dos decimales para 95/95: **[96,11 %, 100 %]**.
Para el resultado histórico 95/96, el Wilson bilateral 95 % es aproximadamente
**[94,33 %, 99,82 %]**, también descriptivo.
Los 95 criterios proceden de 20 casos y no deben interpretarse como 95
observaciones independientes que permitan generalizar el rendimiento real del
modelo. La muestra es funcional y estratificada; las puntuaciones de un mismo
caso pueden estar correlacionadas. El intervalo no resuelve dependencia,
selección de casos ni sesgo del procedimiento de revisión.

## 10. Quién realizó la evaluación: redacción académica

«Las respuestas de la muestra conversacional definitiva se revisaron con
apoyo de ChatGPT. El autor del TFM validó y aceptó las puntuaciones finales
de la rúbrica y de claridad. Antes de incorporarlas al pipeline, Codex realizó
una comprobación mecánica de fidelidad numérica contra los resultados
analíticos completos, admitiendo diferencias razonables de redondeo. Codex
se utilizó como herramienta de comprobación y procesamiento, no como
evaluador humano independiente. No se realizó una evaluación interjueces
independiente ni se midió concordancia entre evaluadores.»

La descripción del apoyo de ChatGPT y de la aceptación por el autor procede
de su declaración para este informe. El artefacto numérico registra la
comprobación y el origen de las puntuaciones; no acredita un evaluador externo.

## 11. Tag y commits: significado y límites

`v1.0-tfm` es un tag anotado. Objeto tag:
`3e8dca8093b0b69fb362532cd3f99a4afe2de84a`.
**Commit al que apunta:** `7b5e57c44c699996016590b7430d1b0f9e60a505`
(7/09/2026), «Add validated prototype v1 state for thesis writing».
`git rev-parse v1.0-tfm` devuelve el objeto tag; para el commit se usó
`git rev-parse 'v1.0-tfm^{commit}'`.

| Etapa | Evidencia Git | Qué acredita / qué no acredita |
|---|---|---|
| A. Versión del motor analítico | Tag v1.0-tfm, commit 7b5e57c4… | Snapshot histórico del prototipo y sus resultados documentados; no acredita la nueva muestra final ni su ejecución Luna |
| Corrección posterior del adaptador | 77e4bb5, «Fix SQL consumption unit normalization» | Corrección SQL posterior al tag; no debe confundirse adaptador con cambio de regla del detector |
| B. Congelación metodológica | fdde83d9ee5744b72d044e6628ee85db619c264e, «Freeze methodology using 2024-2025 validation» (2/10/2026) | Protocolo, validación 2025 y configuración congelada; no elimina exposición exploratoria previa a 2026 |
| C. Ejecución conversacional definitiva | Artefactos privados finales y workflow documentado | Modelo etiquetado, respuestas y puntuaciones; **no registran el HEAD/commit de ejecución**, por lo que no puede determinarse inequívocamente |
| D. Cambios posteriores de evaluación/documentación | a3ddcb76c6873c934cd6fc538717d50acd636b62, «Refine benchmark metrics and operational workload» | Nomenclatura y cálculo emparejado del benchmark, tests y documentación; no versión original de generación de las respuestas ni cambio del detector |

Entre el commit del tag y el HEAD actual, `src/detector.py`,
`src/temporal_detector.py`, `src/baseline.py` y `src/data_processing.py` no
presentan diferencias; sí hay cambios de API y adaptador SQL. Entre la
congelación y el HEAD tampoco cambian esos cuatro archivos analíticos.
Eso respalda continuidad del código analítico, no identidad completa de
fuentes, políticas de preparación o ejecución conversacional.

La nueva política de calidad y sus resultados privados son posteriores al
tag. No se atribuye la evaluación conversacional definitiva a v1.0-tfm,
fdde83d o a3ddcb7 sin evidencia de ejecución. Las fechas de archivos o el
HEAD conocido durante esta revisión no reemplazan un manifiesto de ejecución.
Fuente documental histórica: [estado-validado-v1.md](estado-validado-v1.md);
congelación: [configuracion-congelada-validacion-2025.md](configuracion-congelada-validacion-2025.md).
Los hashes anteriores se verificaron directamente mediante Git.

## 12. Qué incorporar al cuerpo de la memoria

Los nueve rangos y su función contextual; comparación A/B30/B50 con
denominadores explícitos; resumen de candidatos y configuración congelada
sin optimalidad; separación del motor determinista y el modelo generativo;
modelo formal Luna frente al prototipo operacional; resumen C1–C6; resultados
finales 95/95 y claridad 4,00; intervalo descriptivo con su dependencia entre
criterios; procedimiento real de revisión; límites del snapshot y de Git.
Usar las tasas vigentes de [metricas-finales-benchmark.md](metricas-finales-benchmark.md),
sin trasladar cabeceras antiguas como nombres finales.

## 13. Qué incorporar a anexos

System Prompt íntegro de la sección 6; rúbrica íntegra de la sección 7 y
valores permitidos; tabla completa de candidatos; tabla A/B30/B50 exacta
con separación de ámbitos; workflow sanitizado y trazabilidad de archivos,
sin credenciales, identificadores de viajes ni datos empresariales privados.
Las respuestas solo se incluyen si su anonimización y divulgación se autorizan;
este informe no las publica ni transcribe.

## 14. Mapa de fuentes y discrepancias documentales

| Dato | Fuente en docs/ | Evidencia primaria complementaria |
|---|---|---|
| Rangos y referencia contextual | resultados-validacion-2025/baseline_eligible_by_range.csv; configuracion-congelada-validacion-2025.md | src/data_processing.py y src/baseline.py |
| A/B30/B50 | resultados-validacion-2025/validation_2025.json: baseline_eligible y baseline_original.strategies | scripts/evaluate_baseline_strategies.py |
| 16 candidatos controles / 12 benchmark | resultados-validacion-2025/candidates_eligible.csv y comparaciones consumption_benchmark/temporal_benchmark | scripts/evaluate_detector_candidates.py y benchmarks |
| Configuración y límites | configuracion-congelada-validacion-2025.md; metricas-finales-benchmark.md | Código analítico vigente |
| Modelo, workflow y prompt históricos | metodologia.md; estado-validado-v1.md; auditoria-correccion-conversacional.md | n8n/conversational_evaluation_v1.json y prompt_original.txt final |
| Rúbrica exacta | metodologia.md | evaluation/rubric_template.json y summarize_llm_evaluation.py |
| Nueva evaluación definitiva y chequeo numérico | **Este informe**, extracción documental de fuentes finales | luna_evaluation_scored.json, luna_evaluation_summary.json y numeric_fidelity_verification.json de la carpeta final |
| Wilson y procedimiento real | **Este informe**; declaración del autor | Cálculo descriptivo 95/95; no nuevo experimento |
| Git | estado-validado-v1.md; documento de congelación; este informe | Comprobación directa de tag y commits |

Carpeta primaria final:
`data/final_evaluation_2026_quality_exclusion_20261004/conversational_sample/`.
Sus artefactos no se modificaron. `metodologia.md` y `estado-validado-v1.md`
conservan cifras de evaluaciones históricas. La auditoría conversacional se
actualiza documentalmente para distinguir su cierre anterior, la salvedad de
case_006 y la nueva evaluación final. No se cambian sus puntuaciones ni fuentes
históricas. Este informe explicita la sucesión y las cifras vigentes.

No se dispone de una fuente dentro de docs/ que verifique de forma independiente
el export operacional gpt-5-mini, el snapshot remoto o el HEAD de la generación
final. Esas lagunas se declaran, no se completan por inferencia.
