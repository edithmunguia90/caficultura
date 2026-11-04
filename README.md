# Asistente Inteligente para la Caficultura Nicaragüense

Sistema conversacional experto e híbrido que integra Reconocimiento de Intenciones (NLU), Gestión de Diálogo, Generación de Respuesta (NLG), Recuperación de Información (RAG), Redes Bayesianas, Visión Computacional (MobileNetV3) y Optimización Bioeconómica (Algoritmos Genéticos y Modelo Mitscherlich-Baule) para la caficultura en Nicaragua.

---

## 1. Arquitectura Modular del Sistema

Conforme a la guía de estructura de proyectos de Inteligencia Artificial:

```text
asistente-caficultura/
├── README.md                 # Documentación e instrucciones de instalación y uso
├── requirements.txt         # Dependencias exactas del proyecto
├── .env.example             # Plantilla de variables de entorno (sin claves reales)
├── .gitignore               # Exclusión de archivos binarios, base de datos y secretos
├── LICENSE                  # Licencia de uso (MIT)
├── data/
│   ├── raw/                 # Corpus agronómico y precios en bruto
│   ├── processed/           # Base de conocimiento y reglas estructuradas
│   └── intents/             # Dataset de intenciones y entidades (intents.json)
├── notebooks/
│   ├── 01_exploracion_datos.ipynb
│   ├── 02_entrenamiento_nlu.ipynb
│   └── 03_evaluacion.ipynb
├── src/
│   ├── __init__.py
│   ├── nlu/                 # Clasificador de intenciones y extractor de entidades
│   │   └── intent_classifier.py
│   ├── dialogue/            # Gestor de diálogo y transiciones de contexto
│   │   └── dialogue_manager.py
│   ├── nlg/                 # Generación de respuestas estructuradas y dinámicas
│   │   └── response_generator.py
│   ├── retrieval/           # Búsqueda semántica / léxica sobre documentos (RAG)
│   │   └── retriever.py
│   ├── integrations/        # Adaptadores para web (Streamlit), Telegram y APIs
│   │   ├── web_channel.py
│   │   ├── telegram_bot.py
│   │   ├── clima.py
│   │   └── mercado.py
│   └── utils/
│       └── preprocessing.py
├── prompts/
│   └── system_prompt.md     # Ingeniería de prompts y personalidades operativas
├── models/                  # Pesos MobileNetV3 y metadatos de modelos
├── evaluation/
│   ├── test_conversations.json # Diálogos de referencia y casos de prueba
│   └── metrics_report.md       # Reporte de métricas de precisión y desempeño
├── reports/
│   ├── figures/             # Gráficos de convergencia, DAG bayesiano y NLU
├── tests/
│   └── test_nlu.py          # Pruebas unitarias de NLU y diálogo
└── pruebas/
    └── test_sistema.py      # Suite integral del sistema (32 pruebas)
```

---

## 2. Requisitos del Sistema

- **Python:** 3.11+ (64-bit)
- **Sistema Operativo:** Windows, Linux o macOS
- **Ollama (Opcional para LLM local):** `ollama pull llama3.2:3b`
- **Google Gemini API (Opcional para Oráculo Cloud y Visión Cloud):** Configurable en `.env`

---

## 3. Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/edithmunguia90/caficultura.git
   cd caficultura
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   ```
   *(Editar `.env` si se dispone de `GEMINI_API_KEY` o puerto personalizado de Ollama)*.

---

## 4. Ejecución del Asistente

### Interfaz Web (Streamlit)
```bash
streamlit run app_streamlit.py
```

### Modo Consola / Terminal
```bash
python main.py
```

### API REST (FastAPI)
```bash
uvicorn api.main:app --reload
```

---

## 5. Pruebas Unitarias y Evaluación

Para ejecutar la totalidad de pruebas automatizadas:

```bash
pytest tests pruebas -v
```

Estado actual: **40/40 tests PASSED** (incluyendo NLU, gestor de diálogo, RAG, redes bayesianas, visión CNN MobileNetV3, algoritmos genéticos y generación de reportes PDF).
