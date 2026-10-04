# Estado validado del proyecto TFM — Prototipo v1

> Nota de nomenclatura revisada (04/10/2026): las menciones históricas a
> «especificidad»/`specificity` y «recall» describen respectivamente tasa de no
> marcado en controles y tasa de marcado tras perturbación, sin ground truth
> real. Se conservan como trazabilidad; para resultados finales y detección
> incremental véase [Métricas finales](metricas-finales-benchmark.md). El término
> «sensibilidad» en análisis de parámetros conserva su sentido metodológico.


**Estado: APROBADO PARA MEMORIA**

Este documento consolida las decisiones, implementación, resultados y
limitaciones del prototipo v1 que pueden utilizarse como hechos del proyecto
durante la redacción de la memoria.

En caso de contradicción con la propuesta inicial del TFT, este documento
representa el estado posterior y actualizado del proyecto. La propuesta inicial
debe conservarse como evidencia del planteamiento original, pero no debe
utilizarse para afirmar que todos sus elementos fueron finalmente implementados.

## 1. Identificación del proyecto

- Proyecto identificado en el repositorio como `TFM-IA-LOGISTICA`.
- Versión de referencia: prototipo v1 de análisis de desviaciones logísticas.
- Este archivo es una referencia técnica para redactar la memoria LaTeX, no
  un capítulo ni una acreditación de despliegue productivo.

## 2. Problema abordado

Identificar desviaciones de consumo y comportamiento temporal en viajes
logísticos respecto a su histórico comparable, y apoyar su revisión humana
mediante resultados estructurados y explicaciones. No se confirman
ineficiencias reales ni se determinan causas.

## 3. Evolución del alcance

- La hipótesis de estudiar tiempos de parada se sustituyó por una señal de
  minutos/km: la duración disponible no separa conducción, espera y parada.
- No existe una variable fiable de carga disponible; carga-consumo quedó
  fuera de la v1 y no se infiere carga desde otras variables.
- Se compararon A, B30 y B50; B30 quedó como baseline operativo. Los otros
  baselines y las reglas candidatas se conservan como experimentos históricos.
- La v1 genera estados de revisión, pero no distribuye alertas automáticamente.

## 4. Datos disponibles

- SQL Server es la fuente operacional; CSV sirve para desarrollo y pruebas.
- Variables analíticas: identidad de viaje y vehículo, fecha de inicio,
  distancia, consumo y duración. No se reproducen aquí identidades reales.
- Velocidad máxima e indicador de conducción no intervienen en los detectores.
- 2024–2025 constituyen el histórico para baselines; 2026 es el periodo de
  evaluación. No se dispone de ground truth real de ineficiencia.
- Las unidades se normalizan a kilómetros, litros y minutos. Aclaración
  posterior al tag v1.0-tfm: el adaptador de aquella versión multiplicaba
  erróneamente el consumo SQL por 1000 al asumir litros. En la fuente
  operacional verificada, `Consumo` ya está en mililitros y debe conservarse
  para el contrato interno; la normalización posterior obtiene litros,
  L/100 km y minutos/km. Esta corrección documental no modifica el tag ni
  recalcula los resultados experimentales anteriores.
- `Consumo=NULL`, `None`, una celda CSV vacía y cadenas de espacios representan
  ausencia, nunca cero. Consumo devuelve `NOT_EVALUABLE` con
  `MISSING_CONSUMPTION`; temporal puede seguir evaluándose.
- Consumo cero o negativo también es no evaluable, con motivo distinto. El
  tratamiento de ausencia no es un sistema general de tolerancia a datos malformados.
- Datos empresariales y artefactos reales de evaluación permanecen bajo
  `data/`, fuera de Git. Las credenciales se configuran externamente.

## 5. Alcance final del prototipo v1

Incluye normalización, baselines robustos, detectores deterministas de consumo
y temporal, consolidación, adaptadores CSV/SQL, API FastAPI, experimentos
semi-sintéticos, utilidades de evaluación y workflow n8n sanitizado.

RF-11 permanece `PARCIAL`: hay explicación evaluada y workflow de evaluación
versionado, pero la integración operacional n8n no está completamente
versionada ni es reproducible solo con el repositorio.

## 6. Metodología analítica

- División temporal no aleatoria: histórico 2024–2025 y evaluación 2026.
- Mínimo de 100 observaciones históricas válidas por vehículo para la
  construcción de las referencias históricas utilizadas por la v1.
- B30 utiliza el contexto vehículo-rango de distancia con al menos 30
  observaciones; si no alcanza ese mínimo, aplica fallback al vehículo.
- Referencia mediante mediana y MAD. El z robusto usa la escala `1.4826 * MAD`.
- Regla estricta común: `relative_deviation > 0.50 AND robust_z > 2`.
- `relative_deviation = (valor - baseline) / baseline`; es una proporción,
  cuya expresión porcentual requiere multiplicar por 100.
- Sin histórico elegible o con MAD cero, la señal es `NOT_EVALUABLE`.

## 7. Detector de consumo v1

`src/detector.py` implementa `DetectorV1` sobre L/100 km. Marca `REVIEW` cuando
se cumplen ambos umbrales por exceso. Con datos evaluables que no satisfacen
ambos, devuelve `NO_RELEVANT_DEVIATION`. La ausencia de consumo no se sustituye
por cero ni implica normalidad.

## 8. Detector temporal v1

`src/temporal_detector.py` implementa `TemporalDetectorV1` sobre
`minutes_per_km`, calculado como duración en minutos dividida por distancia en
kilómetros. Aplica B30 y la misma regla conjunta. Los viajes de distancia
menor o igual a 1 km no son evaluables para esta señal v1.

La señal temporal NO es tiempo de parada ni permite separar sus causas.

## 9. Consolidación de señales

`src/consolidation.py` conserva ambas salidas bajo `signals` y calcula:

| Condición | Estado global |
|---|---|
| Alguna señal en `REVIEW` | `REVIEW` |
| Ninguna en `REVIEW` y alguna evaluable | `NO_RELEVANT_DEVIATION` |
| Ninguna señal evaluable | `NOT_EVALUABLE` |

La cobertura es `COMPLETE`, `PARTIAL` o `NONE` cuando son evaluables dos, una o
ninguna señal, respectivamente. Consumo ausente puede producir `PARTIAL` si
temporal es evaluable. La consolidación no recalcula los detectores.

## 10. Arquitectura implementada

`datos -> normalización -> baselines B30 -> detectores v1 -> consolidación -> API`

`AnalyticalService` inicializa los detectores con el histórico y reúne su
evaluación. n8n y el LLM están fuera del motor determinista. Las explicaciones
no sustituyen estados ni cálculos analíticos.

## 11. Papel de SQL Server

Fuente operacional mediante `src/sql_repository.py`, con consultas de lectura,
parametrizadas y columnas explícitas. El histórico usa el intervalo
`[2024-01-01, 2026-01-01)`. Permite recuperar un viaje por su identificador.

La integración SQL Server → FastAPI está documentada como validada
externamente. Los tests del repositorio usan dobles y no prueban una conexión
real a SQL Server.

## 12. Papel de FastAPI

`src/api.py` implementa la frontera HTTP:

| Endpoint | Función |
|---|---|
| `GET /health` | Respuesta de salud básica |
| `POST /evaluate` | Evaluación del contrato completo de un viaje |
| `POST /evaluate-trip` | Recuperación por `trip_id` y evaluación en modo SQL |

`POST /evaluate` exige `consumption_ml` numérico como decisión de interfaz.
La semántica de consumo ausente de CSV/SQL no modifica ese contrato. La API
delega la decisión analítica en el servicio existente.

## 13. Papel de n8n

n8n es el orquestador. El flujo operacional que consulta `/evaluate-trip` se
validó externamente, pero no está completamente versionado ni es reproducible
solo desde el repositorio.

`n8n/conversational_evaluation_v1.json` es el workflow sanitizado y versionado
de evaluación: lee casos, invoca el modelo y guarda respuestas. No consulta
`/evaluate-trip`. Requiere n8n, entradas de evaluación, credenciales propias y
servicios externos; no contiene credenciales ni datos empresariales.

## 14. Papel del LLM

El LLM es exclusivamente explicativo, no detector. Debe respetar estados,
magnitudes y cobertura, sin atribuir causas ni confirmar ineficiencias.

Las respuestas de la evaluación v1 se generaron mediante n8n con GPT-5.6 Luna.
Las utilidades Python de `evaluation/` preparan casos, incorporan respuestas y
puntuaciones humanas y calculan resúmenes; no invocan automáticamente al LLM
ni deducen las puntuaciones a partir del texto.

## 15. Evaluación semi-sintética

Se aplicaron perturbaciones controladas de +25 %, +50 %, +100 %, +200 % y
+500 % sobre consumo o duración, conservando la distancia y sin contaminar
los baselines históricos. Los scripts comparan reglas candidatas, incluida la
regla final v1.

Recall, tasa marcada del control y especificidad experimental describen este
experimento; no son rendimiento frente a ineficiencias reales.

Los 6.665 registros del análisis MAD anterior corresponden a una fase
exploratoria con criterios de elegibilidad anteriores. Los 6.427 son la
población final evaluable del benchmark de consumo v1 tras los criterios
definitivos, incluido el mínimo histórico por vehículo. Es un cambio de
elegibilidad entre fases, no una contradicción. No se recalculan métricas aquí.

## 16. Evaluación conversacional v1

20 casos reales de 2026 seleccionados de forma determinista como muestra
funcional estratificada, no representativa de la prevalencia operacional:

| Estrato | Casos |
|---|---:|
| `NO_RELEVANT_DEVIATION_COMPLETE` | 5 |
| `REVIEW_COMPLETE` | 5 |
| `NOT_EVALUABLE_NONE` | 5 |
| `PARTIAL` | 5 |

La documentación establece que las respuestas se generaron y congelaron antes
de puntuar y que la rúbrica se fijó previamente. C1–C6 evalúan estados, fidelidad
numérica, ausencia de causas no sustentadas, semántica de revisión y cobertura.
`N/A` queda fuera del denominador; claridad/utilidad se valora por separado.

Se utilizó un único evaluador humano, sin evaluación interjueces. Los
resultados son específicos del modelo y prompt evaluados y no se generalizan
automáticamente a otros modelos, prompts o poblaciones.

## 17. Pruebas y validaciones

- 130 tests automatizados superados en la ejecución completa realizada tras
  corregir consumo CSV vacío: `python -m unittest discover -s tests -v`.
- Cubren lógica analítica, normalización, baselines, consolidación, contratos
  API, repositorio SQL con dobles y utilidades experimentales/de evaluación.
- Hay pruebas de CSV real con consumo vacío y cobertura parcial, espacios,
  formatos numéricos y conservación de SQL NULL.
- Las validaciones SQL Server → FastAPI y n8n operacional son externas,
  declaradas en la documentación; no son tests automatizados end-to-end.
- La valoración conversacional es humana. Los tests de sus utilidades
  comprueban procesamiento y agregación, no la corrección de respuestas reales.
- La creación de esta referencia documental no implica una nueva ejecución
  de tests ni de experimentos.

## 18. Resultados históricos validados (anteriores a la política final de calidad)

Cifras trasladadas de las fuentes documentales, sin reinterpretación ni recálculo.

| Benchmark | Registros evaluables | Control marcado | Especificidad experimental |
|---|---:|---:|---:|
| Consumo v1 | 6.427 | 10,14 % | 89,86 % |
| Temporal v1 | 9.644 | 13,03 % | 86,97 % |

| Perturbación | Recall semi-sintético consumo | Recall semi-sintético temporal |
|---|---:|---:|
| +25 % | 21,44 % | 24,83 % |
| +50 % | 48,87 % | 40,18 % |
| +100 % | 82,70 % | 65,84 % |
| +200 % | 92,95 % | 87,33 % |
| +500 % | 98,38 % | 98,66 % |

Estos valores representan la respuesta del detector ante perturbaciones
artificiales controladas y no sensibilidad frente a ineficiencias reales.

Evaluación conversacional: 98,96 % de cumplimiento sobre criterios aplicables
y claridad/utilidad media de 3,95/5. Se registró un incumplimiento de fidelidad
numérica por conversión porcentual incorrecta. No quedaron criterios sin
puntuar. Estas cifras evalúan explicaciones, no precisión de detección.

## 19. Limitaciones

- Ausencia de ground truth real y de validación experta operacional sistemática.
- Muestra conversacional pequeña, estratificada y con un solo evaluador.
- El LLM puede introducir errores numéricos aunque la entrada sea correcta.
- Sin variable fiable de carga ni separación de conducción, espera y parada.
- Cobertura condicionada por datos válidos, histórico suficiente y MAD no nulo.
- Los artefactos reales quedan fuera de Git: las cifras documentadas no pueden
  reproducirse solo con los archivos versionados. Las validaciones externas
  no se corroboran mediante los tests locales.
- No se acredita un sistema productivo ni una reproducción autónoma de la
  integración operacional n8n. RF-11 sigue siendo `PARCIAL`.
- No se identifica contradicción entre las fuentes prioritarias sobre los
  hechos aquí consolidados; las carencias de evidencia externa se mantienen
  explícitas y no se sustituyen por supuestos.

## 20. Trabajo futuro ya identificado

- Obtener ground truth y validación experta operacional si fueran viables.
- Incorporar evaluación interjueces y evaluar otros modelos/prompts.
- Productivizar despliegue, autenticación, observabilidad, gestión de secretos
  y operación de SQL Server, FastAPI y n8n.
- Incorporar distribución de alertas si entra en un alcance posterior.
- Reabrir carga-consumo únicamente con una variable fiable disponible.

## 21. Terminología obligatoria para la memoria

| Término | Uso obligatorio |
|---|---|
| `REVIEW` | Desviación que requiere revisión; no ineficiencia confirmada |
| `NO_RELEVANT_DEVIATION` | No se cumplen conjuntamente los criterios de revisión |
| `NOT_EVALUABLE` | La señal no pudo evaluarse; no significa normalidad |
| `COMPLETE` / `PARTIAL` / `NONE` | Dos / una / ninguna señal evaluable |
| Señal temporal | Minutos/km respecto al histórico comparable |
| Métricas semi-sintéticas | Resultados experimentales de perturbaciones controladas |
| Cumplimiento conversacional | Fidelidad a la salida analítica sobre criterios aplicables |
| Validación externa | Evidencia declarada fuera de los tests automatizados locales |

## 22. Elementos que NO deben afirmarse

- Que `REVIEW` sea una ineficiencia confirmada.
- Que el sistema determine causas.
- Que `minutes_per_km` sea tiempo de parada.
- Que se haya realizado análisis carga-consumo.
- Que exista ground truth real de ineficiencia.
- Que las métricas semi-sintéticas sean precisión, sensibilidad o especificidad
  frente a ineficiencias reales.
- Que el prototipo sea un sistema productivo.
- Que los 130 tests constituyan validación end-to-end de SQL Server, n8n y LLM.
- Que se haya implementado distribución automática de alertas.
- Que el LLM detecte desviaciones o que el 98,96 % mida precisión del detector.
- Que todos los elementos de la propuesta inicial se hayan implementado.

## 23. Trazabilidad con la documentación del repositorio

| Hechos | Fuente prioritaria | Comprobación técnica complementaria |
|---|---|---|
| Alcance, RF-06, RF-11 y exclusiones | [Requisitos](requisitos.md) | `src/data_processing.py`, `tests/test_detector_v1.py`, `tests/test_data_source_selection.py` |
| Evolución, B30, regla y poblaciones 6.665/6.427 | [Decisiones](decision-log.md) | `src/baseline.py`, detectores y `scripts/evaluate_*` |
| Rúbrica, 20 casos y resultados conversacionales | [Metodología](metodologia.md) | `evaluation/` y workflow n8n de evaluación |
| Consolidación, SQL, API y separación LLM | [Arquitectura](arquitectura.md) | `src/consolidation.py`, `src/analytical_service.py`, `src/sql_repository.py`, `src/api.py` |
| Estado general, instalación y 130 tests | [README](../README.md) | `tests/`; ejecución completa satisfactoria tras corregir RF-06 |
| Resultados semi-sintéticos y límites futuros | [Decisiones](decision-log.md) | Scripts de benchmark de consumo y temporal |

La evidencia documental de resultados y validaciones externas no equivale a
una nueva verificación independiente de sus artefactos originales. Esta
referencia conserva esa distinción para la redacción de la memoria.
