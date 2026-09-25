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

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

La suite actual contiene 154 tests (130 de la v1 y 24 de ampliaciones y regresiones operacionales). No representa cobertura productiva
completa: SQL Server real, n8n y el LLM no se ejercitan mediante tests
automáticos end-to-end dentro del repositorio.

## Ejecución de la API

En modo CSV se usa por defecto `data/datos_operativa.csv`; `TFM_DATA_PATH`
permite indicar otra ruta local:

```powershell
$env:TFM_DATA_SOURCE = "csv"
$env:TFM_DATA_PATH = "data/datos_operativa.csv"
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

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

La ampliaci?n posterior a v1 a?ade `POST /evaluate-vehicle-period` y
`POST /review-vehicles-period`, disponibles en modo SQL. V?anse los
[contratos, l?mites y ejemplos](docs/consulta-periodos.md).
