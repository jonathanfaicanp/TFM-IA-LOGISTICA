# Arquitectura

Este documento describirá la arquitectura del proyecto cuando existan decisiones y evidencias que la respalden.

## Decisiones confirmadas

La primera implementación reutilizable mantiene un flujo local y desacoplado de integraciones externas:

`datos -> preparación -> baseline B30 -> detector v1 -> salida estructurada`

- **Preparación:** normaliza tipos y fechas, convierte distancia y consumo a kilómetros y litros, calcula L/100 km y asigna el rango de distancia.
- **Baseline B30:** se construye exclusivamente con registros históricos válidos de 2024 y 2025. Exige al menos 100 observaciones por vehículo y utiliza mediana y MAD del contexto vehículo-rango cuando existen al menos 30 observaciones; en caso contrario, utiliza el *fallback* del vehículo.
- **Detector v1:** evalúa registros de 2026 con consumo y distancia positivos. Analiza únicamente desviaciones de consumo mediante la regla desviación relativa > 50 % AND `robust_z` > 2.
- **Salida estructurada:** devuelve datos normalizados, referencia histórica, medidas de desviación, tipo de *baseline*, estado y motivo. La estructura puede serializarse posteriormente a JSON, pero no constituye todavía una API.
- **Semántica:** `REVIEW` significa «desviación a revisar», no «ineficiencia confirmada».
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
