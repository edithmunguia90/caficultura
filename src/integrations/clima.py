"""
src/integrations/clima.py
Integración con servicios de meteorología para zonas cafetaleras.
"""
from modulos.clima_api import ModuloClima, DEPTO_COORDS

class ClimaIntegration:
    """Canal de consulta microclimática en tiempo real."""

    def __init__(self, departamento="Matagalpa"):
        self.cliente = ModuloClima(departamento=departamento)

    def obtener_clima(self, departamento=None):
        if departamento:
            self.cliente.set_departamento(departamento)
        return self.cliente.obtener_datos_actuales()

