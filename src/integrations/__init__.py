from src.integrations.clima import ClimaIntegration
from src.integrations.mercado import MercadoIntegration
from src.integrations.web_channel import WebChannelAdapter
from src.integrations.telegram_bot import TelegramBotChannel

__all__ = [
    "ClimaIntegration",
    "MercadoIntegration",
    "WebChannelAdapter",
    "TelegramBotChannel",
]
