# Registro de decisiones

Este documento conserva la evolución de las decisiones del TFM y distingue las
decisiones cerradas, las hipótesis sustituidas y los pendientes reales.

## Decisiones cerradas para la v1

### Alcance y semántica

- El prototipo identifica desviaciones respecto al comportamiento histórico.
- No existe *ground truth* que confirme ineficiencias reales.
- `REVIEW` significa «desviación que requiere revisión», sin confirmar
  ineficiencia o causalidad. `NOT_EVALUABLE` no significa normalidad.
- El LLM solo explica resultados del sistema determinista.
- No existe una variable de carga disponible; el análisis carga-consumo no
  forma parte de la v1.

### División temporal, baselines y detectores

- Los datos válidos de 2024–2025 construyen los baselines; 2026 se reserva para
  evaluación mediante una división temporal no aleatoria.
- Cada vehículo requiere 100 observaciones históricas válidas.
- B30 usa mediana y MAD del contexto vehículo-rango con al menos 30
  observaciones y *fallback* al vehículo.
- Consumo usa L/100 km; temporal usa `minutes_per_km` y exige más de 1 km. La
  señal temporal no representa tiempo de parada.
- Ambas señales aplican
  `relative_deviation > 0.50 AND robust_z > 2`.
- Los estados son `REVIEW`, `NO_RELEVANT_DEVIATION` y `NOT_EVALUABLE`.
- Consumo cero o `NULL` no se interpreta como cero real. `NULL` se conserva
  ausente, produce `MISSING_CONSUMPTION` y no impide la evaluación temporal.

### Consolidación

- El resultado es `REVIEW` si alguna señal está en revisión;
  `NO_RELEVANT_DEVIATION` si no hay revisión y alguna es evaluable; y
  `NOT_EVALUABLE` si ninguna es evaluable.
- La cobertura es `COMPLETE`, `PARTIAL` o `NONE` para dos, una o ninguna señal
  evaluable. Los resultados individuales se conservan bajo `signals`.

### Datos, API y orquestación

- CSV permanece como fuente de desarrollo y SQL Server es la fuente
  operacional de solo lectura.
- El consumo SQL en litros se convierte a mililitros en el adaptador.
- FastAPI expone `GET /health`, `POST /evaluate` y `POST /evaluate-trip`; este
  último recupera el viaje por `trip_id` en modo SQL.
- La integración SQL Server → FastAPI y el workflow n8n operacional se han
  validado fuera del repositorio. No son tests automáticos end-to-end ni un
  despliegue productivo.
- El workflow de evaluación conversacional v1 se conserva sanitizado en
  `n8n/conversational_evaluation_v1.json`, sin credenciales ni metadatos de
  instalación.

### Evaluación cerrada

- Los benchmarks semi-sintéticos evalúan respuestas controladas, no rendimiento
  frente a ineficiencias reales.
- En consumo, sobre 6.427 registros evaluables, el control marcó 10,14 % y la
  especificidad experimental fue 89,86 %. El *recall* fue 21,44 %, 48,87 %,
  82,70 %, 92,95 % y 98,38 % para +25 %, +50 %, +100 %, +200 % y +500 %.
- En temporal, sobre 9.644 casos evaluables, el control marcó 13,03 % y la
  especificidad experimental fue 86,97 %. El *recall* fue 24,83 %, 40,18 %,
  65,84 %, 87,33 % y 98,66 % para las mismas perturbaciones.
- Estas métricas no son precisión, sensibilidad o especificidad frente a
  ineficiencias reales.
- La evaluación conversacional v1 se cerró con 20 casos estratificados,
  98,96 % de cumplimiento aplicable y claridad/utilidad media de 3,95/5. Hubo
  un único incumplimiento de fidelidad numérica. La rúbrica y límites constan en
  `docs/metodologia.md`.

## Evolución histórica y evidencia

Esta sección conserva las hipótesis y decisiones intermedias necesarias para
reconstruir la evolución del proyecto. Las entradas marcadas como `SUSTITUIDA`
no son pendientes actuales.

### Exploración inicial y división temporal

- **Hipótesis inicial:** estudiar una división temporal entre datos históricos
  y posteriores, y comparar referencias basadas en todo el histórico con otras
  que priorizaran contexto reciente o comparable.
- **Evidencia:** la exploración disponible contenía observaciones de 2024, 2025
  y 2026. La separación temporal permitía construir referencias sin utilizar
  información futura del periodo evaluado. También se informó que las
  mediciones de 2026 podían ser más fiables por la evolución de los dispositivos;
  esta última consideración se trató como información proporcionada, no como
  propiedad estadística demostrada.
- **Decisión v1:** 2024–2025 se destinan a construcción de baselines y 2026 a
  evaluación. La hipótesis de mantener la división sin concretar queda
  `SUSTITUIDA` por esta decisión.

### Evolución del baseline A/B30/B50

- **Hipótesis inicial:** utilizar un baseline histórico general por vehículo y
  estudiar si la distancia aportaba contexto relevante.
- **Experimento:** se compararon A, B30 y B50. A representa la referencia del
  vehículo; B30 y B50 emplean contexto vehículo-rango con mínimos respectivos
  de 30 y 50 observaciones y recurren al vehículo cuando el contexto no alcanza
  el mínimo.
- **Evidencia:** las distribuciones de L/100 km variaban por rango dentro de un
  mismo vehículo. B30 ofreció mayor uso del contexto que B50 sin perder el
  fallback, mientras los análisis de sensibilidad mostraron el compromiso
  entre excluir trayectos cortos y conservar cobertura.
- **Decisión v1:** B30 con un mínimo de 100 observaciones históricas válidas por
  vehículo. A, B50 y la selección aún abierta quedan `SUSTITUIDAS` como
  decisiones operativas, aunque se conservan como comparadores experimentales.

### MAD, robust_z y regla de consumo

- **Hipótesis inicial:** estudiar estadísticas robustas antes de recurrir a
  modelos más complejos y analizar valores extremos sin convertirlos
  directamente en alertas.
- **Evidencia:** se calcularon mediana, MAD, desviación relativa y `robust_z`
  sobre B30. En la fase exploratoria previa de análisis MAD sobre datos de 2026,
  MAD pudo calcularse para 6.665 registros evaluables sin casos de MAD igual a
  cero. Las colas extremas aparecieron con
  mayor frecuencia relativa en trayectos cortos, pero no exclusivamente en
  ellos y sin evidencia causal.
- **Conciliación de poblaciones:** los 6.665 registros pertenecen a esa fase
  exploratoria; los 6.427 corresponden a la población final evaluable del
  benchmark de consumo v1 tras aplicar los criterios definitivos de
  elegibilidad, incluido el mínimo de 100 observaciones históricas válidas por
  vehículo. La diferencia refleja el cambio de elegibilidad entre fases, no
  una contradicción ni un recálculo de las métricas publicadas.
- **Experimento:** se compararon reglas AND/OR y distintos puntos de corte, y se
  realizó un benchmark semi-sintético mediante perturbaciones controladas del
  consumo.
- **Decisión v1:** mediana y MAD históricas, y regla estricta
  `relative_deviation > 0.50 AND robust_z > 2`. La ausencia de umbral definitivo
  y las demás reglas candidatas quedan `SUSTITUIDAS` para la v1.

### De «tiempos de parada» a señal temporal

- **Hipótesis inicial (`SUSTITUIDA`):** estudiar tiempos de parada a partir de
  la duración disponible.
- **Evidencia:** los datos no permiten separar conducción, espera y parada. La
  duración total dividida por distancia sí permite comparar el comportamiento
  temporal de viajes del mismo vehículo en rangos de distancia semejantes. El
  indicador resultó especialmente inestable en viajes de hasta 1 km.
- **Decisión v1:** definir la señal como `minutes_per_km`, excluir de su
  evaluación viajes de hasta 1 km y aplicar B30, mediana, MAD y la misma regla
  conjunta que en consumo. No se denomina ni interpreta como tiempo de parada.

### Análisis carga-consumo

- **Hipótesis inicial (`SUSTITUIDA` para la v1):** incorporar la carga como
  contexto explicativo del consumo.
- **Evidencia:** no existe una variable de carga disponible en los datos
  accesibles.
- **Decisión v1:** no implementar análisis carga-consumo ni inferir carga desde
  otras variables. Solo podría reabrirse con una variable fiable futura.

### Semántica de REVIEW y consolidación

- **Problema metodológico:** no existe *ground truth* que permita etiquetar
  viajes como ineficiencias reales ni atribuir causas a una desviación.
- **Decisión semántica:** `REVIEW` identifica una desviación a revisar;
  `NO_RELEVANT_DEVIATION` indica que no se cumplen conjuntamente los criterios;
  `NOT_EVALUABLE` indica ausencia de evaluación y no normalidad.
- **Evolución técnica:** tras implementar señales independientes, se añadió una
  consolidación que conserva ambas salidas, calcula `overall_status`,
  `analysis_coverage` (`COMPLETE`, `PARTIAL`, `NONE`) y `review_signals` sin
  recalcular los detectores.

### Integración SQL y API

- **Hipótesis inicial:** separar SQL Server, análisis, orquestación n8n y
  explicación GPT.
- **Evolución:** primero se mantuvo CSV como interfaz local; después se aisló un
  repositorio SQL de solo lectura, se incorporó FastAPI y se añadió
  `/evaluate-trip` para recuperar un viaje por `trip_id` sin cambiar el contrato
  de `/evaluate`.
- **Decisión v1:** SQL Server es la fuente operacional, CSV permanece para
  desarrollo y FastAPI es la frontera estable. La integración SQL Server → API
  fue validada externamente; n8n y GPT permanecen fuera del motor analítico.

### Evaluación semi-sintética

- **Motivación:** la falta de *ground truth* impedía interpretar registros
  reales como positivos o negativos confirmados.
- **Evolución:** se introdujeron perturbaciones controladas de +25 %, +50 %,
  +100 %, +200 % y +500 % sobre consumo y señal temporal, preservando la
  separación 2024–2025/2026 y evitando contaminar baselines.
- **Decisión v1:** usar *recall*, tasa marcada del control y especificidad
  experimental solo como métricas del experimento semi-sintético. No se
  interpretan como precisión frente a ineficiencias reales.

### Evaluación conversacional v1

- **Diseño:** muestra funcional estratificada de 20 casos, con respuestas
  generadas mediante n8n antes de la puntuación y una rúbrica de fidelidad y utilidad fijada
  previamente.
- **Evidencia:** se obtuvo un 98,96 % de cumplimiento sobre criterios aplicables
  y 3,95/5 de claridad/utilidad media, con un único incumplimiento de fidelidad
  numérica.
- **Decisión v1:** la evaluación conversacional queda cerrada para el modelo y
  *prompt* congelados. El LLM explica la salida determinista y no decide
  anomalías. El workflow empleado se conserva mediante un export sanitizado.

### Tratamiento posterior de Consumo=NULL

- **Riesgo detectado:** el repositorio SQL conservaba `NULL` como `None`, pero
  la normalización intentaba convertirlo directamente a número y podía impedir
  que el viaje llegara a los detectores y a la API.
- **Evidencia:** un test mínimo reprodujo la excepción en la normalización y
  los tests posteriores verificaron todo el recorrido con dobles, sin acceder a
  SQL Server real.
- **Decisión v1:** `NULL` es ausencia de dato, nunca cero. Consumo produce
  `NOT_EVALUABLE` con `MISSING_CONSUMPTION`; temporal puede continuar y la
  consolidación puede devolver cobertura `PARTIAL`.

## Pendientes y límites futuros

- Obtener *ground truth* o validación experta operacional si fuera viable.
- Incorporar evaluación interjueces en evaluaciones humanas posteriores.
- Productivizar despliegue, autenticación, observabilidad, gestión de secretos
  y operación de SQL Server, FastAPI y n8n.
- Implementar distribución de alertas si entra en el alcance futuro.
- Evaluar otros modelos o *prompts* antes de generalizar la evaluación v1.
- Revisar carga-consumo solo si se incorpora una variable de carga fiable.

Estos límites no reabren las decisiones analíticas cerradas para la v1.
