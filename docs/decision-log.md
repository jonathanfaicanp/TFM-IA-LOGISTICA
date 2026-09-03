# Registro de decisiones

Este documento registra las decisiones del TFM y su estado para mantener la trazabilidad.

## Confirmado

- El TFM se desarrolla sobre un caso empresarial real.
- El título del proyecto es: «Sistema IA conversacional para detección de ineficiencias logísticas y apoyo a la toma de decisiones».
- La fuente principal para el análisis será la tabla transformada `dbo.WF_OPERATIVA_CAMIONES` de la base de datos `AETL_SBOBI_v2_LOGISTICA`.
- Entre los campos relevantes de la tabla se encuentran: Código Viaje, Código Vehículo, Nombre Vehículo, Fecha de inicio, Fecha fin, Duración, Distancia, Velocidad máxima, Consumo, Conductor, Consumo CO2, Indicador de conducción y Matrícula.
- Para el análisis actual se consideran principalmente las variables distancia, duración, consumo, velocidad máxima e indicador de conducción.
- Las unidades conocidas son: distancia en metros, duración en segundos y consumo en mililitros.
- Se pueden derivar las siguientes variables normalizadas: distancia en kilómetros; duración en minutos u horas; consumo en litros; y consumo en litros por 100 km.
- Los registros con consumo igual a cero no se interpretarán automáticamente como consumo real cero; actualmente se considera que pueden corresponder a vehículos o dispositivos sin una medición válida de consumo.
- La exploración realizada sobre la tabla obtuvo 70.195 registros.
- En dicha exploración se identificaron 513 registros con distancia o duración no válidas según los criterios utilizados, quedando 69.682 registros candidatos (99,27 %).
- Los datos de 2024 y 2025 no se descartarán automáticamente y se evaluará su utilización dentro del *baseline*.
- Actualmente no existe una variable de *ground truth* que identifique qué viajes constituyen realmente una ineficiencia.
- Tampoco se dispone actualmente de la posibilidad de obtener una validación experta sistemática de una muestra de registros.

## Provisional

- Se estudia utilizar un *baseline* histórico por vehículo para detectar desviaciones respecto al comportamiento habitual.
- Se considera inicialmente la utilización de métodos estadísticos robustos, como mediana y medidas de dispersión, antes de introducir algoritmos de *machine learning* más complejos.
- Se estudia utilizar una división temporal entre datos históricos y datos posteriores para evaluar el comportamiento del detector.
- Se plantea estudiar si un *baseline* basado en todo el histórico funciona mejor o peor que uno que priorice datos recientes.
- Se plantea una arquitectura en la que SQL Server proporcione los datos, un componente analítico realice las transformaciones y detección, N8N realice la orquestación y GPT genere explicaciones en lenguaje natural.
- Las decisiones arquitectónicas anteriores no son definitivas.

## Resultados experimentales — estado provisional

### Baseline B30 como candidata preferente

- **Evidencia:** Las evaluaciones temporales compararon A, B30 y B50. B30 mostró mejor comportamiento descriptivo que A y un mayor uso del contexto que B50, manteniendo el fallback al baseline por vehículo cuando el contexto no alcanza 30 observaciones.
- **Interpretación:** B30 es actualmente la candidata preferente entre las estrategias experimentadas.
- **Estado:** Decisión metodológica provisional; no constituye la selección definitiva del baseline.

### Dependencia respecto al rango de distancia

- **Evidencia:** Las medianas y distribuciones de L/100 km varían por rango de distancia dentro de los vehículos. Los análisis de desviación relativa y robust_z muestran una mayor frecuencia relativa de valores elevados en trayectos cortos.
- **Interpretación:** La distancia aporta contexto relevante para representar el comportamiento habitual del consumo.
- **Estado:** Evidencia experimental; no se adopta todavía una regla definitiva de tratamiento de la distancia.

### Sensibilidad a una distancia mínima evaluable

- **Evidencia:** Al aumentar el umbral mínimo de distancia se reducen los valores extremos del KPI y de las desviaciones, pero también se descarta una proporción significativa de los registros evaluables.
- **Interpretación:** Existe un compromiso entre estabilidad del KPI y cobertura de datos.
- **Estado:** No se adopta un filtro mínimo de distancia como criterio de exclusión global.

### Viabilidad del cálculo MAD sobre B30

- **Evidencia:** En la evaluación de 2026 se calcularon medidas MAD para los 6.665 registros evaluables con B30; no se produjeron casos con MAD igual a cero.
- **Interpretación:** La escala robusta basada en MAD pudo calcularse en el experimento sin divisiones por cero.
- **Estado:** Evidencia experimental; su uso forma parte de la investigación y no de un detector definitivo.

### Cola extrema de robust_z y distancia

- **Evidencia:** Los grupos de robust_z elevado tienen una presencia relativa mayor en trayectos de hasta 1 km que el conjunto completo evaluable. Los grupos extremos también contienen registros de rangos de distancia superiores.
- **Interpretación:** Los valores extremos no están exclusivamente asociados a trayectos cortos.
- **Estado:** Evidencia descriptiva; no permite asignar una causa ni una clasificación definitiva a los registros.

### Ausencia de ground truth de ineficiencia

- **Evidencia:** Los análisis disponibles describen desviaciones respecto a referencias históricas, pero no existe una variable que confirme qué registros representan ineficiencias reales.
- **Interpretación:** Ningún registro puede considerarse todavía una ineficiencia real a partir de estos experimentos.
- **Estado:** Limitación confirmada para la evaluación metodológica.

### Umbral de robust_z y regla de clasificación

- **Evidencia:** Se analizaron puntos de comparación de robust_z, incluidos valores superiores a 1, 2, 3, 4, 5 y grupos de cola más extrema, sin convertirlos en alertas.
- **Interpretación:** Las distribuciones observadas no justifican por sí mismas seleccionar un umbral estadístico concreto.
- **Estado:** No existe todavía un umbral definitivo de robust_z ni una regla definitiva de clasificación.

### Siguiente paso metodológico

- **Evidencia:** Los experimentos permiten construir un baseline contextual B30 y calcular medidas robustas de desviación sobre 2026.
- **Interpretación:** El siguiente paso será diseñar y evaluar un detector de posibles ineficiencias que combine el baseline contextual y medidas robustas de desviación.
- **Estado:** Pendiente de evaluación; no se asumirá todavía que un umbral estadístico concreto sea correcto.

## Información proporcionada

- Según información proporcionada por el responsable del proyecto, los datos de 2026 se consideran más fiables debido a la evolución de los dispositivos o del sistema de medición. Esta afirmación se registra como información proporcionada sobre los datos y no como un hecho estadístico demostrado.

## Pendiente

- Método definitivo de detección.
- Variables definitivas utilizadas por el detector.
- Umbrales de alerta.
- Método definitivo de construcción del *baseline*.
- División temporal exacta del conjunto de datos.
- Métricas de evaluación.
- Estrategia de evaluación sin *ground truth*.
- Formato definitivo de las alertas.
- Arquitectura definitiva de N8N.
- Modelo GPT concreto.
- Interfaz conversacional.

## Decisión confirmada — Evaluación operacional SQL por `trip_id`

- `POST /evaluate` continúa siendo el endpoint analítico genérico y recibe el contrato completo del viaje.
- `POST /evaluate-trip` constituye la integración operacional SQL basada en el identificador y devuelve el mismo resultado consolidado; no está disponible en modo CSV.
- N8N podrá solicitar una evaluación enviando únicamente `trip_id`.
- `SqlHistoricalRepository` es responsable de la lectura parametrizada del viaje y de adaptar las unidades al contrato analítico, incluida la conversión de `Consumo` de litros a mililitros y la preservación de `NULL` como `None`.
- La incorporación de esta entrada no modifica detectores, baselines, umbrales, reglas de consolidación ni el comportamiento de `/evaluate`.

## En investigación

- Existen valores extremos en las variables analizadas; deberán estudiarse antes de establecer el método definitivo de detección.

## Trazabilidad

## Decisión confirmada — Evaluación del componente conversacional

- Los detectores deterministas y la consolidación son la fuente de verdad; el
  LLM generará explicaciones sin modificar ni inferir estados analíticos.
- Al no existir *ground truth* de ineficiencias reales, la evaluación comprueba
  fidelidad numérica y semántica a la salida analítica y aspectos cualitativos
  mediante rúbrica. No valida causalidad ni rendimiento frente a ineficiencias.
- Las métricas semi-sintéticas de los detectores corresponden a una evaluación
  distinta y no son resultados del componente conversacional.
- Se propone una muestra funcional estratificada de hasta 20 casos reales de
  2026: cinco por cada estrato definido en `docs/metodologia.md`. No se considera
  estadísticamente representativa de la operación logística.
- La selección es reproducible y registra carencias si no existen suficientes
  casos; nunca se fuerzan categorías mediante cambios en reglas o datos.

Las decisiones registradas pueden cambiar durante la investigación. Cualquier cambio posterior debe registrarse en este documento, indicando su estado y la información o evidencia que lo justifica.

## Decisión confirmada — Origen de datos del histórico

- SQL Server y `dbo.WF_OPERATIVA_CAMIONES` constituyen la fuente operacional del histórico en el entorno empresarial.
- El repositorio SQL realiza exclusivamente lectura de las columnas requeridas y limita el histórico al intervalo `[2024-01-01, 2026-01-01)` mediante parámetros SQL.
- `Consumo` se almacena/proporciona en litros en la tabla SQL. `SqlHistoricalRepository` lo normaliza a mililitros (`litros × 1000`) al construir el registro que consume la capa analítica.
- CSV permanece disponible y es el origen predeterminado para desarrollo y pruebas; su ruta continúa configurándose mediante `TFM_DATA_PATH`.
- La selección entre `csv` y `sql` se configura con `TFM_DATA_SOURCE`.
- Las credenciales y datos de conexión se proporcionan externamente mediante variables de entorno y no se versionan.
- Esta decisión afecta únicamente a la adquisición del histórico. No cambia reglas, umbrales, baselines, consolidación ni ningún otro comportamiento analítico de `DetectorV1` o `TemporalDetectorV1`.

## Decisión confirmada — División temporal del experimento

- El baseline inicial del detector se construirá utilizando los registros correspondientes a 2024 y 2025.
- El comportamiento del detector se evaluará sobre registros correspondientes a 2026.
- La división será temporal y no aleatoria.
- La selección se justifica por la necesidad de evitar utilizar información futura en la construcción del baseline.
- Según información proporcionada sobre los datos, las mediciones de 2026 se consideran más fiables debido a la evolución de los dispositivos de medición. Esta consideración se tratará como información proporcionada y no como una propiedad estadísticamente demostrada.
- La decisión podrá revisarse si durante la evaluación se observa que la calidad o cantidad de datos impide construir un baseline adecuado.

## Decisión confirmada — Criterio inicial de registros para el *baseline* por vehículo

- Se utilizarán 100 registros históricos válidos como criterio inicial para construir el *baseline* de cada vehículo.
- Este criterio podrá revisarse después de evaluar la estabilidad del *baseline*.

## Decisión definitiva — Detector de consumo v1

- **Baseline seleccionado:** B30, definido por vehículo y rango de distancia cuando el contexto dispone de un mínimo de 30 observaciones, con *fallback* al *baseline* del vehículo cuando no se alcanza ese mínimo.
- **Medida robusta seleccionada:** mediana y MAD calculadas exclusivamente sobre el histórico.
- **Regla seleccionada:** desviación relativa > 50 % AND `robust_z` > 2.
- **Benchmark definitivo alineado:** Sobre 6.427 registros evaluables, la regla marcó el 10,14 % del conjunto de control y obtuvo una especificidad experimental del 89,86 %. El *recall* fue del 21,44 % para una perturbación de +25 %, del 48,87 % para +50 %, del 82,70 % para +100 %, del 92,95 % para +200 % y del 98,38 % para +500 %.
- **Alcance de las métricas:** Estas cifras proceden de perturbaciones semi-sintéticas y de un control experimental. No representan precisión, sensibilidad ni especificidad frente a ineficiencias reales. El conjunto de control no constituye un *ground truth* negativo empresarial.
- **Interpretación de la salida:** Todo caso marcado deberá interpretarse únicamente como «desviación a revisar».
- **Estado:** Decisión metodológica definitiva para la primera versión del detector de consumo.

## Decisión confirmada — DetectorTemporalV1

- **Interpretación:** «desviación temporal respecto al comportamiento histórico del vehículo en viajes de distancia comparable».
- **Variable:** `minutes_per_km`, calculada como duración en minutos dividida por distancia en kilómetros.
- **Elegibilidad:** La señal temporal v1 se limita a viajes de 2026 con duración positiva, distancia superior a 1 km y vehículo con al menos 100 observaciones históricas válidas en 2024-2025.
- Los viajes de hasta 1 km quedan fuera porque `minutes_per_km` presenta en ese rango un régimen estadístico claramente más inestable, con dispersión, percentiles extremos y porcentajes de superación superiores. Esta exclusión no implica que dichos registros sean inválidos.
- **Baseline:** B30 por vehículo y rango de distancia cuando existen al menos 30 observaciones históricas, con *fallback* al baseline del vehículo; se utilizan mediana y MAD históricas.
- **Regla seleccionada:** desviación relativa > 50 % AND `robust_z` > 2.
- **Benchmark semi-sintético:** Sobre 9.644 casos evaluables, la regla marcó el 13,03 % del control experimental y obtuvo una especificidad experimental del 86,97 %. El *recall* fue del 24,83 % para una perturbación de +25 %, del 40,18 % para +50 %, del 65,84 % para +100 %, del 87,33 % para +200 % y del 98,66 % para +500 %.
- **Alcance de las métricas:** Estas métricas proceden de perturbaciones temporales artificiales controladas y no representan rendimiento frente a ineficiencias reales.
- **Semántica:** `REVIEW` identifica una desviación temporal a revisar. No confirma ineficiencias ni permite atribuir una explicación concreta al comportamiento observado.
- **Estado:** Decisión metodológica confirmada para la primera versión del detector temporal.

## Decisión confirmada — Consolidación de resultados analíticos

- Los detectores de consumo y comportamiento temporal son las fuentes de verdad analítica y conservan íntegramente sus resultados individuales en la salida consolidada.
- `overall_status` será `REVIEW` si cualquier señal está en revisión; será `NO_RELEVANT_DEVIATION` si ninguna está en revisión y al menos una es evaluable; y será `NOT_EVALUABLE` si ambas son no evaluables.
- `analysis_coverage` será `COMPLETE` cuando ambas señales sean evaluables, `PARTIAL` cuando exactamente una sea no evaluable y `NONE` cuando ambas sean no evaluables.
- `review_signals` contendrá exclusivamente las señales individuales con estado `REVIEW`.
- La API constituye una frontera de acceso a la capa analítica y no decide estados, cobertura ni revisiones.
- GPT no decidirá desviaciones analíticas. Una futura capa de explicación podrá describir resultados ya calculados, pero no sustituir ni alterar las decisiones de los detectores.
- La integración con N8N o GPT permanece como fase posterior y no se registra todavía como implementada.
