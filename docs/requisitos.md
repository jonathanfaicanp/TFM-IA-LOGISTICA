# Requisitos del proyecto

Los requisitos de este documento son propuestas del proyecto elaboradas a partir de la información disponible en esta conversación. No son requisitos oficiales de la VIU.

## Decisiones confirmadas

- La construcción inicial del *baseline* utilizará los registros de 2024 y 2025.
- La evaluación del comportamiento del detector utilizará los registros de 2026.
- La división entre construcción y evaluación será temporal y no aleatoria.

## Requisitos funcionales propuestos

| Identificador | Estado | Requisito |
| --- | --- | --- |
| RF-01 | Propuesto | El sistema deberá abordar la detección de ineficiencias logísticas y el apoyo a la toma de decisiones en un caso empresarial real. |
| RF-02 | Propuesto | El análisis deberá utilizar como fuente principal la tabla transformada `dbo.WF_OPERATIVA_CAMIONES` de la base de datos `AETL_SBOBI_v2_LOGISTICA`. |
| RF-03 | Propuesto | El sistema deberá poder utilizar los campos relevantes identificados: Código Viaje, Código Vehículo, Nombre Vehículo, Fecha de inicio, Fecha fin, Duración, Distancia, Velocidad máxima, Consumo, Conductor, Consumo CO2, Indicador de conducción y Matrícula. |
| RF-04 | Propuesto | El análisis deberá considerar principalmente distancia, duración, consumo, velocidad máxima e indicador de conducción. |
| RF-05 | Propuesto | El sistema deberá poder derivar distancia en kilómetros, duración en minutos u horas, consumo en litros y consumo en litros por 100 km a partir de las unidades conocidas. |
| RF-06 | Propuesto | El sistema no deberá interpretar automáticamente los registros con consumo igual a cero como consumo real cero. |
| RF-07 | Propuesto | El sistema deberá permitir detectar desviaciones respecto al comportamiento habitual de cada vehículo. |
| RF-08 | Propuesto | El sistema deberá permitir evaluar el comportamiento del detector mediante una división temporal: registros de 2024 y 2025 para la construcción del *baseline* y registros de 2026 para la evaluación. |
| RF-09 | Propuesto | El sistema deberá utilizar los registros de 2024 y 2025 para la construcción inicial del *baseline*, sin descartarlos automáticamente. |
| RF-10 | Propuesto | El sistema deberá generar alertas asociadas a las ineficiencias detectadas. |
| RF-11 | Propuesto | El sistema deberá proporcionar apoyo a la toma de decisiones mediante explicaciones en lenguaje natural. |

## Requisitos no funcionales propuestos

| Identificador | Estado | Requisito |
| --- | --- | --- |
| RNF-01 | Propuesto | El proyecto deberá mantener la trazabilidad de sus decisiones, requisitos, resultados y cambios durante la investigación. |
| RNF-02 | Propuesto | El proyecto no deberá incluir en su documentación credenciales, cadenas de conexión, datos empresariales reales ni archivos `.env`. |
| RNF-03 | Propuesto | La evaluación deberá tener en cuenta que actualmente no existe una variable de *ground truth* que identifique los viajes realmente ineficientes. |
| RNF-04 | Propuesto | La evaluación deberá tener en cuenta que actualmente no se dispone de validación experta sistemática de una muestra de registros. |
| RNF-05 | Propuesto | El método definitivo de detección deberá estudiar los valores extremos presentes en las variables analizadas antes de establecerse. |

## Decisiones pendientes

- Método definitivo de detección.
- Variables definitivas utilizadas por el detector.
- Umbrales de alerta.
- Método definitivo de construcción del *baseline*.
- Métricas de evaluación.
- Estrategia de evaluación sin *ground truth*.
- Formato definitivo de las alertas.
- Arquitectura definitiva de N8N.
- Modelo GPT concreto.
- Interfaz conversacional.

## Trazabilidad futura

La trazabilidad futura relacionará cada objetivo con el requisito correspondiente, el componente que lo cubra, la prueba realizada y la métrica utilizada.

| Objetivo | Requisito | Componente | Prueba | Métrica |
| --- | --- | --- | --- | --- |
| | | | | |
