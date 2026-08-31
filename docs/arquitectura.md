# Arquitectura

Este documento describirá la arquitectura del proyecto cuando existan decisiones y evidencias que la respalden.

## Decisiones confirmadas

La capa analítica reutilizable mantiene un flujo local y desacoplado de integraciones externas:

`datos -> preparación -> baselines B30 -> detectores v1 -> salidas estructuradas`

- **Preparación común:** normaliza tipos y fechas, convierte unidades, asigna el rango de distancia y calcula el indicador correspondiente a cada señal.
- **Baselines B30:** se construyen exclusivamente con registros históricos válidos de 2024 y 2025. Exigen al menos 100 observaciones por vehículo y utilizan mediana y MAD del contexto vehículo-rango cuando existen al menos 30 observaciones; en caso contrario, utilizan el *fallback* del vehículo.
- **Señal de consumo:** `DetectorV1` evalúa registros de 2026 con consumo y distancia positivos mediante L/100 km y la regla desviación relativa > 50 % AND `robust_z` > 2.
- **Señal temporal:** `TemporalDetectorV1` evalúa registros de 2026 con duración positiva y distancia superior a 1 km mediante `minutes_per_km` y la regla desviación relativa > 50 % AND `robust_z` > 2. Los viajes de hasta 1 km producen `NOT_EVALUABLE` para esta señal, sin considerarse datos inválidos por ese motivo.
- **Salidas estructuradas independientes:** cada detector devuelve sus propios datos normalizados, referencia histórica, medidas de desviación, tipo de *baseline*, estado y motivo. Las estructuras pueden serializarse posteriormente a JSON, pero no constituyen todavía una API externa.
- **Semántica:** `REVIEW` significa únicamente «desviación a revisar».
- **Ausencia de causalidad:** ninguna de las dos señales identifica ni confirma el motivo de una desviación.
- **Integraciones posteriores:** N8N y GPT quedan fuera del detector v1 y corresponden a fases posteriores de orquestación y explicación.

### Consolidación de señales

Los resultados independientes de consumo y comportamiento temporal se entregan a una capa de consolidación que no modifica sus cálculos:

`DetectorV1 + TemporalDetectorV1 -> consolidación -> API`

El contrato consolidado contiene la identidad del viaje, `overall_status`, `analysis_coverage`, las señales en revisión y los resultados estructurados originales bajo `signals.consumption` y `signals.temporal`.

- `overall_status` es `REVIEW` si cualquier señal está en revisión; es `NO_RELEVANT_DEVIATION` si ninguna está en revisión y al menos una es evaluable; y es `NOT_EVALUABLE` cuando ninguna señal es evaluable.
- `analysis_coverage` es `COMPLETE` cuando ambas señales son evaluables, `PARTIAL` cuando sólo una es evaluable y `NONE` cuando ninguna lo es.
- `review_signals` incluye exclusivamente los nombres de las señales cuyo estado individual es `REVIEW`.

### Frontera HTTP

La API FastAPI constituye la frontera estable entre la capa Python y futuros consumidores. Expone `GET /health` y `POST /evaluate`. Los detectores se inicializan una vez con el histórico al arrancar el servicio; la ruta local puede configurarse mediante `TFM_DATA_PATH` y no se envía el histórico en cada petición.

La API valida únicamente datos de entrada del viaje. Los estados, cobertura, referencias históricas, puntuaciones robustas y decisiones de revisión siempre son calculados internamente. La detección y la futura explicación permanecen separadas: ni la API ni futuros componentes N8N/GPT sustituyen las decisiones analíticas de los detectores. La integración con N8N/GPT no está implementada todavía.

### Origen del histórico

El arranque selecciona el origen mediante `TFM_DATA_SOURCE`: `csv` (valor por defecto) conserva `TFM_DATA_PATH` para desarrollo y pruebas, mientras que `sql` obtiene de SQL Server únicamente los registros de 2024 y 2025 necesarios para construir los detectores. El acceso SQL está aislado en un repositorio de solo lectura y utiliza consultas parametrizadas con columnas explícitas. La tabla SQL proporciona `Consumo` en litros; el repositorio lo convierte a mililitros antes de entregar cada registro, preservando así el contrato analítico existente.

SQL Server será la fuente operacional en el entorno empresarial. Su servidor, base de datos, usuario, contraseña y controlador ODBC se suministran externamente mediante `TFM_DB_SERVER`, `TFM_DB_DATABASE`, `TFM_DB_USER`, `TFM_DB_PASSWORD` y, opcionalmente, `TFM_DB_DRIVER`. No se almacenan credenciales en el repositorio. La elección del origen solo cambia la carga del histórico y no modifica la normalización, los baselines, los umbrales, la consolidación ni la lógica de los detectores.

## Decisiones provisionales

- La interfaz pública inicial se implementa como módulos Python en `src/`, sin servicios externos ni capas adicionales.

## Supuestos

No hay supuestos de arquitectura documentados todavía.

## Decisiones pendientes

No hay decisiones de arquitectura pendientes documentadas todavía.

## Cuestiones que requieren investigación

No hay cuestiones de investigación de arquitectura documentadas todavía.

## Cuestiones que requieren validación con datos

No hay cuestiones de validación con datos de arquitectura documentadas todavía.

## Estructura prevista del documento

- Contexto y alcance.
- Componentes y responsabilidades.
- Flujos de información.
- Interfaces e integraciones.
- Seguridad, privacidad y gestión de configuración.
- Riesgos, limitaciones y decisiones relacionadas.
