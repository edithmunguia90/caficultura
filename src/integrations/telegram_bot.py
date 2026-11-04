"""
src/integrations/telegram_bot.py
Adaptador de canal para Telegram Bot API (demostración o despliegue en mensajería).
"""
import os
from typing import Optional
from src.dialogue.dialogue_manager import DialogueManager


class TelegramBotChannel:
    """Manejador de canal Telegram para el Asistente Caficultura."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")

    def responder_mensaje(self, dm: DialogueManager, mensaje_texto: str) -> str:
        """Simula o despacha la respuesta conversacional a un mensaje de Telegram."""
        if not mensaje_texto:
            return "Por favor envía una consulta agronómica sobre café."
        respuesta, _ = dm.procesar_turno(mensaje_texto)
        return respuesta

