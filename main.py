"""Interfaz de consola del Asistente Caficultura."""
import sys
from modulos.chatbot import ChatbotCaficultura


def main():
    print("=" * 62)
    print("  ASISTENTE INTELIGENTE PARA LA CAFICULTURA")
    print("  Consola interactiva. Escriba 'salir' para terminar.")
    print("=" * 62)

    bot = ChatbotCaficultura(perfil="pequeno_productor")
    print(f"  Sesion: {bot.sesion_uuid}")
    print("-" * 62)

    while True:
        try:
            entrada = input("\nUSUARIO: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesion terminada.")
            break

        if not entrada:
            continue
        if entrada.lower() in ("salir", "exit", "quit"):
            print("Hasta luego. Buenas cosechas.")
            break

        respuesta, intent = bot.responder(entrada)
        print(f"\nASISTENTE [{intent}]:")
        print(respuesta)


if __name__ == "__main__":
    main()
