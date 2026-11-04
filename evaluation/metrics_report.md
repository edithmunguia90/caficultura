# Reporte de Métricas del Sistema Conversacional (NLU / Diálogo / CSAT)

**Proyecto:** Asistente Inteligente para la Caficultura en Nicaragua  
**Evaluación Oficial:** Suite de Pruebas de Referencia (`evaluation/test_conversations.json`)  
**Fecha de Ejecución:** 2026-11-03  

---

## 1. Resumen Ejecutivo de Cumplimiento de Umbrales

| Métrica | Meta / Umbral Exigido | Valor Obtenido | Estado |
|---|---|---|---|
| **Exactitud de Intención (Intent Accuracy)** | $\ge 90\%$ | **91.7\%** | ✅ Cumple |
| **F1-Score de Entidades (Entity F1)** | $\ge 0.85$ | **0.870** | ✅ Cumple |
| **Tasa de Éxito de Tarea (Task Success Rate)** | $\ge 90\%$ | **100.0\%** | ✅ Cumple |
| **Tasa de Caída a Fallback (Fallback Rate)** | $\le 15\%$ | **0.0\%** | ✅ Cumple |
| **Satisfacción del Usuario (CSAT Promedio)** | $\ge 4.0 / 5.0$ | **4.8 / 5.0** | ✅ Cumple |

---

## 2. Detalle de Rendimiento NLU

- **Casos de prueba analizados:** 8 diálogos completos (12 turnos conversacionales).
- **Intenciones evaluadas:** 11 aciertos de 12 turnos (91.7%).
  - Matriz de confusión: 0 falsos positivos en comandos estructurados críticos (`Confirmar_Accion`, `Optimizar_Plan_Fertilizacion_Riego`, `Consultar_Diagnostico_Sintoma`).
- **Entidades evaluadas:** 10 slots anotados.
  - Verdaderos Positivos (TP): 10
  - Falsos Positivos (FP): 3
  - Falsos Negativos (FN): 0
  - Precisión: 76.9% | Recall: 100.0% | **F1: 0.870**.

---

## 3. Eficiencia en Flujos de Diálogo y Manejo de Errores

1. **Flujo de Diagnóstico Progresivo:** Manejo exitoso de transiciones multietapa (`lluvia` $\rightarrow$ `temperatura` $\rightarrow$ `humedad` $\rightarrow$ diagnóstico determinista y riesgo bayesiano).
2. **Resiliencia ante Desconocimiento:** Cuando el usuario responde *"no sé"*, el sistema activa el autocompletado microclimático departamental sin interrumpir la sesión ni provocar excepciones.
3. **Optimización Bioeconómica:** Conciliación estricta entre la formulación de insumos del modelo Mitscherlich-Baule, los costos en Córdobas (C$) y el reporte final en PDF.
4. **Retrocompatibilidad Completa:** La fachada `modulos/chatbot.py` mantiene la API pública intacta mientras delega en `src/nlu/`, `src/dialogue/` y `src/nlg/`.
