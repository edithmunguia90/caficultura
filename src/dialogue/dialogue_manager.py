"""
src/dialogue/dialogue_manager.py
Gestor de diálogo, contexto de sesión y transiciones de estado conversacional.
"""
import os
import time
from modulos.motor_reglas import MotorReglas
from modulos.red_bayesiana import RedBayesianaCafe
from modulos.algoritmo_genetico import OptimizacionGenetica
from modulos.clima_api import ModuloClima
from modulos.precios import actualizar_precios
from modulos.reporte_pdf import generar_reporte, exportar_a_descargas
from modulos.llm_fallback import OraculoAgronomoLLM
from modulos.db import guardar_diagnostico, guardar_optimizacion
from src.nlg.response_generator import ResponseGenerator


class DialogueManager:
    """Gestiona el flujo de interacción, estado y transiciones."""

    def __init__(self, ctx: dict, sesion_uuid: str, sesion_db_id: int):
        self.ctx = ctx
        self.sesion_uuid = sesion_uuid
        self.sesion_db_id = sesion_db_id

        self.motor = MotorReglas()
        self.bayes = RedBayesianaCafe()
        self.ag = OptimizacionGenetica(generaciones=40, tam_poblacion=60)
        self.clima = ModuloClima(departamento=self.ctx.get("departamento_zona", "Matagalpa"))
        self.llm = OraculoAgronomoLLM(perfil=self.ctx.get("perfil", "pequeno_productor"))
        self.nlg = ResponseGenerator()

    def set_perfil(self, perfil: str):
        self.ctx["perfil"] = perfil
        self.llm.set_perfil(perfil)

    def set_departamento(self, depto: str):
        self.ctx["departamento_zona"] = depto
        self.clima.set_departamento(depto)

    def autocompletar_clima(self) -> dict:
        """Autocompleta de forma segura las variables meteorológicas en self.ctx."""
        depto = self.ctx.get("departamento_zona", "Matagalpa")
        self.clima.set_departamento(depto)
        try:
            datos = self.clima.obtener_datos_actuales()
        except Exception:
            datos = {
                "temperatura": 22.0,
                "humedad_relativa": 80.0,
                "precipitacion_24h": 0.0,
                "fuente": "Fallback local por zona",
            }

        temp = float(datos.get("temperatura", 22.0))
        hr = float(datos.get("humedad_relativa", 80.0))
        lluvia = bool(datos.get("precipitacion_24h", 0) > 0)

        self.ctx["temperatura"] = temp
        self.ctx["humedad_relativa"] = hr
        self.ctx["lluvia_previa"] = lluvia
        self.ctx["clima_auto"] = datos
        self.ctx["clima"] = {
            "temperatura": temp,
            "humedad_relativa": hr,
            "lluvia_previa": lluvia,
            "fuente": datos.get("fuente", "Estimado meteorologico"),
        }
        return datos

    def despachar(self, intent: str, texto_usuario: str, historial_chat: list) -> tuple:
        """Enruta la intención hacia la acción correspondiente según el estado."""
        try:
            if intent == "Confirmar_Accion":
                return ("Acción confirmada. ¿En qué más puedo ayudarle?", intent, False)

            if intent == "Cancelar_Operacion":
                self.ctx["flujo_pendiente"] = None
                return ("Operación cancelada. Puede iniciar una nueva consulta.", intent, False)

            if intent == "Solicitar_Ayuda":
                return (self.nlg.formatear_ayuda(), intent, False)

            if intent == "Optimizar_Plan_Fertilizacion_Riego":
                return self._flujo_optimizacion()

            if intent == "Generar_Reporte_PDF":
                return self._flujo_reporte()

            if intent == "Sincronizar_Clima_Entorno":
                depto = self.ctx.get("departamento_zona", "Matagalpa")
                self.clima.set_departamento(depto)
                datos = self.clima.obtener_datos_actuales()
                self.ctx["clima"] = {
                    "temperatura": datos["temperatura"],
                    "humedad_relativa": datos["humedad_relativa"],
                    "lluvia_previa": datos["precipitacion_24h"] > 0,
                    "fuente": datos["fuente"],
                }
                return (
                    f"Clima en {depto}: {datos['temperatura']} °C, "
                    f"HR {datos['humedad_relativa']} %, lluvia 24h: {datos['precipitacion_24h']} mm.",
                    intent, False,
                )

            if intent == "Consultar_Precios_Mercado":
                p = actualizar_precios()
                return (
                    f"Precio del café: {p['precio_cafe_oro_qq_usd']} USD/qq. "
                    f"Tipo de cambio: {p['tipo_cambio_usd_nio']} NIO/USD.",
                    intent, False,
                )

            if intent == "Consultar_Diagnostico_Sintoma":
                return self._flujo_diagnostico()

            # Fallback Oráculo LLM
            if self.llm._esta_corriendo():
                contexto = self._contexto_finca_texto()
                respuesta = self.llm.consultar_oraculo(texto_usuario, contexto, historial_chat)
                return (respuesta, "Consultar_Oraculo_LLM_Fallback", False)

            return ("El Oráculo LLM está apagado.", "Consultar_Oraculo_LLM_Fallback", False)
        except Exception as e:
            return (f"Error interno: {e}", intent, True)

    def _flujo_diagnostico(self) -> tuple:
        """Cuestionario secuencial e inferencia diagnóstica."""
        if "lluvia_previa" not in self.ctx:
            self.ctx["flujo_pendiente"] = "lluvia"
            return (
                "Ha llovido fuerte en su parcela en las ultimas 24 horas? (Si/No/'no se')",
                "Consultar_Diagnostico_Sintoma", False,
            )
        if "temperatura" not in self.ctx:
            self.ctx["flujo_pendiente"] = "temp"
            return (
                "Cual es la temperatura aproximada? (o escriba 'no se')",
                "Consultar_Diagnostico_Sintoma", False,
            )
        if "humedad_relativa" not in self.ctx:
            self.ctx["flujo_pendiente"] = "hr"
            return (
                "Cual es la humedad relativa aproximada? (o escriba 'no se')",
                "Consultar_Diagnostico_Sintoma", False,
            )

        self.ctx["flujo_pendiente"] = None
        sintoma_final = self.ctx.get("sintoma_observado", "")
        if not sintoma_final and self.ctx.get("imagenes_analizadas"):
            ultima_img = self.ctx["imagenes_analizadas"][-1]
            mapa = {
                "Roya": "manchas_naranjas",
                "Antracnosis": "manchas_negras",
                "Deficiencia_Nitrogeno": "hojas_amarillas",
                "Ojo_de_gallo": "manchas_circulares",
                "Mancha_de_hierro": "mancha_cafe_rojiza",
            }
            sintoma_final = mapa.get(ultima_img.get("clase"), "")
            if sintoma_final:
                self.ctx["sintoma_observado"] = sintoma_final

        hechos = {
            "sintoma_observado": sintoma_final,
            "humedad_relativa": self.ctx["humedad_relativa"],
            "temperatura": self.ctx["temperatura"],
            "lluvia_previa": self.ctx["lluvia_previa"],
        }
        diags = self.motor.inferir(hechos)
        self.ctx["diagnosticos"] = diags

        riesgo = self.bayes.evaluar(
            lluvia=hechos["lluvia_previa"],
            hr=hechos["humedad_relativa"],
            temp=hechos["temperatura"],
            sintoma=hechos["sintoma_observado"],
        )
        self.ctx["riesgo"] = riesgo

        principal = diags[0]
        guardar_diagnostico(self.sesion_db_id, principal.get("regla_id"), principal.get("diagnostico", ""), riesgo)

        perfil = self.ctx.get("perfil", "pequeno_productor")
        respuesta = self.nlg.formatear_diagnostico(principal, riesgo, perfil)
        return (respuesta, "Consultar_Diagnostico_Sintoma", False)

    def _flujo_optimizacion(self) -> tuple:
        sup = float(self.ctx.get("superficie_manzanas", 1.0))
        riesgo_roya = float(self.ctx.get("riesgo", {}).get("roya", 0.65)) * 100
        res = self.ag.optimizar(superficie_mz=sup, riesgo_roya_pct=riesgo_roya, verbose=False)
        self.ctx["optimizacion"] = res
        guardar_optimizacion(self.sesion_db_id, res)
        msg = self.nlg.formatear_optimizacion(res, sup)
        return (msg, "Optimizar_Plan_Fertilizacion_Riego", False)

    def _flujo_reporte(self) -> tuple:
        if not self.ctx.get("clima"):
            try:
                depto = self.ctx.get("departamento_zona", "Matagalpa")
                self.clima.set_departamento(depto)
                d = self.clima.obtener_datos_actuales()
                self.ctx["clima"] = {
                    "temperatura": d["temperatura"],
                    "humedad_relativa": d["humedad_relativa"],
                    "lluvia_previa": d["precipitacion_24h"] > 0,
                    "fuente": d["fuente"],
                }
            except Exception:
                pass

        datos = {
            "sesion_id": self.sesion_uuid,
            "zona": self.ctx.get("departamento_zona", "Matagalpa"),
            "superficie_manzanas": self.ctx.get("superficie_manzanas", 1.0),
            "clima": self.ctx.get("clima", {}),
            "diagnosticos": self.ctx.get("diagnosticos", []),
            "riesgo": self.ctx.get("riesgo", {}),
            "optimizacion": self.ctx.get("optimizacion", {}),
            "imagenes": self.ctx.get("imagenes_analizadas", []),
        }
        ruta = generar_reporte(datos, nombre=f"reporte_{self.sesion_uuid}.pdf")
        ruta_desc = exportar_a_descargas(ruta)
        desc_info = f"\nCopia en Descargas: {ruta_desc}" if ruta_desc else ""
        return (f"Reporte PDF generado: {ruta}{desc_info}", "Generar_Reporte_PDF", False)

    def _contexto_finca_texto(self) -> str:
        partes = []
        if self.ctx.get("departamento_zona"):
            partes.append(f"Ubicación: {self.ctx['departamento_zona']}")
        if self.ctx.get("superficie_manzanas"):
            partes.append(f"Superficie: {self.ctx['superficie_manzanas']} mz")
        if self.ctx.get("imagenes_analizadas"):
            clases = [img["clase"] for img in self.ctx["imagenes_analizadas"]]
            partes.append(f"Enfermedades vistas en fotos: {', '.join(clases)}")
        if self.ctx.get("diagnosticos"):
            partes.append(f"Diagnóstico previo: {self.ctx['diagnosticos'][0]['diagnostico']}")
        if self.ctx.get("clima"):
            c = self.ctx["clima"]
            partes.append(f"Clima: {c.get('temperatura')}°C, HR {c.get('humedad_relativa')}%")
        return " | ".join(partes) if partes else "Sin datos previos."

