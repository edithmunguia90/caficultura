# ============================================================
# modulos/chatbot.py
# Fachada (Facade Pattern) para el Asistente Inteligente
# Delega en src/nlu, src/dialogue y src/nlg preservando
# retrocompatibilidad absoluta con pruebas y UI.
# ============================================================
import os
import time
import uuid

from src.nlu.intent_classifier import (
    IntentClassifier,
    SUPERFICIE_FACTORES,
    NO_SE,
    INTENTS,
    _SINTOMAS_MAP,
    _DEPTO_ALIASES,
)
from src.dialogue.dialogue_manager import DialogueManager
from src.nlg.response_generator import ResponseGenerator
from modulos.clima_api import DEPTO_COORDS
from modulos.vision_cnn import ClasificadorVisionCNN
from modulos.kpis import registrar_turno
from modulos.db import crear_sesion, guardar_mensaje

DEPARTAMENTOS = list(DEPTO_COORDS.keys())


class ChatbotCaficultura:
    """
    Fachada conversacional (Facade) que coordina los módulos de NLU,
    gestión de diálogo (DM), generación de respuestas (NLG) y servicios
    de inteligencia artificial (Reglas, Bayes, AG, CNN, LLM).
    """

    def __init__(self, perfil: str = "pequeno_productor"):
        self.sesion_uuid = str(uuid.uuid4())[:8]
        self.sesion_db_id = crear_sesion(self.sesion_uuid, perfil=perfil)
        self.historial_chat = []

        # Estado y contexto de sesión
        self.ctx = {
            "perfil": perfil,
            "flujo_pendiente": None,
            "departamento_zona": "Matagalpa",
            "imagenes_analizadas": [],
            "superficie_manzanas": 1.0,
            "superficie_original": {"valor": 1.0, "unidad": "manzana"},
            "clima": {},
            "diagnosticos": [],
            "riesgo": {},
            "optimizacion": {},
        }

        # Subsistemas
        self.classifier = IntentClassifier()
        self.nlg = ResponseGenerator()
        self.dm = DialogueManager(self.ctx, self.sesion_uuid, self.sesion_db_id)
        self.cnn = ClasificadorVisionCNN()

        # Enlaces directos a motores para retrocompatibilidad
        self.motor = self.dm.motor
        self.bayes = self.dm.bayes
        self.ag = self.dm.ag
        self.clima = self.dm.clima
        self.llm = self.dm.llm

    @property
    def flujo_pendiente(self):
        return self.ctx.get("flujo_pendiente")

    @flujo_pendiente.setter
    def flujo_pendiente(self, val):
        self.ctx["flujo_pendiente"] = val

    def set_perfil(self, perfil: str):
        self.dm.set_perfil(perfil)

    def set_departamento(self, depto: str):
        if depto in DEPARTAMENTOS:
            self.dm.set_departamento(depto)

    def set_superficie(self, valor: float, unidad: str = "manzana"):
        factor = SUPERFICIE_FACTORES.get(unidad.lower(), 1.0)
        self.ctx["superficie_manzanas"] = round(valor * factor, 4)
        self.ctx["superficie_original"] = {"valor": valor, "unidad": unidad}

    def registrar_imagen(
        self,
        ruta: str,
        clase: str,
        confianza: float,
        nota_cruce: str = None,
        modo: str = "Gemini Vision AI",
        justificacion: str = "",
    ):
        """Registra la imagen analizada evitando duplicaciones."""
        self.ctx.setdefault("imagenes_analizadas", [])
        for img in self.ctx["imagenes_analizadas"]:
            if img.get("ruta") == ruta or (
                ruta and img.get("ruta") and os.path.basename(img["ruta"]) == os.path.basename(ruta)
            ):
                img["clase"] = clase
                img["confianza"] = float(confianza)
                img["nota_cruce"] = nota_cruce
                img["modo"] = modo
                img["justificacion"] = justificacion
                return

        self.ctx["imagenes_analizadas"].append({
            "ruta": ruta,
            "clase": clase,
            "confianza": float(confianza),
            "fecha": time.strftime("%Y-%m-%d %H:%M"),
            "nota_cruce": nota_cruce,
            "modo": modo,
            "justificacion": justificacion,
        })

    def detectar_intent(self, texto: str) -> str:
        """Clasifica la intención mediante el componente NLU."""
        return self.classifier.predecir_intencion(texto)

    def extraer_entidades(self, texto: str) -> dict:
        """Extrae entidades mediante el componente NLU."""
        flujo = self.ctx.get("flujo_pendiente")
        return self.classifier.extraer_entidades(texto, flujo_pendiente=flujo)

    def _autocompletar_clima(self) -> dict:
        """Delega en el DialogueManager el autocompletado microclimático."""
        return self.dm.autocompletar_clima()

    def responder(self, texto_usuario: str) -> tuple:
        """Procesa el turno conversacional completo."""
        t0 = time.time()
        self.historial_chat.append({"role": "user", "content": texto_usuario})

        flujo = self.ctx.get("flujo_pendiente")
        if flujo in ("lluvia", "temp", "hr"):
            intent = "Consultar_Diagnostico_Sintoma"
        else:
            intent = self.detectar_intent(texto_usuario)

        ents = self.extraer_entidades(texto_usuario)
        if ents.pop("_auto_clima", False):
            self._autocompletar_clima()

        # Si el usuario describió síntomas, corregir intención
        if "sintoma_observado" in ents:
            intent = "Consultar_Diagnostico_Sintoma"

        self.ctx.update(ents)
        guardar_mensaje(self.sesion_db_id, "usuario", texto_usuario, intent)

        respuesta, intent_final, error = self._despachar(intent, texto_usuario)
        guardar_mensaje(self.sesion_db_id, "asistente", respuesta, intent_final)
        self.historial_chat.append({"role": "assistant", "content": respuesta})

        registrar_turno(
            sesion_uuid=self.sesion_uuid,
            intent=intent_final,
            entidades=ents,
            respuesta=respuesta,
            tiempo_seg=time.time() - t0,
            fallback=(intent_final == "Consultar_Oraculo_LLM_Fallback"),
            error=error,
        )
        return respuesta, intent_final

    def _despachar(self, intent: str, texto_usuario: str) -> tuple:
        """Delega el enrutamiento y ejecución al DialogueManager."""
        return self.dm.despachar(intent, texto_usuario, self.historial_chat)

    def _flujo_diagnostico(self) -> tuple:
        return self.dm._flujo_diagnostico()

    def _flujo_optimizacion(self) -> tuple:
        return self.dm._flujo_optimizacion()

    def _flujo_reporte(self) -> tuple:
        return self.dm._flujo_reporte()

    def _texto_ayuda(self) -> str:
        return self.nlg.formatear_ayuda()

    def _contexto_finca_texto(self) -> str:
        return self.dm._contexto_finca_texto()
