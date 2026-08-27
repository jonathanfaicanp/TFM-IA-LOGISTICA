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

## En investigación

- Existen valores extremos en las variables analizadas; deberán estudiarse antes de establecer el método definitivo de detección.

## Trazabilidad

Las decisiones registradas pueden cambiar durante la investigación. Cualquier cambio posterior debe registrarse en este documento, indicando su estado y la información o evidencia que lo justifica.

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
