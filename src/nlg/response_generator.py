"""
src/nlg/response_generator.py
Modulo de NLG: Generador de respuestas y formateo adaptativo por perfil.
"""

class ResponseGenerator:
    """Genera respuestas en lenguaje natural según el perfil del usuario."""

    @staticmethod
    def formatear_diagnostico(principal: dict, riesgo: dict, perfil: str) -> str:
        """Formatea el diagnóstico determinista y probabilístico según el rol."""
        diag_nombre = principal.get("diagnostico", "Sin diagnostico concluyente")
        recom = principal.get("recomendacion", "Consulte con su extensionista.")
        regla_id = principal.get("regla_id", "N/A")
        riesgo_global = riesgo.get("riesgo_global", 0.0)

        if perfil == "pequeno_productor":
            nivel = "ALTO" if riesgo_global > 0.5 else "BAJO"
            return (
                f"Diagnostico: Su cafe tiene {diag_nombre}.\n"
                f"Que hacer: {recom}\n"
                f"Nivel de riesgo: {nivel} ({riesgo_global*100:.1f}%)"
            )
        elif perfil == "administrador_finca":
            return (
                f"Diagnostico fitosanitario: {diag_nombre} (Regla {regla_id})\n"
                f"Accion de mitigacion recomendada: {recom}\n"
                f"Evaluacion de impacto economico y riesgo:\n"
                f"  - Probabilidad de Roya: {riesgo.get('roya', 0)*100:.1f}%\n"
                f"  - Probabilidad de Antracnosis: {riesgo.get('antracnosis', 0)*100:.1f}%\n"
                f"  - Probabilidad de Ojo de gallo: {riesgo.get('ojo_gallo', 0)*100:.1f}%\n"
                f"  - Indice de Riesgo Global: {riesgo_global*100:.1f}%"
            )
        else: # extensionista_tecnico
            return (
                f"Diagnostico presuntivo: {diag_nombre} ({regla_id})\n"
                f"Recomendacion: {recom}\n"
                f"Niveles de riesgo (probabilidades):\n"
                f"  - Roya: {riesgo.get('roya', 0)*100:.1f}%\n"
                f"  - Antracnosis: {riesgo.get('antracnosis', 0)*100:.1f}%\n"
                f"  - Ojo de gallo: {riesgo.get('ojo_gallo', 0)*100:.1f}%\n"
                f"Riesgo global: {riesgo_global*100:.1f}%"
            )

    @staticmethod
    def formatear_optimizacion(res: dict, superficie_mz: float) -> str:
        """Formatea el plan bioeconómico optimizado por el algoritmo genético."""
        d = res.get("dosis_por_mz", {})
        costo_total = res.get("costo_total_nio", 0.0)
        beneficio = res.get("beneficio_neto_nio", 0.0)
        rend = res.get("rendimiento_qq_mz", 0.0)

        return (
            f"Plan de fertilizacion y riego para {superficie_mz} mz:\n"
            f"- Riego: {d.get('riego_m3', 0)} m3/mz\n"
            f"- Nitrogeno: {d.get('N_kg', 0)} kg/mz\n"
            f"- Fosforo: {d.get('P_kg', 0)} kg/mz\n"
            f"- Potasio: {d.get('K_kg', 0)} kg/mz\n"
            f"- Fungicida: {d.get('fungicida_L', 0)} L/mz\n"
            f"Costo total: C$ {costo_total:,.2f}\n"
            f"Beneficio neto: C$ {beneficio:,.2f}\n"
            f"Rendimiento esperado: {rend} qq/mz"
        )

    @staticmethod
    def formatear_ayuda() -> str:
        """Devuelve el texto de ayuda del sistema."""
        return (
            "Soy tu Asistente Agronomo Experto para la caficultura.\n"
            "Puedes pedirme:\n"
            "- Diagnostico fitosanitario describiendo sintomas (ej. 'Tengo manchas naranjas en hojas')\n"
            "- Subir fotos de hojas para clasificar enfermedades con IA\n"
            "- Optimizar tu plan de fertilizacion y riego (ej. 'Optimizar fertilizacion para 2 manzanas')\n"
            "- Consultar precios de mercado del cafe y fertilizantes\n"
            "- Consultar el clima en tu departamento\n"
            "- Generar un reporte tecnico en PDF"
        )

