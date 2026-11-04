# ASIGNATURA DE INTELIGENCIA ARTIFICIAL

## Guía de Estructura de Proyectos
**Documentación y Organización del Código Fuente**
*Enfoque: Chatbot / Agente Conversacional*
*Guía de referencia para la elaboración de proyectos finales*
*Fecha: agosto de 2026*

---

## Índice
*(Clic derecho sobre esta área → "Actualizar campo" → "Actualizar toda la tabla" para generar el índice automáticamente en Word)*

1. Introducción
2. Estructura Documental del Informe
    2.1 Secciones obligatorias
    2.2 Formato del documento
3. Estructura de Programación (Repositorio de Código)
    3.1 Árbol de directorios recomendado
    3.2 Descripción de carpetas y archivos clave
    3.3 Buenas prácticas de programación exigidas
4. Relación entre el Informe y el Código
5. Criterios de Evaluación Sugeridos
6. Recomendaciones Finales

---

## 1. Introducción
Esta guía define la estructura mínima que debe seguir todo proyecto final de chatbot / agente conversacional de la asignatura de Inteligencia Artificial, tanto en su componente documental (el informe escrito) como en su componente de programación (el código fuente y su organización en el repositorio). El objetivo es estandarizar la presentación de los proyectos, facilitar su evaluación y fomentar buenas prácticas propias del desarrollo de sistemas conversacionales.

Un proyecto de chatbot no se evalúa únicamente por si "responde bien": se evalúa el diseño conversacional (qué problema resuelve y para quién), la solidez técnica del motor de comprensión y generación de lenguaje, la calidad y organización del código, y el rigor con que se probaron y midieron los resultados. Por ello, esta guía combina dos partes complementarias: la estructura del documento (informe) y la estructura del proyecto de código (repositorio).

Esta plantilla aplica independientemente del enfoque técnico elegido: chatbot basado en reglas/árbol de decisión, chatbot de intenciones con NLU (p. ej. Rasa, Dialogflow), chatbot basado en recuperación de información (retrieval), o chatbot generativo basado en un modelo de lenguaje (LLM), incluyendo arquitecturas RAG (Retrieval-Augmented Generation).

## 2. Estructura Documental del Informe
El informe escrito debe entregarse en formato PDF (o Word) y seguir el siguiente orden de secciones. Cada sección debe estar claramente titulada y numerada.

### 2.1 Secciones obligatorias

| N° | Sección | Contenido esperado |
| :--- | :--- | :--- |
| 1 | Portada | Nombre de la institución, asignatura, título del proyecto, integrantes, docente, fecha. |
| 2 | Índice / Tabla de contenido | Listado de secciones con numeración de página. |
| 3 | Resumen ejecutivo | Síntesis del propósito del chatbot, enfoque técnico y principales resultados (150–250 palabras). |
| 4 | Introducción | Contexto del problema y motivación del proyecto. |
| 5 | Planteamiento del problema | Necesidad conversacional a resolver: ¿qué tarea o consulta atenderá el chatbot y para quién? |
| 6 | Objetivos | Objetivo general y objetivos específicos, medibles y alcanzables. |
| 7 | Justificación | Relevancia académica, social o técnica del proyecto. |
| 8 | Marco teórico y estado del arte | Conceptos de NLP/NLU/NLG, tipos de chatbot (reglas, retrieval, generativo, RAG) y soluciones similares existentes. |
| 9 | Diseño conversacional | Definición de intenciones (intents), entidades, flujos de diálogo, personas de usuario, casos de uso y ejemplos de conversación esperada. |
| 10 | Metodología | Enfoque técnico elegido y justificación; herramientas y frameworks utilizados (Rasa, Dialogflow, LangChain, OpenAI API, Hugging Face, etc.). |
| 11 | Datos / corpus de entrenamiento | Fuente del corpus, FAQs, documentos base (para RAG), dataset de intents y entidades, tamaño y licencia de uso. |
| 12 | Preprocesamiento de texto | Limpieza, normalización, tokenización, embeddings o vectorización utilizada. |
| 13 | Arquitectura del sistema | Diagrama y descripción de los módulos: NLU, gestor de diálogo, NLG/generación de respuesta, integración con el canal. |
| 14 | Implementación | Descripción técnica del motor conversacional, modelo o API usada, ingeniería de prompts (si aplica), integración con el canal (web, Telegram, WhatsApp, etc.). |
| 15 | Pruebas y evaluación | Metodología de prueba: conjunto de diálogos de prueba, pruebas con usuarios reales, métricas usadas. |
| 16 | Resultados | Métricas obtenidas (exactitud de intención, tasa de éxito de tarea, satisfacción, BLEU/ROUGE si es generativo) e interpretación. |
| 17 | Discusión y limitaciones | Casos donde el chatbot falla, limitaciones del enfoque, riesgos (alucinaciones, sesgos, seguridad de datos). |
| 18 | Conclusiones | Respuestas a los objetivos planteados. |
| 19 | Recomendaciones y trabajo futuro | Mejoras posibles y líneas de continuidad. |
| 20 | Referencias bibliográficas | En formato APA (7.ª edición) u otro indicado por el docente. |
| 21 | Anexos | Capturas de conversaciones reales, diagramas de flujo de diálogo, enlace al repositorio y a un video/demo. |

### 2.2 Formato del documento
*   **Extensión sugerida:** entre 15 y 30 páginas (sin contar anexos).
*   **Fuente:** Calibri u otra de fácil lectura, tamaño 11–12 pts, interlineado 1.15–1.5.
*   Todas las figuras, diagramas de flujo y tablas deben numerarse y llevar título y fuente.
*   Debe incluirse el enlace al repositorio de código (GitHub/GitLab) y, de ser posible, un enlace o video de demostración funcionando.
*   Las citas y referencias deben seguir un formato consistente (recomendado: APA 7.ª edición).
*   Se recomienda incluir capturas de pantalla de al menos 3 a 5 conversaciones representativas (casos exitosos y casos límite).

## 3. Estructura de Programación (Repositorio de Código)
El código debe organizarse en un repositorio con una estructura modular que separe claramente los componentes propios de un sistema conversacional: comprensión del lenguaje (NLU), gestión del diálogo, generación de respuestas (NLG), recuperación de información (si aplica) e integración con el canal de mensajería.

### 3.1 Árbol de directorios recomendado

```text
chatbot-ia/
├── README.md
├── requirements.txt
├── .env.example                 # Variables de entorno de ejemplo (sin claves reales)
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/                     # Corpus original, documentos fuente, FAQs
│   ├── processed/               # Datos limpios y formateados
│   └── intents/                 # Dataset de intenciones y entidades (NLU)
├── notebooks/
│   ├── 01_exploracion_datos.ipynb
│   ├── 02_entrenamiento_nlu.ipynb
│   └── 03_evaluacion.ipynb
├── src/
│   ├── __init__.py
│   ├── nlu/                     # Reconocimiento de intenciones y entidades
│   │   └── intent_classifier.py
│   ├── dialogue/                # Gestor de diálogo / manejo de estados y contexto
│   │   └── dialogue_manager.py
│   ├── nlg/                     # Generación de respuestas
│   │   └── response_generator.py
│   ├── retrieval/               # (si aplica RAG) recuperación de documentos
│   │   └── retriever.py
│   ├── integrations/            # Conexión al canal (Telegram, WhatsApp, web, Slack)
│   │   └── telegram_bot.py
│   └── utils/
│       └── preprocessing.py
├── prompts/                     # Plantillas de prompts (si se usa un LLM)
│   └── system_prompt.md
├── models/                      # Modelos/fine-tuning propios, índice vectorial (vectorstore)
├── evaluation/
│   ├── test_conversations.json  # Casos de prueba / diálogos de referencia
│   └── metrics_report.md
├── reports/
│   ├── figures/                 # Diagramas de flujo, capturas
│   └── informe_final.pdf
└── tests/
    └── test_nlu.py              # Pruebas unitarias básicas
```

### 3.2 Descripción de carpetas y archivos clave

| Elemento | Propósito |
| :--- | :--- |
| `README.md` | Descripción del chatbot, instrucciones de instalación, configuración de variables de entorno y ejecución. |
| `requirements.txt` | Lista de dependencias y versiones exactas para reproducir el entorno. |
| `.env.example` | Plantilla de variables de entorno (API keys, tokens del canal) sin valores reales. |
| `data/intents/` | Dataset de entrenamiento del NLU: ejemplos de frases por intención y entidades a extraer. |
| `src/nlu/` | Módulo que clasifica la intención del usuario y extrae entidades relevantes del mensaje. |
| `src/dialogue/` | Gestor de diálogo: controla el estado de la conversación, el contexto y las transiciones. |
| `src/nlg/` | Genera la respuesta final que recibe el usuario (plantillas, o llamada a un modelo generativo). |
| `src/retrieval/` | Si el chatbot usa RAG: búsqueda semántica sobre una base de documentos/FAQs. |
| `src/integrations/` | Código de conexión con el canal donde opera el bot (Telegram, WhatsApp, web widget, Slack, etc.). |
| `prompts/` | Prompts de sistema y plantillas versionadas, si el chatbot usa un modelo de lenguaje (LLM). |
| `models/` | Modelos entrenados/ajustados y almacenes vectoriales (embeddings) usados por el bot. |
| `evaluation/` | Casos de prueba conversacionales y reporte de métricas de desempeño. |
| `tests/` | Pruebas que validan que el NLU, el gestor de diálogo y la generación de respuesta funcionan correctamente. |

### 3.3 Buenas prácticas de programación exigidas
*   **Control de versiones:** usar Git desde el inicio del proyecto, con commits pequeños y mensajes descriptivos (ej. "agrega clasificador de intención de saludo").
*   **Arquitectura modular:** separar claramente NLU, gestión de diálogo y generación de respuesta; evitar mezclar toda la lógica en un solo archivo.
*   **Manejo seguro de credenciales:** las claves de API (OpenAI, Telegram, etc.) nunca se suben al repositorio; deben cargarse desde variables de entorno (`.env`) y excluirse con `.gitignore`.
*   **Manejo de fallback:** el chatbot debe responder de forma controlada cuando no entiende un mensaje o la intención tiene baja confianza, en lugar de fallar o inventar información.
*   **Registro (logging):** guardar un historial de conversaciones (anonimizado si es necesario) útil para depuración y para el análisis de resultados.
*   **Versionado de prompts y datos:** si se usa un LLM, documentar y versionar los prompts de sistema; documentar cambios al dataset de intents.
*   **Pruebas con casos de diálogo:** mantener un conjunto de conversaciones de prueba (`evaluation/test_conversations.json`) que se ejecute antes de cada entrega.
*   **README completo:** debe permitir a cualquier persona clonar el repositorio, configurar las variables de entorno y ejecutar el bot sin ayuda adicional.

## 4. Relación entre el Informe y el Código
El informe documental y el repositorio de código no son piezas independientes: cada sección analítica del informe (diseño conversacional, NLU, arquitectura, evaluación) debe estar respaldada por el código correspondiente en el repositorio. Se recomienda incluir, en cada sección relevante del informe, una referencia al módulo o notebook donde se implementó ese paso (por ejemplo: "ver `src/nlu/intent_classifier.py`" o "ver `evaluation/metrics_report.md`").

## 5. Criterios de Evaluación Sugeridos
A modo de referencia, se sugiere la siguiente distribución de ponderación entre los componentes del proyecto. El docente puede ajustar estos porcentajes según los objetivos particulares de la asignatura.

| Componente | Ponderación | Aspectos evaluados |
| :--- | :--- | :--- |
| **Documentación / informe** | 25% | Claridad, completitud de secciones, redacción, referencias. |
| **Diseño conversacional y NLU** | 20% | Calidad de intents/entidades, cobertura de casos de uso, coherencia de los flujos de diálogo. |
| **Calidad del código / arquitectura** | 25% | Modularidad NLU–diálogo–NLG, manejo seguro de credenciales, buenas prácticas, reproducibilidad. |
| **Evaluación y pruebas** | 15% | Rigor de las pruebas, métricas adecuadas, manejo de casos límite y de fallback. |
| **Presentación / demo en vivo** | 15% | Funcionamiento real del chatbot, claridad expositiva, respuesta a preguntas. |

## 6. Recomendaciones Finales
*   Definir primero el alcance conversacional (qué preguntas SÍ y qué preguntas NO debe responder el bot) antes de escribir código.
*   Iniciar el repositorio de código desde la primera semana del proyecto, no al final.
*   Probar el chatbot con usuarios reales (compañeros de clase) y registrar los casos donde falla.
*   Nunca exponer claves de API en el código fuente ni en capturas de pantalla del informe.
*   Preparar una demostración en vivo funcional como respaldo del informe escrito.
*   Citar correctamente cualquier framework, modelo preentrenado o dataset de intents que no sea de autoría propia.