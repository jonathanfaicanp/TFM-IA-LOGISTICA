# Reproducción de la política de calidad y alcance operacional

Revisión: 5 de octubre de 2026. La política pertenece exclusivamente a la
capa de evaluación final. No cambia DetectorV1, los umbrales congelados,
los endpoints operacionales ni los resultados históricos.

## Script reproducible

`scripts/evaluate_final_2026_quality_policy.py` acepta un CSV explícito con
las columnas Codigo Viaje, Codigo Vehiculo, Fecha de inicio, Distancia,
Consumo y Duracion, separado por punto y coma. Reutiliza AnalyticalService,
ambos detectores y consolidate_results. Construye referencias 2024–2025 y
evalúa los registros de 2026 con la configuración vigente congelada.

```powershell
python -B scripts/evaluate_final_2026_quality_policy.py --input data/datos_operativa.csv
```

El resultado es JSON agregado en stdout, sin viajes ni vehículos individuales.
`--output` permite escribir un archivo JSON nuevo; se rechaza sobrescribir
uno existente. El dataset empresarial debe permanecer privado y no se incluye
en Git. No se ejecutan benchmarks ni generación conversacional.

Antes del 20/08/2026 el consumo se evalúa normalmente. Desde ese día el
registro se conserva, pero su señal de consumo se marca NOT_EVALUABLE con
motivo DATA_QUALITY_NON_COMPARABLE_CONSUMPTION_FINAL_EVALUATION. Se eliminan
las métricas de comparación de esa señal; no se alteran las magnitudes
derivadas por la normalización vigente ni se aplica una unidad hipotética.
La señal temporal se conserva exactamente y se vuelve a consolidar usando
las mismas reglas. No se atribuye la discontinuidad a un proveedor, hardware,
API o ETL ni se da por confirmada la semántica de los regímenes.

## Reproducción del snapshot privado vigente

| Población de consumo | Viajes | Evaluables | REVIEW | NO_RELEVANT_DEVIATION | NOT_EVALUABLE |
|---|---:|---:|---:|---:|---:|
| Antes de política, todo 2026 | 13484 | 6427 | 652 | 5775 | 7057 |
| Comparación final, antes del 20/08 | 12955 | 6230 | 455 | 5775 | 6725 |
| Con política, todos los viajes retenidos | 13484 | 6230 | 455 | 5775 | 7254 |

Los 6725 NOT_EVALUABLE corresponden a la población comparable; al conservar
los 529 viajes del lote posterior como no evaluables para consumo, el total
de esa señal es 7254. No se deben mezclar ambos denominadores.

6427 → 6230 evaluables = −197; 652 → 455 REVIEW = −197.
La comprobación individual devuelve affected_evaluable_before=197,
affected_review_before=197, affected_review_rate=1,0 y
all_affected_evaluable_were_review=true. Los conteos se obtienen de los datos,
no son constantes del programa; en otras entradas el indicador puede ser false
o null si no hay casos afectados.

«En el lote afectado, los 197 registros que resultaban evaluables para
consumo con la lógica previa eran marcados como REVIEW. Tras aplicar la
política de calidad dejaron de participar en la comparación histórica de
consumo.» No se les asignan etiquetas de falsos positivos reales.

Consolidación final: 13484 viajes; 1507 REVIEW, 9172 NO_RELEVANT_DEVIATION
y 2805 NOT_EVALUABLE. Cobertura: 5195 COMPLETE, 5484 PARTIAL y 2805 NONE.
Señales REVIEW: consumo 455, temporal 1257, ambas 205; solo consumo 250,
solo temporal 1052. Se verificó temporal inalterado. Cambian 181 estados
globales, 197 coberturas y 197 conjuntos de review_signals.

Fuente: reproducción en lectura del snapshot con el script anterior y
contraste con los agregados históricos de la política final bajo data/.
No se sustituyen esos artefactos. Véase también
[métricas finales](metricas-finales-benchmark.md).

## Auditoría de los endpoints operacionales

En `src/api.py`, `evaluate_period()` obtiene las filas del repositorio SQL y
ejecuta `analytical_service.evaluate(row)` sobre cada una. No importa ni
aplica la política de calidad. `/evaluate-vehicle-period` y
`/review-vehicles-period` comparten esa ruta; también `/evaluate` y
`/evaluate-trip` delegan directamente en el servicio sin la política final.
Consumo posterior al 20/08 sigue pasando normalmente a DetectorV1.

El repositorio operacional consulta SQL Server mediante
`load_operational_rows_between()`. Las fechas vienen del cuerpo de la petición:
start_date inclusivo y end_date inclusivo, implementado como límite superior
exclusivo a medianoche del día siguiente. No hay una semana de septiembre
hardcodeada. El límite es 1000 viajes; si se recuperan 1001, la API rechaza
la petición en lugar de presentar un resultado truncado. El endpoint global
filtra identificadores de presentación con formato matrícula, sin modificar
los resultados analíticos ni aplicar la exclusión de calidad.

El snapshot formal termina el 25/08/2026. No contiene la semana operacional
de finales de septiembre. En esta sesión faltan TFM_DB_SERVER,
TFM_DB_DATABASE, TFM_DB_USER y TFM_DB_PASSWORD; no se intentó conectarse ni
se solicitaron credenciales. No se dispone de export del workflow operacional,
petición exacta o versión desplegada que permita reconstruir aquella semana.
El export local de evaluación Luna no llama a los endpoints por periodo.

## Clasificación de la captura de septiembre

**C: no determinable con la evidencia disponible.** Está comprobado que
el código operacional actual no aplica la política final; si la captura se
generó con esa ruta sin una preparación externa, correspondería a B. No se
afirma esa procedencia como hecho sin imagen, workflow o registro de ejecución.

Los 155 viajes semanales y los 43 REVIEW de un vehículo son cifras comunicadas
por el autor/director, no reproducidas localmente. No se pueden comparar
directamente con mediana 10, P90 18, P95 20 y máximo 27 REVIEW por día del
snapshot formal: cambian ventana, población y posiblemente política. Una
cifra semanal por vehículo tampoco tiene el denominador de una cifra diaria
global. El impacto de aplicar la política a esa semana no puede calcularse
con los datos disponibles. No se cambia el endpoint operacional.

La captura no debe presentarse como evidencia inequívoca del comportamiento
final. Su uso exige indicar fuente, periodo, versión y política, o sustituirla
por una demo sintética identificada como tal.

## Captura y privacidad

No se localizó la captura de finales de septiembre en el repositorio ni en
los recursos de capturas accesibles de Documents/MASTER. La carpeta externa
«capturas par ael tfm» contiene tres imágenes fechadas 03/09/2026, que no
acreditan la captura indicada. No se encontró una referencia a la imagen en
docs/ ni una memoria LaTeX local. Por tanto, no puede confirmarse su ruta,
los identificadores que muestra, la presencia de un webhook ni si sigue activo.
No se reproduce ninguna URL sensible ni se invoca un webhook para comprobarlo.

Se propone una nueva demo con datos inventados, identificadores 0000ZZZ,
0001ZZZ o SYNTHETIC_VEHICLE_001, y sin URL visible o con localhost. Puede
usarse examples/sample_operativa.csv para el endpoint de evaluación individual.
Los endpoints por periodo requieren SQL; una demo de esos endpoints necesitaría
un repositorio de fixtures sintéticas o una base de demo separada, rotulada
como demostración, sin simular que son volúmenes operacionales observados.
No se recomienda difuminar parcialmente la captura real. Si el responsable
confirma que expone un webhook activo, debe regenerarlo/rotarlo; su vigencia
no está comprobada aquí.

Los tests saneados del working tree ya no contienen los identificadores reales
retirados, pero el HEAD y el historial antiguo sí los conservan. Hasta publicar
la sanitización, la versión remota actual también conserva ese contenido.
Un repositorio público limpio debería generarse con archivos revisados y
datasets sintéticos, sin importar el historial anterior ni temp/, data/ o
recursos privados. El repositorio histórico puede conservarse privado para
trazabilidad. No se ejecutó reescritura de historial, force push, rebase ni
movimiento de tags; no se verificó ni cambió la visibilidad remota.
