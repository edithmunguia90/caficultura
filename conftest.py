"""
conftest.py
Configuración de entorno de pruebas pytest para el proyecto Asistente Caficultura.
"""
import sys
import matplotlib
from pathlib import Path

# Modo headless sin GUI para generacion de graficos en pruebas
matplotlib.use("Agg")

# Asegurar que la raíz del proyecto esté en el sys.path para importaciones directas
RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))
