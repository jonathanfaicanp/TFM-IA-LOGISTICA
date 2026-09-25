# Consultas operacionales por periodo

Ampliaci?n de acceso posterior a `v1.0-tfm`. No modifica detectores,
referencias hist?ricas, elegibilidad, umbrales ni consolidaci?n. Los endpoints
anteriores `/health`, `/evaluate` y `/evaluate-trip` conservan su contrato.

## Acceso SQL

`SqlHistoricalRepository.load_operational_rows_between()` a?ade una lectura
operacional acotada, preservando `load_rows_between()` y sus consumidores de
evaluaci?n existentes. Utiliza dos consultas fijas: `VEHICLE_PERIOD_QUERY`
(con `[Nombre Vehiculo] = ?`) y `OPERATIONAL_PERIOD_QUERY` (sin filtro de matrícula).
Ambas consultan `[dbo].[WF_OPERATIVA_CAMIONES]`, con `TOP (?)`, fechas
parametrizadas y orden por `[Fecha de inicio], [Codigo Viaje]`.

Seleccionan explícitamente `Codigo Viaje`, `Codigo Vehiculo`, `Nombre Vehiculo`
(alias `matricula`), `Fecha de inicio`, `Distancia`, `Consumo` y `Duracion`.
No hay interpolaci?n de valores ni funciones sobre la columna temporal.
El campo lógico `matricula` se usa solo para búsqueda y presentación/agrupación operacional;
`Codigo Vehiculo` sigue siendo la identidad del motor y sus referencias.
Se reutiliza el adaptador de unidades SQL existente.

En la fuente operacional verificada, `[Consumo]` ya está en mililitros.
Las cuatro rutas del repositorio comparten el adaptador `_to_analytical_row`,
que conserva esa escala y los valores nulos, sin multiplicar por 1000.
Por ejemplo, SQL `Consumo=4156` llega al contrato interno como 4156 ml y la
normalización del motor obtiene 4.156 litros. Esta corrección sustituye la
suposición anterior de litros y es específica del entorno verificado.
Tras desplegarla se debe reiniciar la API para reconstruir las referencias
en memoria con el histórico adaptado correctamente.

Según la verificación del entorno operacional comunicada por el responsable
de los datos, la columna física `[Matricula]` existe pero no está poblada.
En esta fuente actual la matrícula operativa se almacena en `[Nombre Vehiculo]`,
por lo que ambas consultas seleccionan `[Nombre Vehiculo] AS [matricula]`.
Esta correspondencia es una particularidad verificada del entorno actual,
no una regla universal del esquema ni una detección automática del repositorio.
El contrato público de la API conserva el nombre `matricula`.

Una misma matrícula puede estar asociada históricamente a varios códigos de
vehículo. No se construye una correspondencia previa matrícula → código ni se
elige un único código: cada fila conserva su propio `[Codigo Vehiculo]` y el
servicio evalúa ese viaje con sus referencias correspondientes. La agrupación
operacional por matrícula se realiza después de evaluar y filtrar los estados
`REVIEW`, sin alterar el resultado de ningún viaje.

## Contrato com?n

Ambas operaciones requieren modo SQL y utilizan `AnalyticalService.evaluate()`
para cada viaje recuperado. SQL filtra los datos; nunca decide `REVIEW`.
El LLM tampoco decide estados ni proporciona consultas SQL.

`start_date` y `end_date` deben ser cadenas `YYYY-MM-DD`, con fin mayor o
igual al inicio. Ambos d?as son inclusivos: SQL recibe el intervalo
`[start_date 00:00, end_date + 1 d?a 00:00)`, en la misma referencia horaria
que `Fecha de inicio`, sin conversi?n de zona. Se rechaza `9999-12-31` como
fecha final porque no admite calcular el d?a siguiente.
La capa conversacional/n8n convierte expresiones como ?esta semana? en fechas
expl?citas antes de llamar a la API.

M?ximo: 1.000 viajes por consulta. SQL recupera como m?ximo 1.001 filas para
detectar el exceso; si lo hay, se devuelve HTTP 413 y se pide reducir el
periodo, sin evaluar ni devolver un subconjunto. No hay paginaci?n ni
truncamiento silencioso. El l?mite se aplica antes de filtrar `REVIEW`.

Respuestas de error: 422 para entradas inv?lidas o campos adicionales,
503 sin acceso operacional SQL y 413 por exceso de viajes.
Un periodo sin viajes devuelve 200 con listas vac?as y recuentos cero;
no distingue una matr?cula inexistente de una sin actividad en el periodo.
No se consulta ni devuelve `Conductor`.

Los recuentos `status_counts` y `coverage_counts` incluyen todos los viajes
recuperados, tambi?n los no evaluables. Consultar fechas fuera de 2026 no
cambia el periodo de evaluaci?n de la v1: el motor devuelve `NOT_EVALUABLE`.
`/health` no verifica la conectividad SQL en cada petici?n.

## POST /evaluate-vehicle-period

```json
{"matricula":"TEST001","start_date":"2026-09-01","end_date":"2026-09-07"}
```

La matr?cula es una cadena no vac?a de hasta 32 caracteres. Se recortan los
espacios exteriores, sin transformar guiones ni letras. La comparaci?n SQL
exacta sigue la intercalaci?n de la base de datos.

La respuesta contiene `matricula`, fechas, `total_trips`, `status_counts`,
`coverage_counts` y `results`. Cada elemento de `results` conserva el mismo
contrato consolidado que `/evaluate`: identificadores, fecha, distancia,
estado, cobertura, se?ales de revisi?n y m?tricas de ambos detectores.
Se conservan los tres estados, no solo `REVIEW`.

Ejemplo sin viajes:

```json
{
  "start_date": "2026-09-01", "end_date": "2026-09-07",
  "total_trips": 0,
  "status_counts": {"NOT_EVALUABLE": 0, "NO_RELEVANT_DEVIATION": 0, "REVIEW": 0},
  "coverage_counts": {"COMPLETE": 0, "PARTIAL": 0, "NONE": 0},
  "matricula": "TEST001", "results": []
}
```

## POST /review-vehicles-period

```json
{"start_date":"2026-09-01","end_date":"2026-09-07"}
```

Evalúa todos los viajes del periodo y después selecciona exclusivamente los
resultados con `overall_status=REVIEW`. En el entorno real actual,
`[Nombre Vehiculo]` es un campo mixto: contiene matrículas y nombres u otros
identificadores operacionales; `[Matricula]` sigue sin estar poblada.

Solo para este listado global, `normalize_operational_registration()` aplica
`strip()` y `upper()` y exige coincidencia completa con `^[0-9]{4}[A-Z]{3}$`.
Agrupa únicamente las matrículas reconocidas, usando su forma normalizada.
No extrae matrículas de textos compuestos ni utiliza un LLM. Los nulos también
se excluyen del listado. Es una regla de presentación operacional, no un
criterio analítico ni una comprobación de que la matrícula exista legalmente.
La consulta individual y las consultas SQL permanecen sin cambios.

`total_trips`, `status_counts` y `coverage_counts` conservan todos los resultados
analíticos, incluidos los excluidos del listado. Se añaden dos campos:

- `excluded_review_trips`: viajes REVIEW excluidos por formato o valor nulo.
- `excluded_review_identifiers`: identificadores distintos entre esos viajes,
  contados después de `strip().upper()`; nulo cuenta como un identificador
  ausente distinto de la cadena vacía. No se publican sus nombres.

La suma de `review_count` en `vehicles` más `excluded_review_trips` coincide
con `status_counts.REVIEW`. La agrupación no cambia códigos ni evaluaciones.

Ejemplo ilustrativo con identificadores sint?ticos:

```json
{
  "start_date": "2026-09-01", "end_date": "2026-09-07",
  "total_trips": 3,
  "status_counts": {"NOT_EVALUABLE": 1, "NO_RELEVANT_DEVIATION": 1, "REVIEW": 1},
  "coverage_counts": {"COMPLETE": 2, "PARTIAL": 0, "NONE": 1},
  "vehicles": [{"matricula": "0001ABC", "review_count": 1, "trip_ids": ["R1"]}],
  "excluded_review_trips": 0,
  "excluded_review_identifiers": 0
}
```

## Ejecuci?n y pruebas

Se mantiene el arranque documentado en el README y la configuraci?n SQL
externa existente. No se a?aden credenciales ni nuevas variables de entorno.

```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
python -m unittest discover -s tests -v
```

Las pruebas nuevas emplean hist?ricos sint?ticos y conexiones SQL simuladas.
No validan conectividad, esquema ni intercalaci?n contra un servidor real.
