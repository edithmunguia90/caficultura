"""
tests/test_nlu.py
Pruebas unitarias de reconocimiento de intenciones, extracción de entidades y RAG.
Conforme a la sección 3.1 y 3.2 de la Guía de Estructura de Proyectos de IA.
"""
import pytest
from src.nlu.intent_classifier import IntentClassifier
from src.retrieval.retriever import RecuperadorConocimiento
from src.dialogue.dialogue_manager import DialogueManager


@pytest.fixture
def nlu():
    return IntentClassifier()


@pytest.fixture
def retriever():
    return RecuperadorConocimiento()


@pytest.fixture
def dialogue_manager():
    ctx = {
        "perfil": "pequeno_productor",
        "departamento_zona": "Matagalpa",
        "superficie_manzanas": 1.0,
    }
    return DialogueManager(ctx=ctx, sesion_uuid="test-uuid", sesion_db_id=1)


def test_intencion_saludo(nlu):
    intent, confianza, entidades = nlu.clasificar("Hola, buenos dias")
    assert intent == "Saludo"
    assert confianza >= 0.85


def test_intencion_clima_y_extraccion_departamento(nlu):
    intent, confianza, entidades = nlu.clasificar("Como esta el clima en Jinotega?")
    assert intent == "Sincronizar_Clima_Entorno"
    assert entidades.get("departamento_zona") == "Jinotega"


def test_intencion_diagnostico_y_sintoma(nlu):
    intent, confianza, entidades = nlu.clasificar("Tengo manchas naranjas en las hojas de mi cafe")
    assert intent == "Consultar_Diagnostico_Sintoma"
    assert entidades.get("sintoma_observado") == "manchas_naranjas"


def test_intencion_fertilizacion_y_superficie(nlu):
    intent, confianza, entidades = nlu.clasificar("Necesito un plan de fertilizacion para 2 manzanas")
    assert intent == "Optimizar_Plan_Fertilizacion_Riego"
    assert entidades.get("superficie_manzanas") == 2.0


def test_intencion_precios(nlu):
    intent, confianza, entidades = nlu.clasificar("Cual es el precio actual del cafe hoy?")
    assert intent == "Consultar_Precios_Mercado"
    assert confianza >= 0.8


def test_manejo_de_fallback_y_desconocido(nlu):
    intent, confianza, entidades = nlu.clasificar("kjashdkjasd texto sin sentido 12345")
    assert intent == "Consultar_Oraculo_LLM_Fallback"
    assert confianza < 0.8


def test_recuperador_rag_documentos(retriever):
    resultados = retriever.recuperar("roya cafe fungicida", top_k=2)
    assert isinstance(resultados, list)
    assert len(resultados) > 0
    assert "texto" in resultados[0]
    assert "score" in resultados[0]


def test_intencion_tratamiento_recomendacion(nlu):
    intent, confianza, entidades = nlu.clasificar("Que hago con este tipo de enfermedad?")
    assert intent == "Consultar_Tratamiento_Recomendacion"
    assert confianza >= 0.85

    intent2, _, _ = nlu.clasificar("Como tratar la roya y que fungicida aplicar?")
    assert intent2 == "Consultar_Tratamiento_Recomendacion"


def test_dialogue_manager_flujo_completo(dialogue_manager):
    respuesta, intent = dialogue_manager.procesar_turno("Hola, buenos dias")
    assert isinstance(respuesta, str)
    assert len(respuesta) > 10
    assert intent == "Saludo"


def test_dialogue_manager_tratamiento_con_imagen(dialogue_manager):
    dialogue_manager.ctx["imagenes_analizadas"] = [{
        "ruta": "test.jpg",
        "clase": "Roya",
        "confianza": 0.95,
        "justificacion": "Manchas anaranjadas en envés",
    }]
    respuesta, intent = dialogue_manager.procesar_turno("Que hago con este tipo de enfermedad?")
    assert intent == "Consultar_Tratamiento_Recomendacion"
    assert "roya" in respuesta.lower() or "fungicida" in respuesta.lower()
