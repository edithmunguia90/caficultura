# Asistente Técnico para la Caficultura en Nicaragua

Sistema conversacional híbrido diseñado para asistir a pequeños productores, administradores de fincas y técnicos extensionistas en el manejo fitosanitario y bioeconómico del cultivo de café en Nicaragua.

El asistente integra diagnóstico fitopatológico (visual y sintomático), evaluación de riesgo microclimático, cálculo optimizado de fertilización y riego, consulta de precios de mercado y generación de reportes técnicos.

---

## Descripción

El proyecto combina métodos de inteligencia artificial deterministas, probabilísticos y generativos para resolver consultas operativas en finca:

- **Diagnóstico fitopatológico:** Identifica enfermedades como Roya (*Hemileia vastatrix*), Antracnosis (*Colletotrichum spp.*), Ojo de gallo (*Mycena citricolor*) y deficiencias nutricionales mediante dos vías: clasificación de imágenes foliares (MobileNetV3 / Gemini Vision) y un cuestionario evaluado por un motor de reglas determinista.
- **Evaluación de riesgo probabilístico:** Una red bayesiana calcula la probabilidad de dispersión de patógenos a partir de variables microclimáticas (temperatura, humedad relativa y precipitación previa).
- **Optimización bioeconómica:** Aplica un algoritmo genético sobre la función de producción de Mitscherlich-Baule para estimar las dosis más rentables de fertilizantes (N-P-K), riego y fungicidas según la superficie del lote.
- **Oráculo agronómico con modelos de lenguaje:** Si una consulta excede las reglas predefinidas o se solicita asesoría sobre manejo técnico, el sistema consulta a Google Gemini (`gemini-3.5-flash-lite`) o al modelo local en Ollama (`llama3.2:3b`), inyectando el contexto de la finca y de las muestras analizadas.
- **Datos meteorológicos y de mercado:** Integra el pronóstico agroclimático departamental de Open-Meteo y cotizaciones internacionales de café (Contrato C / tipo de cambio oficial).

---

## Estructura del Proyecto

```text
asistente-caficultura/
├── app_streamlit.py          # Interfaz web principal (Streamlit)
├── main.py                   # Interfaz de línea de comandos (consola)
├── config.py                 # Rutas base y configuración de la aplicación
├── monitor_precios.py        # Tarea programada para sincronización de cotizaciones
├── analisis_sensibilidad.py  # Simulación de escenarios de mercado y costos
├── requirements.txt          # Dependencias exactas del entorno Python
├── .env.example              # Plantilla de variables de entorno
├── api/
│   └── servidor.py           # Endpoints HTTP REST (FastAPI)
├── data/
│   ├── raw/                  # Corpus agronómico y notas técnicas de origen
│   ├── processed/            # Datos transformados para inferencia
│   └── intents/              # Dataset de intenciones y entidades (intents.json)
├── datos/
│   ├── contexto_agronomico.txt # Referencia agronómica del café en Nicaragua
│   ├── precios_cafe.json     # Registro local de precios y tipo de cambio
│   └── reglas_produccion.json # Base de conocimiento determinista (reglas SI-ENTONCES)
├── evaluation/
│   ├── metrics_report.md     # Informe de métricas, tiempos de respuesta y CSAT
│   └── test_conversations.json # Casos de diálogo de prueba
├── modulos/
│   ├── algoritmo_genetico.py # Optimización bioeconómica de insumos de manejo
│   ├── chatbot.py            # Fachada conversacional principal del asistente
│   ├── clima_api.py          # Conexión meteorológica por coordenadas de departamentos
│   ├── db.py                 # Persistencia en SQLite (sesiones, mensajes, CSAT)
│   ├── entrenar_cnn.py       # Pipeline de entrenamiento de la red convolucional
│   ├── kpis.py               # Registro y cálculo de indicadores del sistema
│   ├── llm_fallback.py       # Oráculo agronómico con Google Gemini y Ollama local
│   ├── mitscherlich_baule.py # Modelo agronómico de rendimientos decrecientes
│   ├── motor_reglas.py       # Motor determinista con encadenamiento hacia adelante
│   ├── precios.py            # Consulta y persistencia de cotizaciones de café
│   ├── red_bayesiana.py      # Red Bayesiana para inferencia probabilística de riesgo
│   ├── reporte_pdf.py        # Generación de reportes agronómicos en formato PDF
│   ├── sugerencias.py        # Sugerencias dinámicas según el estado de la consulta
│   ├── ui_theme.py           # Tema visual, tokens de diseño y estilos CSS
│   └── vision_cnn.py         # Inferencia visual foliar (clasificador local y API)
├── notebooks/
│   ├── 01_exploracion_datos.ipynb # Análisis exploratorio de variables agronómicas
│   ├── 02_entrenamiento_nlu.ipynb # Validación del modelo de intenciones
│   └── 03_evaluacion.ipynb        # Comparativa y evaluación de respuestas
├── prompts/
│   └── system_prompt.md      # Directrices de rol y tono para los modelos LLM
├── pruebas/
│   └── test_sistema.py       # Pruebas funcionales e integración de módulos
├── reports/
│   └── figures/              # Diagramas y curvas generadas
├── src/
│   ├── dialogue/
│   │   └── dialogue_manager.py # Control de estados y transiciones de diálogo
│   ├── integrations/
│   │   ├── telegram_bot.py   # Conector opcional para canal de Telegram
│   │   └── web_channel.py    # Adaptador para clientes web externos
│   ├── nlg/
│   │   └── response_generator.py # Formateo de respuestas por perfil operativo
│   ├── nlu/
│   │   └── intent_classifier.py  # Clasificación de intenciones y entidades
│   ├── retrieval/
│   │   └── retriever.py      # Búsqueda léxica y semántica en documentos (RAG)
│   └── utils/
│       └── preprocessing.py  # Normalización y limpieza léxica
└── tests/
    └── test_nlu.py           # Pruebas unitarias del pipeline NLU y diálogo
```

---

## Tecnologías y Librerías Utilizadas

El desarrollo se construyó sobre Python 3.11+, organizado en tres grupos de librerías:

### Inteligencia Artificial y Computación Científica
- **pgmpy (1.1.2):** Definición del grafo acíclico dirigido (DAG) y cálculo de distribuciones de probabilidad condicional (CPD) en la Red Bayesiana.
- **scikit-learn (1.9.1) y scipy (1.18.1):** Métricas de desempeño, optimización numérica y cálculo de modelos agronómicos.
- **OpenCV (5.0.0) y Pillow (13.0.0):** Lectura, preprocesamiento y transformaciones de imágenes foliares.
- **google-genai (2.34.0):** Conexión con la API de Google Gemini para análisis de visión y consultas agronómicas (`gemini-3.5-flash-lite`).
- **ollama (0.6.3):** Cliente para ejecución de modelos de lenguaje locales sin conexión (`llama3.2:3b`).
- **pandas (3.1.0) y numpy (2.5.4):** Manipulación de estructuras de datos tabulares, cálculos vectoriales y matrices de insumos.

### Interfaz, Integraciones y Salidas
- **Streamlit (1.66.1):** Interfaz web del usuario con soporte para modo claro/oscuro, navegación lateral compacta, chat y escáner foliar.
- **FastAPI (0.162.0) y Uvicorn (0.54.0):** Publicación de endpoints REST para consumo externo de los módulos.
- **ReportLab (5.1.0):** Generación técnica y maquetación de informes fitosanitarios descargables en PDF.
- **Requests (2.34.2) y yfinance (1.8.0):** Consumo de datos meteorológicos de Open-Meteo y cotización internacional del café.
- **Schedule (1.2.2):** Tareas periódicas en segundo plano para refresco de precios de mercado.
- **SQLite3:** Persistencia local de sesiones, historial de mensajes, diagnósticos generados y métricas CSAT.

### Pruebas y Validación
- **Pytest (9.2.0):** Ejecución automatizada de 43 pruebas unitarias y de integración que validan NLU, diálogo, reglas, redes bayesianas y generación documental.

---

## Instalación y Configuración

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

4. **Variables de entorno:**
   Copiar la plantilla `.env.example` a un archivo `.env`:
   ```bash
   cp .env.example .env
   ```
   Configurar los valores según los recursos disponibles:
   ```env
   GEMINI_API_KEY=tu_api_key_aqui
   OLLAMA_HOST=http://127.0.0.1:11434
   ```

---

## Ejecución

### Interfaz Web (Streamlit)
```bash
streamlit run app_streamlit.py
```

### Modo Consola
```bash
python main.py
```

### Servidor de API (FastAPI)
```bash
uvicorn api.servidor:app --reload --port 8000
```

---

## Ejecución de Pruebas

Para verificar la totalidad de los componentes:
```bash
pytest tests pruebas -v
```
Pasan las 43 pruebas del sistema (100% exitosas).
