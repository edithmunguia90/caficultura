"""
src/integrations/web_channel.py
Adaptador de canal web para la integración con la interfaz gráfica Streamlit y API REST.
"""
from typing import Tuple, Optional
from src.dialogue.dialogue_manager import DialogueManager


class WebChannelAdapter:
    """Canal web para despachar mensajes y recibir respuestas estructuradas."""

    def __init__(self, dialogue_manager: DialogueManager):
        self.dm = dialogue_manager

    def procesar_mensaje(self, texto_usuario: str) -> Tuple[str, str]:
        """Procesa una consulta del usuario a través del canal web."""
        return self.dm.procesar_turno(texto_usuario)

