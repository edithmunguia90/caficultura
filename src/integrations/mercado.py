"""
src/integrations/mercado.py
Integración con mercados de materias primas y divisas.
"""
from modulos.precios import leer_precios_actuales, actualizar_precios

class MercadoIntegration:
    """Canal de consulta de indicadores financieros del sector café."""

    @staticmethod
    def obtener_indicadores():
        return leer_precios_actuales()

    @staticmethod
    def sincronizar_en_vivo():
        return actualizar_precios()

