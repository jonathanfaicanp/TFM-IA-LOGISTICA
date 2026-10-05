# TFM-IA-LOGISTICA

Prototipo de un sistema analítico para identificar desviaciones de consumo y
comportamiento temporal en viajes logísticos, consolidar ambas señales y
exponer el resultado mediante una API. `REVIEW` significa desviación que
requiere revisión, no ineficiencia confirmada.

## Estado del prototipo

La versión v1 incluye detectores deterministas de consumo y comportamiento
temporal, baselines robustos, consolidación, fuentes CSV y SQL Server, una API
FastAPI, benchmarks semi-sintéticos y una evaluación conversacional cerrada
sobre 20 casos estratificados. También conserva un export sanitizado del
workflow n8n usado para esa evaluación.

El LLM no forma parte del motor de detección: únicamente explica su salida
estructurada. La orquestación operacional n8n se ha probado fuera del
repositorio, pero no se presenta aquí como despliegue productivo ni como prueba
automatizada de extremo a extremo.

## Instalación y tests

Tested with Python 3.14 (entorno verificado: 3.14.3). No se declara un rango
de compatibilidad con versiones que no se han probado.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

La suite no representa cobertura productiva completa: SQL Server real,
n8n y el LLM no se ejercitan mediante tests
automáticos end-to-end dentro del repositorio.

## Ejecución de la API

Desde la raíz del repositorio, el modo demo usa un CSV completamente sintético,
incluido en Git. No necesita datos empresariales ni credenciales SQL:

```powershell
$env:TFM_DATA_SOURCE = "csv"
$env:TFM_DATA_PATH = "examples/sample_operativa.csv"
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

En otra terminal: `Invoke-RestMethod http://127.0.0.1:8000/health`.
Para evaluar un ejemplo inventado:

```powershell
$body = '{"trip_id":"SYNTHETIC_TRIP_NORMAL","vehicle_id":"SYNTHETIC_VEHICLE_001","timestamp":"2026-01-01T12:00:00","distance_m":2000,"consumption_ml":1000,"duration_seconds":360}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/evaluate -ContentType "application/json" -Body $body
```

El sample contiene 100 observaciones históricas inventadas (2024–2025) de un
vehículo, con MAD no nula y contexto ≥30, y tres ejemplos de 2026: normal,
REVIEW y sin referencia. No deriva de filas empresariales. `/evaluate` recibe
el viaje en el cuerpo de la petición; no lo busca en las filas del CSV.

El modo demo es explícito: sin `TFM_DATA_PATH`, se conserva el valor por defecto
`data/datos_operativa.csv` y se falla si no existe; no hay fallback silencioso
al sample. Los datos empresariales reales no están incluidos.

Para SQL Server se configura `TFM_DATA_SOURCE=sql` y se proporcionan fuera del
repositorio `TFM_DB_SERVER`, `TFM_DB_DATABASE`, `TFM_DB_USER`,
`TFM_DB_PASSWORD` y, opcionalmente, `TFM_DB_DRIVER`:

```powershell
$env:TFM_DATA_SOURCE = "sql"
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

No deben versionarse credenciales ni cadenas de conexión. La API expone
`GET /health`, `POST /evaluate` y `POST /evaluate-trip`; el último requiere el
modo SQL y recupera el viaje mediante `trip_id`.

## Documentación

- [Requisitos](docs/requisitos.md)
- [Arquitectura](docs/arquitectura.md)
- [Metodología](docs/metodologia.md)
- [Registro de decisiones](docs/decision-log.md)
- [Workflow n8n de evaluación conversacional](n8n/README.md)

Los datos empresariales y los artefactos reales de evaluación permanecen bajo
`data/`, fuera de Git.

## Consultas operacionales por periodo

La ampliación posterior a v1 añade `POST /evaluate-vehicle-period` y
`POST /review-vehicles-period`, disponibles en modo SQL. Véanse los
[contratos, límites y ejemplos](docs/consulta-periodos.md).

## Alcance y licencia

El detector v1 delimita historia 2024–2025 y evaluación 2026. Un viaje de otro
año, incluido 2027, devuelve `NOT_EVALUABLE`; no existe una política automática
de actualización de referencias. Véase el [análisis de alcance](docs/alcance-2026.md).

La licencia del código está pendiente de decisión del autor; no se concede
una licencia implícita por publicar el repositorio.
