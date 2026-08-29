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
