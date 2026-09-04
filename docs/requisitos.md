# Requisitos del proyecto

Estos requisitos pertenecen al proyecto del TFM y se basan en el alcance y la
evidencia disponibles. No son requisitos oficiales de la universidad.

Estados: `IMPLEMENTADO`, `PARCIAL`, `FUERA DE ALCANCE V1` y
`PENDIENTE FUTURO`.

## Requisitos funcionales

| ID | Estado | Requisito y alcance actual |
|---|---|---|
| RF-01 | IMPLEMENTADO | La v1 implementa un prototipo para identificar desviaciones logísticas y apoyar su revisión. La ausencia de *ground truth* real limita la evaluación, no el cumplimiento de este requisito funcional. |
| RF-02 | IMPLEMENTADO | Usar `dbo.WF_OPERATIVA_CAMIONES` de SQL Server como fuente operacional, manteniendo CSV para desarrollo local. |
| RF-03 | IMPLEMENTADO | Obtener para la v1 identidad del viaje y vehículo, fecha de inicio, distancia, consumo y duración. |
| RF-04 | IMPLEMENTADO | Analizar distancia, consumo y duración. Velocidad máxima e indicador de conducción no participan en los detectores v1. No existe una variable de carga disponible y el análisis carga-consumo queda fuera de la v1. |
| RF-05 | IMPLEMENTADO | Normalizar distancia a kilómetros, duración a minutos, consumo a litros, L/100 km y minutos/km. |
| RF-06 | IMPLEMENTADO | Tratar consumo cero o ausente como no evaluable, sin interpretarlo como consumo real cero. |
| RF-07 | IMPLEMENTADO | Detectar desviaciones respecto al histórico del vehículo y su contexto de distancia. |
| RF-08 | IMPLEMENTADO | Separar temporalmente 2024–2025 para baselines y 2026 para evaluación. |
| RF-09 | IMPLEMENTADO | Construir baselines con observaciones históricas válidas de 2024–2025. |
| RF-10 | FUERA DE ALCANCE V1 | La v1 genera estados estructurados `REVIEW` para desviaciones que requieren revisión, pero no incluye un subsistema de distribución de alertas. La notificación automática puede abordarse como trabajo futuro. |
| RF-11 | PARCIAL | Explicar resultados sin alterar la decisión analítica. El workflow n8n se probó externamente y el de evaluación está sanitizado; la generación LLM no es un componente ejecutable del repositorio. |

## Requisitos no funcionales

| ID | Estado | Requisito y alcance actual |
|---|---|---|
| RNF-01 | IMPLEMENTADO | Mantener trazabilidad mediante documentación, scripts y tests. |
| RNF-02 | IMPLEMENTADO | Excluir credenciales, secretos y datos empresariales de Git. |
| RNF-03 | IMPLEMENTADO | Delimitar la evaluación por ausencia de *ground truth* real de ineficiencia. |
| RNF-04 | IMPLEMENTADO | La evaluación deberá tener en cuenta la ausencia de validación experta sistemática. La evaluación conversacional v1 incorpora una valoración humana con un único evaluador, y la ausencia de evaluación interjueces se mantiene explícitamente como limitación. |
| RNF-05 | IMPLEMENTADO | Estudiar distribuciones, extremos, sensibilidad y reglas antes de fijar los detectores v1. |

## Contrato analítico v1

- Mediana y MAD del contexto vehículo-rango con al menos 30 observaciones, y
  *fallback* al vehículo.
- Mínimo de 100 observaciones históricas válidas por vehículo.
- Regla en ambas señales:
  `relative_deviation > 0.50 AND robust_z > 2`.
- Estados: `REVIEW`, `NO_RELEVANT_DEVIATION` y `NOT_EVALUABLE`.
- `REVIEW` identifica una desviación a revisar, no una ineficiencia confirmada.
- La señal temporal representa minutos por kilómetro respecto al histórico
  comparable, no tiempo de parada.
- Cobertura consolidada: `COMPLETE`, `PARTIAL` o `NONE`.

## Trazabilidad

| Requisito | Componente | Evidencia |
|---|---|---|
| RF-02, RF-03 | `src/sql_repository.py` | Tests del repositorio y validación externa SQL Server → FastAPI. |
| RF-04–RF-06 | `src/data_processing.py` | Tests de normalización, valores no positivos y consumo ausente. |
| RF-07–RF-09 | `src/baseline.py`, `src/detector.py`, `src/temporal_detector.py` | Tests de baselines, umbrales, elegibilidad y separación temporal. |
| RF-07 | `src/consolidation.py` | Tests de estados y cobertura. |
| RF-11 | `n8n/conversational_evaluation_v1.json`, `evaluation/` | Evaluación conversacional documentada en `docs/metodologia.md`. |
| RNF-01 | `scripts/`, `tests/`, `docs/` | Experimentos reproducibles, suite automatizada y decisiones. |
| RNF-02 | `.gitignore`, `n8n/README.md` | Datos y exportes originales excluidos; workflow sanitizado. |
| RNF-03–RNF-05 | `scripts/evaluate_*`, `docs/metodologia.md` | Benchmarks, límites de validez y rúbrica humana. |

## Pendientes reales

- Distribución o notificación automática de estados `REVIEW`, como posible
  trabajo futuro fuera del alcance v1.
- RF-11: productivización de la orquestación y generación conversacional, si se
  incorpora a un alcance posterior.
- Validación interjueces y con *ground truth*, si en el futuro se dispone de
  evaluadores y etiquetas adecuadas.
- Seguridad, despliegue y operación productiva, fuera del prototipo v1.
