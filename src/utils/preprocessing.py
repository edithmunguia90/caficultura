import re
import unicodedata

def normalizar_texto(texto: str) -> str:
    """Limpia y estandariza el texto del usuario preservando el significado."""
    if not texto:
        return ""
    texto = texto.strip().lower()
    # Estandarizar espacios
    texto = re.sub(r"\s+", " ", texto)
    return texto

def remover_acentos(texto: str) -> str:
    """Remueve tildes para comparaciones insensibles a diacríticos."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

