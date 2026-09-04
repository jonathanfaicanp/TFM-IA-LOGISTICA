# Workflow de evaluación conversacional v1

`conversational_evaluation_v1.json` es una representación sanitizada y
reproducible del workflow n8n utilizado para generar las respuestas de la
evaluación conversacional v1. Reproduce la orquestación experimental y no debe
confundirse con el flujo operacional basado en `POST /evaluate-trip`.

El workflow espera que `llm_evaluation.json` esté disponible en
`/files/llm_evaluation.json` dentro del entorno de ejecución de n8n. Esta ruta
es genérica: debe asociarse a un volumen o directorio accesible para la
instancia. El flujo lee el documento, separa sus evaluaciones, envía cada
`analytical_result` al modelo GPT-5.6 Luna con el *prompt* congelado de la
evaluación v1 y conserva `case_id`, `stratum`, `model` y `response`. Finalmente,
genera `/files/luna_responses.json`.

Después de importar el workflow, cada usuario debe configurar en el nodo
`Message a model` su propia credencial de OpenAI administrada por n8n. El export
no contiene credenciales, claves de API, identificadores de credenciales ni
metadatos específicos de una instalación.

Los artefactos reales de entrada y salida permanecen bajo `data/` y fuera de
Git. Este workflow no incorpora datos empresariales: únicamente documenta la
orquestación reproducible aplicada sobre el artefacto anonimizado de evaluación.
