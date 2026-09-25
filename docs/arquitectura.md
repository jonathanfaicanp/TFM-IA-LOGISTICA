# Arquitectura

La arquitectura v1 separa el motor analítico determinista de las fronteras de
integración y de la explicación en lenguaje natural:

`datos -> normalización -> baselines B30 -> detectores v1 -> consolidación -> API`

Ni n8n ni GPT forman parte del motor de detección ni pueden sustituir sus
estados o cálculos.

## 1. Pipeline analítico

La preparación normaliza tipos, fechas y unidades, asigna rangos de distancia y
calcula L/100 km o `minutes_per_km`. Los baselines usan observaciones válidas de
2024–2025, mediana y MAD:

- mínimo de 100 observaciones históricas por vehículo;
- contexto vehículo-rango con un mínimo de 30 observaciones;
- *fallback* al vehículo cuando el contexto no alcanza 30.

`DetectorV1` evalúa consumo mediante L/100 km. `TemporalDetectorV1` evalúa
minutos por kilómetro en viajes de más de 1 km; esta señal no representa tiempo
de parada. Ambos aplican la regla estricta:

`relative_deviation > 0.50 AND robust_z > 2`

Los estados son `REVIEW`, `NO_RELEVANT_DEVIATION` y `NOT_EVALUABLE`. `REVIEW`
significa desviación que requiere revisión, no ineficiencia confirmada, y
ninguna señal atribuye causas.

### Consolidación

- `REVIEW` si cualquier señal está en `REVIEW`;
- `NO_RELEVANT_DEVIATION` si no hay `REVIEW` y al menos una señal es evaluable;
- `NOT_EVALUABLE` si ninguna señal es evaluable.

La cobertura es `COMPLETE`, `PARTIAL` o `NONE` según sean evaluables dos, una o
ninguna señal. Los resultados individuales se preservan bajo `signals`.

## 2. Datos y frontera API

CSV es el origen predeterminado para desarrollo local. SQL Server es la fuente
operacional. Su repositorio es de solo lectura, usa consultas parametrizadas y
columnas explícitas, y carga el histórico `[2024-01-01, 2026-01-01)`.

En la fuente operacional verificada, SQL proporciona `Consumo` en mililitros;
el adaptador conserva esa unidad para el contrato interno, sin multiplicar
por 1000. La normalización analítica convierte después a litros.
Esta unidad corresponde al entorno actual, no a una regla universal de SQL.
`Consumo=NULL` se conserva como
ausencia: consumo produce `NOT_EVALUABLE` con `MISSING_CONSUMPTION`, la señal
temporal puede evaluarse y la cobertura consolidada puede ser `PARTIAL`. El
valor ausente nunca se convierte en cero.

FastAPI constituye la frontera HTTP implementada:

- `GET /health`;
- `POST /evaluate`, con el contrato completo del viaje;
- `POST /evaluate-trip`, que recupera por `trip_id` en modo SQL.

Los detectores se inicializan una vez con el histórico. La API no decide
estados, cobertura o revisiones. La integración SQL Server → FastAPI ha sido
validada externamente; los tests del repositorio emplean dobles y no conectan
con una base real. La configuración SQL se proporciona externamente y no se
versionan credenciales.

## 3. Orquestación n8n operacional

El flujo operacional consulta `POST /evaluate-trip` mediante un `trip_id`,
recibe el resultado consolidado y puede entregarlo a una capa explicativa. Se ha
probado fuera del repositorio, pero no se presenta como despliegue productivo ni
está cubierto por tests automáticos end-to-end.

n8n actúa como orquestador. GPT explica la salida calculada: no decide
desviaciones, no corrige estados y no infiere causas no demostradas.

## 4. Workflow n8n de evaluación conversacional

`n8n/conversational_evaluation_v1.json` reproduce exclusivamente la generación
offline de respuestas de la evaluación conversacional v1:

`Manual Trigger -> lectura JSON -> extracción -> Split Out -> GPT-5.6 Luna -> Edit Fields -> Aggregate -> JSON -> escritura`

Recibe un artefacto anonimizado y guarda `case_id`, `stratum`, `model` y
`response`. No consulta `/evaluate-trip`, no incorpora datos empresariales, no
contiene credenciales y exige configurar una credencial propia de OpenAI.

## Alcance de despliegue

El repositorio implementa el prototipo analítico, sus adaptadores y la frontera
HTTP. No declara una plataforma productiva: autenticación, monitorización, alta
disponibilidad, alertas y despliegue seguro son trabajo futuro.
