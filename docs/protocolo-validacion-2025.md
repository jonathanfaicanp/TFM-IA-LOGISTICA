# Protocolo de reconstrucción 2024 → 2025

Fijado antes de ejecutar esta reconstrucción. No implica que 2026 nunca se
haya observado: la auditoría reconstruye un desarrollo que ya lo utilizó.

- Referencias exclusivamente de 2024; validación exclusivamente de 2025.
- Reutilizar A/B30/B50, escenarios D1/D2/AND/OR y perturbaciones existentes.
- Repetir sin cambios los percentiles, tasas, concentración por vehículo,
  cobertura y métricas semi-sintéticas de los scripts originales.
- Mostrar por separado exploración sin mínimo por vehículo y población con
  mínimo histórico de 100. No probar mínimos alternativos inventados.
- Distancias: sin filtro, >0,5, >1, >2 y >5 km, ya existentes en sensibilidad.
  Consumo conserva referencias fijas; para temporal mostrar referencias fijas
  y referencias filtradas, porque el motor excluye <=1 km también del histórico.
- Ninguna tasa marcada real es precisión ni evidencia de ineficiencia.
- La documentación describe compromisos cualitativos (contexto/fallback,
  dispersión/cobertura, respuesta a perturbaciones), pero no establece una
  función objetivo, prioridad de métricas o desempate para elegir reglas o
  distancia. No maximizar retrospectivamente balanced accuracy ni Youden.
- Presentar todas las métricas y detenerse en fase 5 si la decisión técnica
  sigue abierta. No ejecutar 2026 ni modificar el motor productivo.
- Una futura configuración congelada debe declarar baseline, elegibilidad,
  reglas, umbrales, distancia, política MAD cero y ámbito de filtrado histórico.
  Solo después se construiría 2024+2025 y se ejecutaría la evaluación final.

Esta reconstrucción aporta validación retrospectiva independiente de los
cálculos de 2026, pero no convierte 2026 en un test prospectivamente intacto.
