# Corrección de escala: evaluación conversacional pendiente de artefactos

Fecha de revisión: 2 de octubre de 2026 (Europe/Madrid).

## Herramienta para ejecutar en el equipo remoto

Preparada `scripts/audit_conversational_sql_correction.py`, sin modificar el
motor y sin conectar a SQL desde este equipo. Utiliza exclusivamente las
variables SQL existentes, consulta el histórico 2024+2025 y los candidatos
de 2026 mediante SqlHistoricalRepository, y evalúa mediante AnalyticalService.

Desde la raíz del repositorio remoto:

```powershell
python -B scripts/audit_conversational_sql_correction.py `
  --cases data/conversational_evaluation/cases.json `
  --output-dir data/conversational_evaluation_corrected_audit
```

La salida debe ser una carpeta nueva bajo data/ y no puede solaparse con el
directorio de los originales. Si ya existe, elegir otro nombre: nunca se
sobrescriben resultados anteriores. No se aceptan credenciales por argumentos.

El matching compara los campos invariantes disponibles con tolerancias
`rel_tol=1e-9` y `abs_tol=1e-9`; no usa magnitudes absolutas de consumo para
resolver identidades. La selección determinista original se reutiliza como
comprobación adicional, pero nunca desempata candidatos compatibles.

Se generarán:

- `case_mapping_private.json`: identidades internas y justificación del match.
- `comparison.json` y `comparison.csv`: valores original/corregido, ratios,
  igualdad y evidencia del factor 1000, solo para UNIQUE_MATCH.
- `audit_summary.md`: matching, cambios, limitaciones y siguiente paso.
- `corrected_cases.json`: únicamente con 20 UNIQUE_MATCH de viajes distintos;
  conserva case_id/estratos y usa la anonimización existente. No reelige una
  muestra distinta. La disponibilidad por estrato se actualiza a la consulta
  actual y se registra si coincide con la selección determinista actual.

Estados e invariantes son también condiciones del matching. Cero cambios en
los emparejados no acredita invariancia de los casos ambiguos o sin match.
Un cambio de SQL desde la generación original puede impedir identificar los
viajes. No se presenta como efecto demostrado del adaptador.

Si aparecen cambios absolutos distintos del factor 1000, el informe pide
detener la preparación de n8n y revisarlos. Un archivo corregido no constituye
aprobación automática de diferencias inesperadas. No se generan respuestas,
se reutilizan respuestas antiguas ni se modifican puntuaciones.

Verificación de la herramienta: **167 tests, OK**, nueve nuevos, incluidos
matching único/ambiguo/ausente, tolerancias, factor 1000, protección de
originales/salidas y ejecución con motor real sobre datos sintéticos y SQL
simulado. No se ejecutó la auditoría sobre la fuente SQL empresarial.

## Actualización: originales recuperados y verificados

**Esta actualización sustituye el estado de ausencia descrito en las secciones
preliminares de abajo.** Los ocho originales recuperados están realmente en
`data/conversational_evaluation/`; la ruta comunicada con sufijo `_original`
no existe en esta copia. Ningún archivo histórico se renombró, movió o modificó.
Se registraron sus SHA-256 en `temp/conversational_original_hashes.json` y se
comprobó que permanecen intactos después de las lecturas.

| Original encontrado | Función |
| --- | --- |
| cases.json | Dataset anonimizado de 20 casos |
| llm_evaluation.json | Plantilla con resultados analíticos y evaluación vacía |
| luna_responses.json | 20 respuestas registradas, todas con modelo GPT-5.6-LUNA |
| luna_evaluation_filled.json | Respuestas incorporadas a las fichas |
| luna_evaluation_scored.json | Fichas con puntuaciones humanas históricas |
| luna_evaluation_summary.json | Resumen histórico |
| luna_review_sheet.csv | Hoja humana puntuada |
| luna_review_sheet_before_scoring.csv | Hoja previa a la puntuación |

Verificaciones sobre los originales:

- 20 case_id distintos; cuatro estratos, cinco casos por estrato.
- Las plantillas, fichas con respuestas y fichas puntuadas tienen los mismos
  case_id y resultados analíticos exactamente iguales a cases.json.
- Las respuestas y modelos de luna_responses.json coinciden con las fichas
  incorporadas. Los archivos registran GPT-5.6-LUNA; el workflow también
  configura gpt-5.6-luna. No hay logs del proveedor para verificar un snapshot
  específico del modelo servido.
- El resumen almacenado contiene 20 casos evaluados, cumplimiento 98,96 %,
  claridad media 3,95 y cero criterios sin puntuar. **Se leyó el resumen
  histórico; no se importaron ni recalcularon puntuaciones.**
- Once casos tienen consumo evaluable y magnitudes absolutas de consumo no
  nulas/no cero. Esto identifica once casos potencialmente expuestos a la
  escala, **no demuestra todavía que estén afectados**.
- Los casos no conservan trip_id, vehicle_id, timestamp ni sus equivalentes
  en las señales. No se ha recuperado un mapping privado de identidades.
- Los archivos no incluyen un commit o fecha verificable de generación;
  timestamps de copia no deben interpretarse como fechas del experimento.

**Punto de parada para reevaluación:** faltan `TFM_DB_SERVER`,
`TFM_DB_DATABASE`, `TFM_DB_USER` y `TFM_DB_PASSWORD`. No se intentó conectar
a SQL ni se solicitaron/escribieron credenciales. Para comprobar empíricamente
la escala de los mismos viajes se necesita además reconstruir su identidad
con un mapping privado o una correspondencia inequívoca sobre el snapshot
original. Los case_id secuenciales no permiten identificar viajes por sí solos.

No se ha dividido automáticamente el consumo entre 1000 para presentarlo
como reevaluación. No se ha utilizado el CSV como sustituto no verificado de
la fuente SQL original. Estados, cobertura, review_signals, desviación relativa
y robust_z originales frente a corregidos siguen pendientes de comparación.
No se ha generado dataset corregido, nuevas respuestas ni nuevas puntuaciones.

## Registro preliminar conservado (anterior a la recuperación)

## Búsqueda exhaustiva adicional solicitada

Se confirmó con `Test-Path` que
`C:\Users\USER\Documents\MASTER\TFM-IA-LOGISTICA\data\conversational_evaluation\`
**no existe en esta copia local**. Data/ contiene dos subcarpetas:
`validation_2025/` y `final_evaluation_2026_frozen_2025/`.

Se enumeraron recursivamente todos los archivos de data/ sin aplicar las
exclusiones de Git: **45 archivos, de los cuales 38 CSV, 5 JSON y 2 Markdown**.
Se leyeron todos los JSON y todos los registros de los CSV, incluidos
`datos_operativa.csv` y los archivos con nombres diferentes de los esperados.
Se comprobaron claves, cabeceras, listas de longitud 20, case_id y marcadores
de casos, respuestas y rúbrica. Ninguno contiene los casos conversacionales
originales, sus respuestas o puntuaciones. Los archivos que coinciden por
`summary` o `evaluation` son datos operativos o resultados analíticos de
baselines, detectores y benchmarks, no la evaluación formal del LLM.

Se amplió además la búsqueda de contenido a los JSON/CSV de todo el repositorio,
incluidos los ignorados, excluyendo únicamente .git y cachés de Python. No se
identificaron casos, respuestas o puntuaciones originales adicionales.
Se leyeron **67 JSON/CSV**, atendiendo también a codificación UTF-16 cuando
correspondía; no quedaron archivos ilegibles. Las coincidencias de contenido
conversacional fueron la rúbrica, el workflow sanitizado y **temp/20 n8n.json**.

Este último es una exportación adicional del workflow original, con 11 nodos,
pinData vacío y sin case_id ni listas de 20 casos. Su nodo de modelo configura
`gpt-5.6-luna`; sus parámetros son idénticos a los del workflow sanitizado.
Contiene las rutas originales de la instalación:

- Entrada: `C:\Users\Informatica\.n8n-files\llm_evaluation.json`.
- Salida: `C:\Users\Informatica\.n8n-files\luna_responses.json`.

La carpeta y ambos archivos **no existen en el entorno actual**, comprobado
con Test-Path. Esta es una ubicación concreta para recuperar los originales
desde la máquina/perfil de la instalación n8n; no acredita que los archivos
permanezcan allí. La exportación se conserva sin modificaciones y fuera de
Git: no se copian sus metadatos de instalación ni credenciales al informe.

Esta ampliación fue solo de localización y lectura. **No se conectó a SQL,
no se evaluaron viajes, no se generaron casos nuevos y no se modificó ningún
artefacto existente bajo data/.** No se presume que los originales no existan
fuera de esta copia local o en el volumen de la instalación de n8n.

**No se ha podido realizar la comparación empírica de los 20 casos.** Los
artefactos originales no están disponibles en las ubicaciones revisadas y el
entorno no dispone de las variables de conexión SQL. No se ha generado un
dataset sustitutivo, respuestas ni puntuaciones. No se ha hecho commit ni push.

## Inventario y evidencia localizada

Se revisaron los archivos del proyecto, incluidos data/ y temp/ ignorados por
Git, y se buscaron los nombres de los artefactos en Documents/MASTER. No se
encontraron los siguientes archivos de la evaluación formal:

| Artefacto | Ruta esperada según las utilidades | Resultado |
| --- | --- | --- |
| Dataset original | data/conversational_evaluation/cases.json | No encontrado |
| Plantilla del LLM | data/conversational_evaluation/llm_evaluation.json | No encontrada |
| Respuestas originales | data/conversational_evaluation/luna_responses.json | No encontradas |
| Respuestas incorporadas | data/conversational_evaluation/luna_evaluation_filled.json | No encontrado |
| Hoja humana | data/conversational_evaluation/luna_review_sheet.csv | No encontrada |
| Puntuaciones | data/conversational_evaluation/luna_evaluation_scored.json o documento evaluado | No localizado |
| Resumen final | data/conversational_evaluation/llm_evaluation_summary.json o salida personalizada | No localizado |

Las rutas son valores predeterminados del código, no prueba de la ubicación
real ni del nombre elegido en la ejecución original. Tampoco pueden determinarse
fechas o commits de generación de esos archivos ausentes.

Sí están disponibles:

- `n8n/conversational_evaluation_v1.json`: workflow sanitizado, commit
  `0a83068`, fechado 4 de septiembre de 2026. Configura modelId
  `gpt-5.6-luna`, nombre `GPT-5.6-LUNA`, prompt de sistema explícito y entrada
  `JSON.stringify($json.analytical_result)`. El nodo del modelo es versión 2.3.
  `options` y `builtInTools` están vacíos: no constan temperatura, seed,
  snapshot del modelo ni límites personalizados. El nombre del modelo en la
  salida se asigna como texto fijo; no es una verificación independiente del
  modelo servido por el proveedor.
- `n8n/README.md` y `docs/metodologia.md`: documentan generación mediante n8n
  y GPT-5.6 Luna, con puntuación humana posterior. Sin respuestas ni logs
  originales no puede confirmarse empíricamente el modelo de cada respuesta.
- `evaluation/rubric_template.json` y utilidades de preparación, incorporación,
  exportación y resumen: definen el formato y C1–C6, pero no son los resultados
  originales.
- Commit `74ac4a61fc672ba1aeb582759fd2de7d8c29b686`, fechado 25 de septiembre
  de 2026: el adaptador pasa de `float(Consumo) * 1000` a `float(Consumo)`;
  conserva NULL. El normalizador actual divide el valor en mililitros por 1000.

## Comparación aún no realizada

| Cuestión solicitada | Estado verificable |
| --- | --- |
| Número de casos con escala incorrecta | Indeterminado; no equivale a cero |
| Estados, cobertura y review_signals invariantes | No comprobado en los 20 casos |
| relative_deviation y robust_z invariantes | No comprobado en los 20 casos |
| Cambios limitados a magnitudes absolutas de consumo | No comprobado en los 20 casos |
| Mismos viajes y case_id reutilizables | No comprobado |
| Dataset corregido | No generado |

El cambio de código identifica magnitudes potencialmente afectadas:
`consumo_litros`, `consumo_l_100km`, baseline y MAD de consumo, y cualquier
escala robusta absoluta almacenada. Bajo la hipótesis de una única escala
constante, podrían dividirse por 1000, pero **no se ha aplicado esa transformación
a un dataset ni se presenta como resultado observado**. Las respuestas del LLM
y la hoja humana también pueden contener magnitudes verbales afectadas; hacen
falta los originales para identificarlas.

## Qué falta para continuar

1. Ubicación o disponibilidad del dataset/plantilla originales, respuestas,
   hoja humana, puntuaciones y resumen, sin sobrescribirlos.
2. Mapping privado case_id → viaje si existe, o los datos originales que
   permitan una reconstrucción inequívoca. El generador elimina viaje,
   vehículo y fecha y no guarda en cases.json el hash usado para ordenar.
   Un case_id por sí solo no identifica un viaje ni prueba que dos muestras
   deterministas procedan de los mismos viajes.
3. Acceso SQL configurado localmente o snapshot de las filas históricas y de
   evaluación usadas. Actualmente están ausentes TFM_DB_SERVER,
   TFM_DB_DATABASE, TFM_DB_USER y TFM_DB_PASSWORD. No se deben incluir sus
   valores en informes ni Git.

Se preservarán hashes de los originales. Se compararán los mismos viajes con
el adaptador corregido, el mismo histórico y campos restantes constantes.
Solo tras verificar los casos se reconstruirá la selección con el procedimiento
existente. Si SQL ha cambiado desde la generación original, esa diferencia
debe separarse del efecto de escala. Diferencias inesperadas obligan a detenerse.

## Procedimiento de repetición preparado, aún no ejecutado

Ruta de destino prevista: `data/conversational_evaluation_corrected/`.
Debe estar separada de los originales. No existe todavía un cases.json corregido
ni una plantilla lista para enviar a n8n.

Después de completar la auditoría, el generador existente admite una salida
nueva; requiere la fuente SQL verificada:

```powershell
python -m evaluation.conversational_dataset --output data/conversational_evaluation_corrected/cases.json
python -m evaluation.prepare_llm_evaluation --input data/conversational_evaluation_corrected/cases.json --output data/conversational_evaluation_corrected/llm_evaluation.json
```

No se ejecutarán estos comandos para reemplazar los originales sin verificar
los viajes y el snapshot. Se comprobarán 20 casos, cinco por cada uno de los
cuatro estratos, y la coincidencia de identidades internas, no solo de case_id.

Archivo que se proporcionará a n8n una vez generado y verificado:
`data/conversational_evaluation_corrected/llm_evaluation.json`.
El workflow lee `/files/llm_evaluation.json`; se debe usar un volumen o
directorio separado de los originales, o cambiar únicamente las rutas de
entrada/salida en una copia del workflow. Mantener modelId, prompt, configuración
disponible y formato del workflow conservado; configurar la credencial en n8n.
No se ejecuta el modelo desde estas utilidades Python.

Recuperar `/files/luna_responses.json` y conservarlo como
`data/conversational_evaluation_corrected/luna_responses.json`, con formato
`[{"responses": [...]}]` y 20 respuestas, cada una con case_id, model y response.
Conservar también logs y export de la ejecución para verificar el modelo y
los parámetros efectivamente utilizados. No sustituirlo por otro modelo si
GPT-5.6 Luna no está disponible; la equivalencia quedaría pendiente.

Después de generar y congelar respuestas reales, se podrán preparar las fichas
humanas vacías, sin copiar puntuaciones anteriores:

```powershell
python -m evaluation.merge_llm_responses --evaluation data/conversational_evaluation_corrected/llm_evaluation.json --responses data/conversational_evaluation_corrected/luna_responses.json --output data/conversational_evaluation_corrected/luna_evaluation_filled.json
python -m evaluation.export_llm_review_sheet --input data/conversational_evaluation_corrected/luna_evaluation_filled.json --output data/conversational_evaluation_corrected/luna_review_sheet.csv
```

Mantener C1–C6, escala 1–5 y el mismo evaluador humano, cuya identidad no puede
confirmarse con los artefactos actualmente disponibles. No se importarán nuevas
puntuaciones ni se calculará un resumen en esta fase. El modelo/configuración
documentados no garantizan respuestas textualmente idénticas en una repetición.

## Verificación realizada

`python -m unittest discover -s tests -v`: **158 tests, OK**, incluyendo
regresiones SQL de unidades y utilidades conversacionales. Son pruebas con
fixtures/dobles; no sustituyen la comparación de los 20 casos reales ausentes.
Motor, evaluación y workflow permanecen sin cambios. El único archivo nuevo
visible en git status es este informe; no se hizo commit ni push.
