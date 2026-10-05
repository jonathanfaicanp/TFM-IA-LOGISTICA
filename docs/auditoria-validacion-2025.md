# Auditor?a y validaci?n retrospectiva 2024 ? 2025

> Nota de nomenclatura revisada (04/10/2026): las menciones históricas a
> «especificidad»/`specificity` y «recall» describen respectivamente tasa de no
> marcado en controles y tasa de marcado tras perturbación, sin ground truth
> real. Se conservan como trazabilidad; para resultados finales y detección
> incremental véase [Métricas finales](metricas-finales-benchmark.md). El término
> «sensibilidad» en análisis de parámetros conserva su sentido metodológico.


Se completan las fases 1?5. **La selecci?n sigue pendiente; no se ha ejecutado una nueva evaluaci?n de 2026 y no hay configuraci?n final congelada.** Se conserva el motor productivo. No se ha hecho commit ni push.

Esta reconstrucci?n utiliza solo 2024 para las referencias y 2025 para las m?tricas nuevas. No elimina la exposici?n hist?rica a 2026 ni puede presentar ese a?o como un test prospectivamente intacto. El protocolo previo est? en [protocolo-validacion-2025.md](protocolo-validacion-2025.md).

## Auditor?a con evidencia

B significa estudiada o seleccionada mirando 2026, no necesariamente que podamos probar que 2026 fue su ?nica fuente. C significa que no se puede acreditar una selecci?n exclusivamente anterior a 2026. La presencia de un script acredita su dise?o; los documentos y artefactos locales aportan evidencia adicional de experimentos realizados. Los tests verifican contratos, no reconstruyen el criterio de selecci?n.

| Decisi?n | Clase | Evidencia y alcance |
| --- | --- | --- |
| A por veh?culo frente a contexto | B | `evaluate_baseline_strategies.py` usa 2024?2025, pero `evaluate_2026_baseline_strategies.py` compara las mismas estrategias sobre 2026. `decision-log.md`, evoluci?n A/B30/B50, y versi?n `7e7abe4` documentan preferencia todav?a provisional despu?s de esas evaluaciones. |
| B30 frente a B50 | B | Mismos scripts y documento. Haber hecho tambi?n 2024?2025 no acredita selecci?n exclusiva sin 2026. |
| M?nimo hist?rico 100 | C | `6aa96d0:docs/decision-log.md`, criterio inicial, fija 100 y permite revisarlo tras estudiar estabilidad; `analyze_distance_ranges.ps1` y `DistanceRangeAggregation.cs` aplican 100 solo sobre 2024?2025. No consta comparaci?n de m?nimos ni prueba de informaci?n exclusivamente anterior a 2026: la exploraci?n inicial ya inclu?a los tres a?os. No se demuestra selecci?n por m?tricas de 2026 ni selecci?n independiente de ellas. |
| M?nimo contextual 30 | B | Es el par?metro de B30 comparado con B50 en 2026. `analyze_b30_mad.py` y `analyze_duration_distance_feasibility.py` examinan cobertura/viabilidad con 30 sobre 2026. |
| Regla relativa D1 | B | `evaluate_detector_candidates.py`, cinco cortes en controles de 2026; `evaluate_synthetic_benchmark.py`, perturbaciones del mismo a?o. |
| Regla robust z D2 | B | Mismos scripts; `analyze_b30_mad.py` y `analyze_b30_mad_extremes.py` analizan sus colas en 2026. |
| AND/OR | B | `scenario_definitions()` y `RULES` en candidatos y ambos benchmarks; los cargadores originales construyen 2024?2025 y eval?an 2026. |
| relative_deviation >0,50 | B | `b65716e:docs/decision-log.md`, decisi?n provisional del detector, justifica la candidata con resultados semi-sint?ticos de 2026. `8192152` la declara definitiva. |
| robust_z >2 | B | Misma justificaci?n y comparaci?n con 3 y 5; el documento hist?rico dice expresamente que las distribuciones no justificaban por s? mismas un corte. |
| Distancia temporal >1 km | B | `analyze_temporal_robustness.py` compara <=1 y >1 sobre 2026; `8192152:docs/decision-log.md`, DetectorTemporalV1, usa inestabilidad del primer grupo para excluirlo. `analyze_duration_distance_feasibility.py` mezcla los tres a?os en distribuciones por rango. |

No hay decisi?n de esta lista para la que pueda acreditarse la categor?a A en su sentido estricto de **selecci?n exclusivamente sin informaci?n de 2026**. El m?nimo 100 s? tiene antecedentes aplicados a hist?rico; eso no prueba su procedencia exclusiva.

Otras decisiones: mediana/MAD y factor 1,4826 fueron estudiados sobre 2026 (`analyze_b30_mad.py`, categor?a B para su estudio); elegir `minutes_per_km` frente a duraci?n tambi?n recibi? evidencia de los tres a?os (`analyze_duration_distance_feasibility.py`, B). Los rangos de distancia, el tratamiento de consumo no positivo, el m?nimo 100 exacto y la pol?tica MAD cero no tienen una comparaci?n de alternativas que permita reconstruir su selecci?n (C). La divisi?n temporal se document? con exploraci?n de los tres a?os y una afirmaci?n externa de mayor fiabilidad de 2026 (B en cuanto al contexto informado; no es prueba estad?stica de calidad). La sem?ntica REVIEW y la consolidaci?n tienen motivaci?n funcional documentada, sin evidencia de optimizaci?n por m?tricas de 2026; no se les atribuye una selecci?n experimental inventada.

## Disponibilidad de scripts antes de esta correcci?n

| Script | A?os originales / 2026 hardcodeado | Uso directo 2024?2025 | Cambio necesario / realizado |
| --- | --- | --- | --- |
| evaluate_baseline_strategies.py | 2024 referencia, 2025 validaci?n; no 2026 como evaluaci?n | S? | Sin cambios; no exige 100 |
| compare_baselines.py | 2024?2025, descriptivo hist?rico | No separa validaci?n | Sin cambios, no imprescindible |
| analyze_distance_ranges.ps1 / DistanceRangeAggregation.cs | 2024?2025, hist?rico >=100 | No separan validaci?n | Sin cambios |
| evaluate_2026_baseline_strategies.py | 2024?2025?2026; s? | No | Parametrizaci?n posible; no necesario, se reutiliza el comparador de 2025 |
| evaluate_detector_candidates.py | 2024?2025?2026; s? | No | Parametrizados cargador, run, CLI y nombres de salida; no exige 100 originalmente |
| analyze_distance_threshold_sensitivity.py | 2024?2025?2026; s? | No | Misma parametrizaci?n; analiza consumo, no temporal |
| analyze_b30_mad.py | 2024?2025?2026; s? | No | Misma parametrizaci?n; no exige 100 originalmente |
| analyze_temporal_robustness.py | 2024?2025?2026; s? | No | Parametrizados a?os y claves del resumen; exige 100, incluye distancias cortas |
| evaluate_synthetic_benchmark.py | 2024?2025?2026; s? | No | Parametrizados a?os; nombres gen?ricos conservados, salida aislada; exige 100 |
| evaluate_temporal_synthetic_benchmark.py | 2024?2025?2026; s? | No | Parametrizados a?os; exige 100 y >1 en hist?rico y evaluaci?n |
| analyze_duration_distance_feasibility.py | 2024,2025,2026; s? | No: mezcla distribuciones y eval?a cobertura 2026 | Sin modificar; reutilizadas transformaciones/estad?sticas por los otros scripts |
| analyze_b30_2026_deviations.py / analyze_b30_mad_extremes.py | 2024?2025?2026; s? | No | No imprescindibles: sus funciones de concentraci?n/c?lculo ya est?n reutilizadas en candidatos |
| profile_dataset.py | CSV completo, sin separaci?n de selecci?n | No | No ejecutado: exploraci?n global no corresponde al protocolo |

Scripts nuevos: `experimental_split.py` valida hist?rico no vac?o, sin duplicados, estrictamente anterior a evaluaci?n; `validate_methodology_2025.py` coordina las funciones existentes. Los seis scripts parametrizados mantienen 2024?2025?2026 como valor predeterminado. El ejecutor fija 2024?2025 y escribe rutas separadas. No se cambiaron reglas, umbrales, f?rmulas ni src/.

## Protocolo y reproducibilidad

No existe funci?n objetivo de selecci?n ni prioridad/desempate demostrable. S? hay criterios cualitativos documentados: uso contextual con fallback, dispersi?n y cobertura, y compromiso tasa marcada/recall semi-sint?tico. Las m?tricas balanced accuracy y Youden existen en los comparadores, pero su presencia no acredita que se utilizaran como objetivo. Se informan sin convertirlas en una nueva regla de elecci?n.

```powershell
python scripts/validate_methodology_2025.py --input data/datos_operativa.csv --output-dir data/validation_2025
python -m unittest discover -s tests -v
```

Tambi?n pueden ejecutarse individualmente los scripts parametrizados con `--history-years 2024 --evaluation-year 2025 --output-dir data/otra_validacion_2025` (robustez temporal imprime JSON y no tiene output-dir). No ejecutar sus valores predeterminados para esta fase. El protocolo qued? escrito antes de ejecutar las m?tricas.

CSV fuente SHA-256: `5acee0912132de006bf31c8657f6703b7ff568cc7b5aa94e6b4c81a25f6f8fdf`. Python 3.14.3. Datos originales le?dos sin modificaci?n. Resultados completos y precisi?n de ocho decimales: [validation_2025.json](resultados-validacion-2025/validation_2025.json). Las copias del informe contienen agregados, sin trayectos ni identidades de veh?culos.

## Baselines

Hist?rico 2024: 14886 registros v?lidos de consumo, 23 veh?culos. Con >=100: 14837 registros y 22 veh?culos. Un veh?culo con 49 observaciones queda fuera. Contextos elegibles >=30: 119; >=50: 100. Validaci?n: 24.597 registros v?lidos de consumo.

### Exploraci?n original sin m?nimo 100

| strategy | evaluable_records | records_without_baseline | coverage_pct | contextual_evaluations | fallback_evaluations | contextual_evaluations_pct | fallback_evaluations_pct | evaluated_vehicles | vehicles_with_fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 23871 | 726 | 97.04842054 | 0 | 0 | 0.0 | 0.0 | 23 | 0 |
| B30 | 23871 | 726 | 97.04842054 | 22166 | 1705 | 92.85744208 | 7.14255792 | 23 | 20 |
| B50 | 23871 | 726 | 97.04842054 | 20386 | 3485 | 85.4006954 | 14.5993046 | 23 | 22 |

| strategy | deviation_median | deviation_p75 | deviation_p90 | deviation_p95 | deviation_p99 | over_25pct | over_50pct | over_100pct | over_200pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.00587916 | 0.28584914 | 1.02338623 | 2.49142942 | 13.27877472 | 6450 | 4079 | 2430 | 1438 |
| B30 | 0.00412149 | 0.16865124 | 0.44981819 | 0.80765106 | 3.66106735 | 4356 | 2116 | 957 | 471 |
| B50 | 0.00345449 | 0.17915155 | 0.49268293 | 0.96061073 | 6.28995622 | 4614 | 2360 | 1156 | 646 |

### Comparaci?n aplicando el m?nimo 100 actual

| strategy | evaluable_records | records_without_baseline | coverage_pct | contextual_evaluations | fallback_evaluations | contextual_evaluations_pct | fallback_evaluations_pct | evaluated_vehicles | vehicles_with_fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 23849 | 748 | 96.95897874 | 0 | 0 | 0.0 | 0.0 | 22 | 0 |
| B30 | 23849 | 748 | 96.95897874 | 22166 | 1683 | 92.94310034 | 7.05689966 | 22 | 19 |
| B50 | 23849 | 748 | 96.95897874 | 20386 | 3463 | 85.47947503 | 14.52052497 | 22 | 21 |

| strategy | deviation_median | deviation_p75 | deviation_p90 | deviation_p95 | deviation_p99 | over_25pct | over_50pct | over_100pct | over_200pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.00583446 | 0.28568124 | 1.02218189 | 2.47908261 | 13.2825434 | 6441 | 4073 | 2426 | 1434 |
| B30 | 0.00408597 | 0.16854383 | 0.44903203 | 0.80463494 | 3.62842695 | 4347 | 2110 | 953 | 467 |
| B50 | 0.00340547 | 0.17899091 | 0.49211691 | 0.95788452 | 6.21531427 | 4605 | 2354 | 1152 | 642 |

A usa referencia por veh?culo: sus usos generales no se denominan fallback. B30 conserva 96,959 % de cobertura, usa 92,943 % de contexto frente a 85,479 % de B50 y reduce p95/p99 respecto a A y B50. Esto respalda B30 seg?n los criterios cualitativos originales; no demuestra que 30 sea un m?nimo estad?stico ?ptimo. El m?nimo 100 excluye 49 registros hist?ricos y 22 registros de validaci?n antes evaluables; no hay un barrido documentado que justifique exactamente 100.

## Reglas reales de consumo: todos los candidatos

Sin etiquetas reales, porcentaje marcado no es tasa de error empresarial. La tabla aplica hist?rico elegible >=100; los resultados originales sin ese m?nimo se conservan por separado. D2/D3 excluyen MAD cero antes de evaluar incluso OR, seg?n el script original.

| scenario | family | relative_threshold | robust_z_threshold | operation | records_evaluable | records_marked | marked_pct | vehicles_affected | vehicles_for_at_least_50pct_of_marked | pct_marked_distance_lte_1km | pct_marked_distance_gt_5km | pct_marked_distance_gt_20km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_relative_gt_25pct | D1 | 0.25 | ? | ? | 23849 | 4347 | 18.22717934 | 22 | 6 | 35.68914162 | 13.39544253 | 12.80055183 |
| D1_relative_gt_50pct | D1 | 0.5 | ? | ? | 23849 | 2110 | 8.84733112 | 22 | 6 | 28.13430815 | 4.04758907 | 3.9613717 |
| D1_relative_gt_100pct | D1 | 1 | ? | ? | 23849 | 953 | 3.99597467 | 22 | 6 | 19.55050095 | 0.45322926 | 0.30547891 |
| D1_relative_gt_200pct | D1 | 2 | ? | ? | 23849 | 467 | 1.95815338 | 22 | 5 | 11.39994584 | 0.04406396 | 0.00985416 |
| D1_relative_gt_500pct | D1 | 5 | ? | ? | 23849 | 175 | 0.73378339 | 20 | 4 | 4.65746006 | 0.0 | 0.0 |
| D2_robust_z_gt_2 | D2 | ? | 2.0 | ? | 23849 | 2628 | 11.01932995 | 22 | 6 | 21.17519632 | 8.23995971 | 8.73078439 |
| D2_robust_z_gt_3 | D2 | ? | 3.0 | ? | 23849 | 1418 | 5.94574196 | 22 | 6 | 15.86785811 | 3.28591212 | 3.49822625 |
| D2_robust_z_gt_4 | D2 | ? | 4.0 | ? | 23849 | 912 | 3.82405971 | 22 | 6 | 13.07879773 | 1.44781569 | 1.52739456 |
| D2_robust_z_gt_5 | D2 | ? | 5.0 | ? | 23849 | 627 | 2.62904105 | 22 | 6 | 10.3168156 | 0.67354904 | 0.62081198 |
| D2_robust_z_gt_10 | D2 | ? | 10.0 | ? | 23849 | 229 | 0.96020798 | 22 | 4 | 5.17194693 | 0.05665366 | 0.04927079 |
| D3_AND_relative_gt_50pct_z_gt_2 | D3 | 0.5 | 2.0 | AND | 23849 | 1718 | 7.20365634 | 22 | 5 | 21.14811806 | 3.39921944 | 3.18289318 |
| D3_AND_relative_gt_100pct_z_gt_3 | D3 | 1 | 3.0 | AND | 23849 | 800 | 3.35443834 | 22 | 6 | 15.67831032 | 0.4091653 | 0.26606228 |
| D3_AND_relative_gt_200pct_z_gt_5 | D3 | 2 | 5.0 | AND | 23849 | 386 | 1.6185165 | 22 | 5 | 9.26076361 | 0.04406396 | 0.00985416 |
| D3_OR_relative_gt_50pct_z_gt_2 | D3 | 0.5 | 2.0 | OR | 23849 | 3020 | 12.66300474 | 22 | 6 | 28.16138641 | 8.88832935 | 9.50926291 |
| D3_OR_relative_gt_100pct_z_gt_3 | D3 | 1 | 3.0 | OR | 23849 | 1571 | 6.58727829 | 22 | 6 | 19.74004874 | 3.32997608 | 3.53764289 |
| D3_OR_relative_gt_200pct_z_gt_5 | D3 | 2 | 5.0 | OR | 23849 | 708 | 2.96867793 | 22 | 6 | 12.45599783 | 0.67354904 | 0.62081198 |

## Benchmarks de validaci?n: todos los candidatos

Perturbaciones originales +25, +50, +100, +200 y +500 %, sin alterar referencias. Consumo exige >=100; temporal exige >=100 y >1 km en ambas particiones. Estos benchmarks son de **2025**, no nuevas evaluaciones finales de 2026.

### consumption_benchmark

| scenario | control_marked_pct_experimental | specificity_pct_experimental | recall_pct_plus_25 | recall_pct_plus_50 | recall_pct_plus_100 | recall_pct_plus_200 | recall_pct_plus_500 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 8.84733112 | 91.15266888 | 22.00092247 | 50.80296868 | 90.75013627 | 98.52404713 | 99.73583798 |
| D1_relative_gt_100pct | 3.99597467 | 96.00402533 | 7.14495367 | 13.69449453 | 50.79877563 | 95.06897564 | 99.57650216 |
| D1_relative_gt_200pct | 1.95815338 | 98.04184662 | 2.85965869 | 3.99597467 | 8.84733112 | 50.80296868 | 98.52404713 |
| D2_robust_z_gt_2 | 11.01932995 | 88.98067005 | 39.46496708 | 67.70514487 | 88.84229947 | 96.48622584 | 99.2913749 |
| D2_robust_z_gt_3 | 5.94574196 | 94.05425804 | 22.9485513 | 50.044027 | 81.15224957 | 93.71462116 | 98.86368401 |
| D2_robust_z_gt_5 | 2.62904105 | 97.37095895 | 7.71101514 | 23.31334647 | 60.44697891 | 87.55084071 | 97.61834878 |
| D3_AND_relative_gt_50pct_z_gt_2 | 7.20365634 | 92.79634366 | 19.11191245 | 47.28919452 | 87.08121934 | 96.47364669 | 99.2913749 |
| D3_AND_relative_gt_100pct_z_gt_3 | 3.35443834 | 96.64556166 | 6.32311627 | 12.49947587 | 49.06285379 | 92.98083777 | 98.85529792 |
| D3_AND_relative_gt_200pct_z_gt_5 | 1.6185165 | 98.3814835 | 2.48228437 | 3.53893245 | 8.23095308 | 49.71277622 | 97.51352258 |
| D3_OR_relative_gt_50pct_z_gt_2 | 12.66300474 | 87.33699526 | 42.35397711 | 71.21891903 | 92.5112164 | 98.53662627 | 99.73583798 |
| D3_OR_relative_gt_100pct_z_gt_3 | 6.58727829 | 93.41272171 | 23.7703887 | 51.23904566 | 82.88817141 | 95.80275903 | 99.58488826 |
| D3_OR_relative_gt_200pct_z_gt_5 | 2.96867793 | 97.03132207 | 8.08838945 | 23.7703887 | 61.06335695 | 88.64103317 | 98.62887333 |

| scenario | balanced_accuracy_pct_plus_25 | balanced_accuracy_pct_plus_50 | balanced_accuracy_pct_plus_100 | balanced_accuracy_pct_plus_200 | balanced_accuracy_pct_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 56.57679567 | 70.97781878 | 90.95140258 | 94.83835801 | 95.44425343 |
| D1_relative_gt_100pct | 51.5744895 | 54.84925993 | 73.40140048 | 95.53650049 | 97.79026375 |
| D1_relative_gt_200pct | 50.45075266 | 51.01891064 | 53.44458887 | 74.42240765 | 98.28294687 |
| D2_robust_z_gt_2 | 64.22281856 | 78.34290746 | 88.91148476 | 92.73344794 | 94.13602248 |
| D2_robust_z_gt_3 | 58.50140467 | 72.04914252 | 87.6032538 | 93.8844396 | 96.45897102 |
| D2_robust_z_gt_5 | 52.54098705 | 60.34215271 | 78.90896893 | 92.46089983 | 97.49465387 |
| D3_AND_relative_gt_50pct_z_gt_2 | 55.95412805 | 70.04276909 | 89.9387815 | 94.63499518 | 96.04385928 |
| D3_AND_relative_gt_100pct_z_gt_3 | 51.48433896 | 54.57251876 | 72.85420772 | 94.81319971 | 97.75042979 |
| D3_AND_relative_gt_200pct_z_gt_5 | 50.43188394 | 50.96020798 | 53.30621829 | 74.04712986 | 97.94750304 |
| D3_OR_relative_gt_50pct_z_gt_2 | 64.84548618 | 79.27795714 | 89.92410583 | 92.93681076 | 93.53641662 |
| D3_OR_relative_gt_100pct_z_gt_3 | 58.5915552 | 72.32588369 | 88.15044656 | 94.60774037 | 96.49880498 |
| D3_OR_relative_gt_200pct_z_gt_5 | 52.55985576 | 60.40085538 | 79.04733951 | 92.83617762 | 97.8300977 |

| scenario | youden_j_pct_points_plus_25 | youden_j_pct_points_plus_50 | youden_j_pct_points_plus_100 | youden_j_pct_points_plus_200 | youden_j_pct_points_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 13.15359135 | 41.95563756 | 81.90280515 | 89.67671601 | 90.88850686 |
| D1_relative_gt_100pct | 3.148979 | 9.69851986 | 46.80280096 | 91.07300097 | 95.58052749 |
| D1_relative_gt_200pct | 0.90150531 | 2.03782129 | 6.88917774 | 48.8448153 | 96.56589375 |
| D2_robust_z_gt_2 | 28.44563713 | 56.68581492 | 77.82296952 | 85.46689589 | 88.27204495 |
| D2_robust_z_gt_3 | 17.00280934 | 44.09828504 | 75.20650761 | 87.7688792 | 92.91794205 |
| D2_robust_z_gt_5 | 5.08197409 | 20.68430542 | 57.81793786 | 84.92179966 | 94.98930773 |
| D3_AND_relative_gt_50pct_z_gt_2 | 11.90825611 | 40.08553818 | 79.877563 | 89.26999035 | 92.08771856 |
| D3_AND_relative_gt_100pct_z_gt_3 | 2.96867793 | 9.14503753 | 45.70841545 | 89.62639943 | 95.50085958 |
| D3_AND_relative_gt_200pct_z_gt_5 | 0.86376787 | 1.92041595 | 6.61243658 | 48.09425972 | 95.89500608 |
| D3_OR_relative_gt_50pct_z_gt_2 | 29.69097237 | 58.55591429 | 79.84821166 | 85.87362153 | 87.07283324 |
| D3_OR_relative_gt_100pct_z_gt_3 | 17.18311041 | 44.65176737 | 76.30089312 | 89.21548074 | 92.99760997 |
| D3_OR_relative_gt_200pct_z_gt_5 | 5.11971152 | 20.80171077 | 58.09467902 | 85.67235524 | 95.6601954 |

| scenario | false_negative_rate_pct_plus_25 | false_negative_rate_pct_plus_50 | false_negative_rate_pct_plus_100 | false_negative_rate_pct_plus_200 | false_negative_rate_pct_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 77.99907753 | 49.19703132 | 9.24986373 | 1.47595287 | 0.26416202 |
| D1_relative_gt_100pct | 92.85504633 | 86.30550547 | 49.20122437 | 4.93102436 | 0.42349784 |
| D1_relative_gt_200pct | 97.14034131 | 96.00402533 | 91.15266888 | 49.19703132 | 1.47595287 |
| D2_robust_z_gt_2 | 60.53503292 | 32.29485513 | 11.15770053 | 3.51377416 | 0.7086251 |
| D2_robust_z_gt_3 | 77.0514487 | 49.955973 | 18.84775043 | 6.28537884 | 1.13631599 |
| D2_robust_z_gt_5 | 92.28898486 | 76.68665353 | 39.55302109 | 12.44915929 | 2.38165122 |
| D3_AND_relative_gt_50pct_z_gt_2 | 80.88808755 | 52.71080548 | 12.91878066 | 3.52635331 | 0.7086251 |
| D3_AND_relative_gt_100pct_z_gt_3 | 93.67688373 | 87.50052413 | 50.93714621 | 7.01916223 | 1.14470208 |
| D3_AND_relative_gt_200pct_z_gt_5 | 97.51771563 | 96.46106755 | 91.76904692 | 50.28722378 | 2.48647742 |
| D3_OR_relative_gt_50pct_z_gt_2 | 57.64602289 | 28.78108097 | 7.4887836 | 1.46337373 | 0.26416202 |
| D3_OR_relative_gt_100pct_z_gt_3 | 76.2296113 | 48.76095434 | 17.11182859 | 4.19724097 | 0.41511174 |
| D3_OR_relative_gt_200pct_z_gt_5 | 91.91161055 | 76.2296113 | 38.93664305 | 11.35896683 | 1.37112667 |

### temporal_benchmark

| scenario | control_marked_pct_experimental | specificity_pct_experimental | recall_pct_plus_25 | recall_pct_plus_50 | recall_pct_plus_100 | recall_pct_plus_200 | recall_pct_plus_500 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 18.88975869 | 81.11024131 | 33.57271706 | 50.88662741 | 77.9619482 | 94.92869542 | 99.65964399 |
| D1_relative_gt_100pct | 8.8084136 | 91.1915864 | 15.95929342 | 25.7002825 | 50.88662741 | 85.40553419 | 98.9585106 |
| D1_relative_gt_200pct | 3.02576495 | 96.97423505 | 5.35720364 | 8.8084136 | 18.88975869 | 50.88662741 | 94.92869542 |
| D2_robust_z_gt_2 | 12.97777475 | 87.02222525 | 25.3667336 | 40.94482829 | 66.59065382 | 88.52659882 | 98.68282223 |
| D2_robust_z_gt_3 | 7.35168987 | 92.64831013 | 14.95183962 | 25.86365338 | 50.6483782 | 80.12320888 | 97.49497975 |
| D2_robust_z_gt_5 | 3.05639699 | 96.94360301 | 6.20128655 | 11.35768013 | 26.63626153 | 60.02518634 | 92.57343181 |
| D3_AND_relative_gt_50pct_z_gt_2 | 12.45362649 | 87.54637351 | 23.87597427 | 39.37919063 | 66.22306933 | 88.5027739 | 98.68282223 |
| D3_AND_relative_gt_100pct_z_gt_3 | 6.16044382 | 93.83955618 | 12.22558797 | 20.47581771 | 44.19182465 | 79.17701916 | 97.41329431 |
| D3_AND_relative_gt_200pct_z_gt_5 | 2.41993125 | 97.58006875 | 4.18637895 | 6.98070181 | 16.30305299 | 47.08825431 | 91.94377319 |
| D3_OR_relative_gt_50pct_z_gt_2 | 19.41390695 | 80.58609305 | 35.0634764 | 52.45226507 | 78.32953269 | 94.95252034 | 99.65964399 |
| D3_OR_relative_gt_100pct_z_gt_3 | 9.99965964 | 90.00034036 | 18.68554508 | 31.08811817 | 57.34318097 | 86.3517239 | 99.04019605 |
| D3_OR_relative_gt_200pct_z_gt_5 | 3.66223069 | 96.33776931 | 7.37211123 | 13.18539192 | 29.22296722 | 63.82355944 | 95.55835404 |

| scenario | balanced_accuracy_pct_plus_25 | balanced_accuracy_pct_plus_50 | balanced_accuracy_pct_plus_100 | balanced_accuracy_pct_plus_200 | balanced_accuracy_pct_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 57.34147919 | 65.99843436 | 79.53609475 | 88.01946836 | 90.38494265 |
| D1_relative_gt_100pct | 53.57543991 | 58.44593445 | 71.03910691 | 88.2985603 | 95.0750485 |
| D1_relative_gt_200pct | 51.16571934 | 52.89132432 | 57.93199687 | 73.93043123 | 95.95146524 |
| D2_robust_z_gt_2 | 56.19447943 | 63.98352677 | 76.80643954 | 87.77441204 | 92.85252374 |
| D2_robust_z_gt_3 | 53.80007487 | 59.25598176 | 71.64834416 | 86.38575951 | 95.07164494 |
| D2_robust_z_gt_5 | 51.57244478 | 54.15064157 | 61.78993227 | 78.48439468 | 94.75851741 |
| D3_AND_relative_gt_50pct_z_gt_2 | 55.71117389 | 63.46278207 | 76.88472142 | 88.0245737 | 93.11459787 |
| D3_AND_relative_gt_100pct_z_gt_3 | 53.03257208 | 57.15768695 | 69.01569041 | 86.50828767 | 95.62642525 |
| D3_AND_relative_gt_200pct_z_gt_5 | 50.88322385 | 52.28038528 | 56.94156087 | 72.33416153 | 94.76192097 |
| D3_OR_relative_gt_50pct_z_gt_2 | 57.82478473 | 66.51917906 | 79.45781287 | 87.7693067 | 90.12286852 |
| D3_OR_relative_gt_100pct_z_gt_3 | 54.34294272 | 60.54422926 | 73.67176066 | 88.17603213 | 94.52026821 |
| D3_OR_relative_gt_200pct_z_gt_5 | 51.85494027 | 54.76158061 | 62.78036826 | 80.08066437 | 95.94806167 |

| scenario | youden_j_pct_points_plus_25 | youden_j_pct_points_plus_50 | youden_j_pct_points_plus_100 | youden_j_pct_points_plus_200 | youden_j_pct_points_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 14.68295837 | 31.99686872 | 59.07218951 | 76.03893673 | 80.7698853 |
| D1_relative_gt_100pct | 7.15087982 | 16.8918689 | 42.07821381 | 76.59712059 | 90.150097 |
| D1_relative_gt_200pct | 2.33143869 | 5.78264865 | 15.86399374 | 47.86086246 | 91.90293047 |
| D2_robust_z_gt_2 | 12.38895885 | 27.96705354 | 53.61287907 | 75.54882407 | 85.70504748 |
| D2_robust_z_gt_3 | 7.60014975 | 18.51196351 | 43.29668833 | 72.77151901 | 90.14328988 |
| D2_robust_z_gt_5 | 3.14488956 | 8.30128314 | 23.57986454 | 56.96878935 | 89.51703482 |
| D3_AND_relative_gt_50pct_z_gt_2 | 11.42234778 | 26.92556414 | 53.76944284 | 76.04914741 | 86.22919574 |
| D3_AND_relative_gt_100pct_z_gt_3 | 6.06514415 | 14.31537389 | 38.03138083 | 73.01657534 | 91.25285049 |
| D3_AND_relative_gt_200pct_z_gt_5 | 1.7664477 | 4.56077056 | 13.88312174 | 44.66832306 | 89.52384194 |
| D3_OR_relative_gt_50pct_z_gt_2 | 15.64956945 | 33.03835812 | 58.91562574 | 75.53861339 | 80.24573704 |
| D3_OR_relative_gt_100pct_z_gt_3 | 8.68588544 | 21.08845853 | 47.34352133 | 76.35206426 | 89.04053641 |
| D3_OR_relative_gt_200pct_z_gt_5 | 3.70988054 | 9.52316123 | 25.56073653 | 60.16132875 | 91.89612335 |

| scenario | false_negative_rate_pct_plus_25 | false_negative_rate_pct_plus_50 | false_negative_rate_pct_plus_100 | false_negative_rate_pct_plus_200 | false_negative_rate_pct_plus_500 |
| --- | --- | --- | --- | --- | --- |
| D1_relative_gt_50pct | 66.42728294 | 49.11337259 | 22.0380518 | 5.07130458 | 0.34035601 |
| D1_relative_gt_100pct | 84.04070658 | 74.2997175 | 49.11337259 | 14.59446581 | 1.0414894 |
| D1_relative_gt_200pct | 94.64279636 | 91.1915864 | 81.11024131 | 49.11337259 | 5.07130458 |
| D2_robust_z_gt_2 | 74.6332664 | 59.05517171 | 33.40934618 | 11.47340118 | 1.31717777 |
| D2_robust_z_gt_3 | 85.04816038 | 74.13634662 | 49.3516218 | 19.87679112 | 2.50502025 |
| D2_robust_z_gt_5 | 93.79871345 | 88.64231987 | 73.36373847 | 39.97481366 | 7.42656819 |
| D3_AND_relative_gt_50pct_z_gt_2 | 76.12402573 | 60.62080937 | 33.77693067 | 11.4972261 | 1.31717777 |
| D3_AND_relative_gt_100pct_z_gt_3 | 87.77441203 | 79.52418229 | 55.80817535 | 20.82298084 | 2.58670569 |
| D3_AND_relative_gt_200pct_z_gt_5 | 95.81362105 | 93.01929819 | 83.69694701 | 52.91174569 | 8.05622681 |
| D3_OR_relative_gt_50pct_z_gt_2 | 64.9365236 | 47.54773493 | 21.67046731 | 5.04747966 | 0.34035601 |
| D3_OR_relative_gt_100pct_z_gt_3 | 81.31445492 | 68.91188183 | 42.65681903 | 13.6482761 | 0.95980395 |
| D3_OR_relative_gt_200pct_z_gt_5 | 92.62788877 | 86.81460808 | 70.77703278 | 36.17644056 | 4.44164596 |

Consumo: 23.849 evaluables para estas reglas; temporal: 29.381. AND 50/2 reduce controles marcados frente a OR (7,204 frente a 12,663 % en consumo; 12,454 frente a 19,414 % temporal), a costa de menor recall. No hay una preferencia ?nica sin decidir cu?nto pesa cada criterio.

## Distancia: escenarios existentes

El script original de sensibilidad mide **consumo**. Repetirlo no justifica por s? solo el corte temporal; por ello se reutiliza tambi?n la robustez temporal, con dos ?mbitos de hist?rico expl?citos. No se a?aden cortes nuevos.

### Consumo, hist?rico elegible fijo

| scenario | minimum_distance_km_strict | valid_records_initial | records_after_distance_filter | records_discarded_by_filter | records_discarded_pct | records_evaluable_b30 | vehicles_evaluated | l100_median | l100_p95 | l100_p99 | l100_max | deviation_median | deviation_p75 | deviation_p90 | deviation_p95 | deviation_p99 | over_50pct | over_50pct_pct | over_100pct | over_100pct_pct | over_200pct | over_200pct_pct | over_500pct | over_500pct_pct | coverage_pct_of_remaining |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sin_filtro | ? | 24597 | 24597 | 0 | 0.0 | 23849 | 22 | 0.01350877 | 0.07554916 | 0.37304242 | 22.46 | 0.00408597 | 0.16854383 | 0.44903203 | 0.80463494 | 3.62842695 | 2110 | 8.84733112 | 953 | 3.99597467 | 467 | 1.95815338 | 175 | 0.73378339 | 96.95897874 |
| distancia_gt_0_5km | 0.5 | 24597 | 22224 | 2373 | 9.64751799 | 21572 | 22 | 0.01264199 | 0.05112464 | 0.10986133 | 0.77803922 | -0.00182866 | 0.14449978 | 0.34249296 | 0.52660953 | 1.11438573 | 1193 | 5.53031708 | 281 | 1.3026145 | 63 | 0.29204524 | 8 | 0.03708511 | 97.0662347 |
| distancia_gt_1km | 1.0 | 24597 | 20794 | 3803 | 15.46123511 | 20156 | 22 | 0.01232053 | 0.04550177 | 0.07261223 | 0.31688109 | 0.00506669 | 0.14830115 | 0.3407952 | 0.51430736 | 1.04677208 | 1071 | 5.31355428 | 231 | 1.14606073 | 46 | 0.22821988 | 3 | 0.01488391 | 96.93180725 |
| distancia_gt_2km | 2.0 | 24597 | 19357 | 5240 | 21.30341099 | 18732 | 22 | 0.01212571 | 0.04490938 | 0.06876003 | 0.31688109 | 0.00468792 | 0.1435278 | 0.32774801 | 0.49194729 | 0.94149582 | 909 | 4.85265855 | 163 | 0.8701687 | 23 | 0.12278454 | 3 | 0.01601537 | 96.77119388 |
| distancia_gt_5km | 5.0 | 24597 | 16448 | 8149 | 33.13005651 | 15886 | 22 | 0.0122607 | 0.04414669 | 0.05964543 | 0.14509259 | 0.00261533 | 0.13483378 | 0.30789897 | 0.4529463 | 0.80810713 | 643 | 4.04758907 | 72 | 0.45322926 | 7 | 0.04406396 | 0 | 0.0 | 96.58317121 |

### Temporal

Duraci?n positiva y distancia positiva: 37.090 registros de 2025 de 37.295 totales. Sin filtro hay 35.756 evaluables; 126 distancias no positivas, 79 duraciones no positivas, 1.334 sin referencia y ning?n MAD cero. Hist?rico temporal sin filtro: 19.593 registros, 30 veh?culos elegibles y 159 contextos.

Las columnas KPI se calculan sobre los registros v?lidos restantes; las desviaciones y robust_z sobre los evaluables. Cobertura usa como denominador los v?lidos restantes, no los 37.090 iniciales. `fixed_history` conserva el hist?rico positivo; `filtered_history` aplica el mismo corte al hist?rico y a validaci?n y reproduce en >1 el ?mbito del motor actual.

| history_mode | scenario | records_after_distance_filter | records_discarded_by_filter | history_valid_records | history_eligible_vehicles | history_eligible_contexts | evaluable_2025 | coverage_pct_of_valid_temporal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_history | sin_filtro | 37090 | 0 | 19593 | 30 | 159 | 35756 | 96.40334322 |
| fixed_history | distancia_gt_0_5km | 33528 | 3562 | 19593 | 30 | 159 | 32342 | 96.46265808 |
| fixed_history | distancia_gt_1km | 30506 | 6584 | 19593 | 30 | 159 | 29381 | 96.31220088 |
| fixed_history | distancia_gt_2km | 28049 | 9041 | 19593 | 30 | 159 | 26947 | 96.07116118 |
| fixed_history | distancia_gt_5km | 24119 | 12971 | 19593 | 30 | 159 | 23096 | 95.75853062 |
| filtered_history | sin_filtro | 37090 | 0 | 19593 | 30 | 159 | 35756 | 96.40334322 |
| filtered_history | distancia_gt_0_5km | 33528 | 3562 | 17573 | 30 | 149 | 32342 | 96.46265808 |
| filtered_history | distancia_gt_1km | 30506 | 6584 | 16090 | 30 | 135 | 29381 | 96.31220088 |
| filtered_history | distancia_gt_2km | 28049 | 9041 | 14720 | 30 | 122 | 26947 | 96.07116118 |
| filtered_history | distancia_gt_5km | 24119 | 12971 | 12383 | 29 | 105 | 22790 | 94.4898213 |

| history_mode | scenario | kpi_median | kpi_p75 | kpi_p90 | kpi_p95 | kpi_p99 | kpi_max | relative_p95 | relative_p99 | z_p95 | z_p99 | AND50_2_marked_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_history | sin_filtro | 2.49496846 | 4.823814 | 10.64131702 | 21.75599238 | 113.33333333 | 28150.0 | 1.93267234 | 6.59757784 | 4.21981624 | 13.0071984 | 13.34601186 |
| fixed_history | distancia_gt_0_5km | 2.24832082 | 3.93939394 | 6.71171071 | 9.98608585 | 23.28570846 | 158.07692308 | 1.43878739 | 3.51994654 | 3.60271181 | 8.13415767 | 11.64430153 |
| fixed_history | distancia_gt_1km | 2.06874099 | 3.39550187 | 5.37210474 | 7.3775783 | 15.04045203 | 96.6641957 | 1.41835087 | 3.35875667 | 3.6078137 | 7.84698937 | 11.97372452 |
| fixed_history | distancia_gt_2km | 1.94940476 | 3.03179056 | 4.67756861 | 6.27807161 | 11.88356854 | 96.6641957 | 1.3053654 | 2.82694453 | 3.47745341 | 7.24886768 | 11.47066464 |
| fixed_history | distancia_gt_5km | 1.78008 | 2.63756511 | 3.98382653 | 5.17639383 | 8.94061289 | 40.51408538 | 1.18784445 | 2.45366331 | 3.31886464 | 6.76385572 | 10.82871493 |
| filtered_history | sin_filtro | 2.49496846 | 4.823814 | 10.64131702 | 21.75599238 | 113.33333333 | 28150.0 | 1.93267234 | 6.59757784 | 4.21981624 | 13.0071984 | 13.34601186 |
| filtered_history | distancia_gt_0_5km | 2.24832082 | 3.93939394 | 6.71171071 | 9.98608585 | 23.28570846 | 158.07692308 | 1.77134396 | 5.64153421 | 4.32615809 | 12.83013169 | 13.41908354 |
| filtered_history | distancia_gt_1km | 2.06874099 | 3.39550187 | 5.37210474 | 7.3775783 | 15.04045203 | 96.6641957 | 1.45972501 | 3.57447383 | 3.75361187 | 8.92543791 | 12.45362649 |
| filtered_history | distancia_gt_2km | 1.94940476 | 3.03179056 | 4.67756861 | 6.27807161 | 11.88356854 | 96.6641957 | 1.3460171 | 3.04522136 | 3.61008459 | 7.96603606 | 11.96422607 |
| filtered_history | distancia_gt_5km | 1.78008 | 2.63756511 | 3.98382653 | 5.17639383 | 8.94061289 | 40.51408538 | 1.22357537 | 2.58170329 | 3.48155765 | 7.03568308 | 11.51382185 |

En 2025, <=1 km presenta p99 de desviaci?n 32,324 y p99 de z 61,170 frente a 3,359 y 7,847 en >1 con referencias fijas. Con hist?rico filtrado, >1 conserva 30.506 v?lidos y 29.381 evaluables, descarta 6.584 v?lidos (17,751 %), y baja el p99 del KPI de 113,333 a 15,040 minutos/km. >0,5 ya reduce buena parte de la cola; >2 y >5 siguen reduci?ndola a costa de poblaci?n. Se respalda el problema de los trayectos cortos y el corte >1 como opci?n t?cnica razonable, pero no su elecci?n ?nica u ?ptima. No se confunde reducci?n de cola por truncar poblaci?n con prueba longitudinal de estabilidad de los baselines.

## Fase 5: decisiones y estado

| Decisi?n | Valor actual | Resultado 2024?2025 | ?Justificada sin 2026? | Observaciones |
| --- | --- | --- | --- | --- |
| B30 | B30 | 23.849 evaluables; contexto 92,943 %; p99 3,628 frente a A 13,283 y B50 6,215 | S?, respaldo cualitativo | Preferencia respaldada seg?n contexto/fallback y colas; no optimizaci?n ?nica. |
| M?nimo hist?rico | 100 | 22/23 veh?culos consumo; 14.837/14.886 registros hist?ricos; p?rdida 22 evaluables | No se justifica el valor exacto | Criterio inicial documentado; viable, sin candidatos alternativos ni comparaci?n de estabilidad que seleccione 100. |
| M?nimo contextual | 30 | 119 contextos frente a 100 con m?nimo 50; m?s contexto y menores colas | S? frente a 50, cualitativamente | No demuestra optimalidad de 30; forma parte de B30. |
| Desviaci?n relativa | >0,50 | D1 control consumo 8,847 %, temporal 18,890 % | Pendiente | Existen cortes comparados; falta criterio de elecci?n. |
| Robust z | >2 | Tablas completas D2 y combinadas | Pendiente | No se demuestra preferencia entre 2/3/5 ni los cortes descriptivos adicionales. |
| Combinaci?n | AND | Control 7,204 % consumo y 12,454 % temporal; menor recall que OR | Pendiente | Compromiso observado; no consta prioridad que permita resolverlo. |
| Distancia temporal | >1 km | 29.381 evaluables; cobertura restante 96,312 %; p99 KPI 15,040 | Respaldada como opci?n; selecci?n pendiente | Inestabilidad corta demostrada; elegir 1 frente a 0,5/2/5 requiere criterio t?cnico. |

No se cambi? ninguna decisi?n operativa. No hay configuraci?n final que pueda declararse congelada como resultado autom?tico de esta validaci?n. Candidata conservada para discusi?n: B30, m?nimos 100/30, mediana/MAD, AND >0,50 y >2, temporal >1 aplicado tambi?n al hist?rico, consumo sin corte adicional, MAD cero no evaluable. **Es una candidata, no una selecci?n cerrada.** Requieren confirmaci?n la justificaci?n del m?nimo 100, las prioridades de selecci?n de reglas/umbrales y el compromiso distancia/cobertura. No se propone una funci?n objetivo nueva.

## Resultados anteriores y evaluaci?n final

No procede fase 6. No se reconstruy? el hist?rico final ni se ejecut? un benchmark nuevo de 2026. La comparaci?n siguiente conserva los resultados publicados de `docs/decision-log.md` y muestra validaci?n 2025 de la misma candidata. **No es antiguo 2026 frente a nuevo 2026; cambia el periodo y la poblaci?n.** No permite atribuir mejoras al protocolo ni sustituir las cifras finales de la memoria.

| Se?al/periodo | N | Control % | Especificidad % | Recall +25 | +50 | +100 | +200 | +500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Consumo antiguo 2026 | 6427 | 10.14 | 89.86 | 21.44 | 48.87 | 82.7 | 92.95 | 98.38 |
| Consumo validaci?n 2025 | 23849 | 7.20365634 | 92.79634366 | 19.11191245 | 47.28919452 | 87.08121934 | 96.47364669 | 99.2913749 |
| Temporal antiguo 2026 | 9644 | 13.03 | 86.97 | 24.83 | 40.18 | 65.84 | 87.33 | 98.66 |
| Temporal validaci?n 2025 | 29381 | 12.45362649 | 87.54637351 | 23.87597427 | 39.37919063 | 66.22306933 | 88.5027739 | 98.68282223 |
| Nuevos resultados finales 2026 | No ejecutados | ? | ? | ? | ? | ? | ? | ? |

## Artefactos completos y verificaci?n

Cada CSV incluye todos los campos originales, incluidos recuentos, falsos negativos, m?tricas por perturbaci?n, ?mbito y rango. El JSON incluye todos los percentiles y tasas temporales por escenario/grupo. No se inventaron etiquetas ni m?tricas de eficiencia real. Se conservaron unidades y conversiones originales; las magnitudes absolutas de consumo se informan tal como las calcula el CSV, sin recalibrarlas para coincidir con la memoria.

- [baseline_eligible_by_range.csv](resultados-validacion-2025/baseline_eligible_by_range.csv)
- [baseline_original/baseline_strategy_evaluation_by_range_2025.csv](resultados-validacion-2025/baseline_original/baseline_strategy_evaluation_by_range_2025.csv)
- [baseline_original/baseline_strategy_evaluation_summary_2025.csv](resultados-validacion-2025/baseline_original/baseline_strategy_evaluation_summary_2025.csv)
- [baseline_original/baseline_strategy_evaluation_summary_2025.json](resultados-validacion-2025/baseline_original/baseline_strategy_evaluation_summary_2025.json)
- [candidates_eligible.csv](resultados-validacion-2025/candidates_eligible.csv)
- [candidates_eligible_by_range.csv](resultados-validacion-2025/candidates_eligible_by_range.csv)
- [candidates_original/detector_candidate_scenarios_2025.csv](resultados-validacion-2025/candidates_original/detector_candidate_scenarios_2025.csv)
- [candidates_original/detector_candidate_scenarios_by_range_2025.csv](resultados-validacion-2025/candidates_original/detector_candidate_scenarios_by_range_2025.csv)
- [consumption_benchmark/synthetic_benchmark_by_range.csv](resultados-validacion-2025/consumption_benchmark/synthetic_benchmark_by_range.csv)
- [consumption_benchmark/synthetic_benchmark_rule_comparison.csv](resultados-validacion-2025/consumption_benchmark/synthetic_benchmark_rule_comparison.csv)
- [consumption_benchmark/synthetic_benchmark_summary.csv](resultados-validacion-2025/consumption_benchmark/synthetic_benchmark_summary.csv)
- [distance_consumption_eligible.csv](resultados-validacion-2025/distance_consumption_eligible.csv)
- [distance_consumption_eligible_by_range.csv](resultados-validacion-2025/distance_consumption_eligible_by_range.csv)
- [distance_consumption_original/distance_threshold_sensitivity_2025.csv](resultados-validacion-2025/distance_consumption_original/distance_threshold_sensitivity_2025.csv)
- [distance_consumption_original/distance_threshold_sensitivity_by_range_2025.csv](resultados-validacion-2025/distance_consumption_original/distance_threshold_sensitivity_by_range_2025.csv)
- [mad_original/b30_mad_2025_distance_summary.csv](resultados-validacion-2025/mad_original/b30_mad_2025_distance_summary.csv)
- [mad_original/b30_mad_2025_summary.json](resultados-validacion-2025/mad_original/b30_mad_2025_summary.json)
- [temporal_benchmark/temporal_synthetic_benchmark_rule_comparison.csv](resultados-validacion-2025/temporal_benchmark/temporal_synthetic_benchmark_rule_comparison.csv)
- [temporal_benchmark/temporal_synthetic_benchmark_summary.csv](resultados-validacion-2025/temporal_benchmark/temporal_synthetic_benchmark_summary.csv)
- [validation_2025.json](resultados-validacion-2025/validation_2025.json)

Tests ejecutados: `python -m unittest discover -s tests -v`: **158 tests, OK**, incluyendo cuatro tests nuevos de separaci?n (seis cargadores, exclusi?n de 2026 antes de convertir variables, a?os inv?lidos y compatibilidad del split original e invariancia del ejecutor completo al cambiar las variables de 2026). `git diff --check`: sin errores. Los tests usan fixtures y dobles; no ejecutan evaluaci?n final sobre datos reales de 2026.

### git diff --stat

Esta salida no incluye archivos nuevos sin seguimiento; se enumeran en git status. El ?rbol inicial estaba limpio.

```text
 scripts/analyze_b30_mad.py                        | 26 ++++++++++++++---------
 scripts/analyze_distance_threshold_sensitivity.py | 22 ++++++++++++-------
 scripts/analyze_temporal_robustness.py            | 26 ++++++++++++++---------
 scripts/evaluate_detector_candidates.py           | 22 ++++++++++++-------
 scripts/evaluate_synthetic_benchmark.py           | 18 ++++++++++------
 scripts/evaluate_temporal_synthetic_benchmark.py  | 18 ++++++++++------
 6 files changed, 84 insertions(+), 48 deletions(-)
```

### git status --short

```text
 M scripts/analyze_b30_mad.py
 M scripts/analyze_distance_threshold_sensitivity.py
 M scripts/analyze_temporal_robustness.py
 M scripts/evaluate_detector_candidates.py
 M scripts/evaluate_synthetic_benchmark.py
 M scripts/evaluate_temporal_synthetic_benchmark.py
?? docs/auditoria-validacion-2025.md
?? docs/protocolo-validacion-2025.md
?? docs/resultados-validacion-2025/
?? scripts/experimental_split.py
?? scripts/validate_methodology_2025.py
?? tests/test_experimental_split.py
```

No se ejecutaron comandos commit ni push. `src/baseline.py`, `src/detector.py`, `src/temporal_detector.py` y `src/analytical_service.py` permanecen sin cambios. Los CSV originales y los resultados previos de 2026 permanecen sin modificaciones.
