"""
verificar_ia.py
Script de diagnostico para comprobar la disponibilidad y respuesta de los motores de IA
(Google Gemini y Ollama local con LLaMA 3.2).
"""
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
load_dotenv()

from modulos.llm_fallback import OraculoAgronomoLLM
from modulos.chatbot import ChatbotCaficultura

def probar_gemini(llm: OraculoAgronomoLLM):
    print("\n" + "=" * 60)
    print(" 1. VERIFICACION DE GOOGLE GEMINI API")
    print("=" * 60)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print(" [AVISO] No se encontro GEMINI_API_KEY en .env")
        return False
    print(f" [OK] GEMINI_API_KEY detectada (prefijo: {key[:8]}...)")
    
    t0 = time.time()
    try:
        from google.genai import types
        contents = [types.Content(role="user", parts=[types.Part(text="Responde brevemente: OK")])]
        respuesta = llm._generar_con_gemini(contents, "Eres un asistente util.")
        duracion = time.time() - t0
        print(f" [OK] Gemini respondio en {duracion:.2f}s:")
        print(f"      \"{respuesta.strip()}\"")
        return True
    except Exception as e:
        duracion = time.time() - t0
        print(f" [FALLO] Error al consultar Gemini ({duracion:.2f}s): {e}")
        return False

def probar_ollama(llm: OraculoAgronomoLLM):
    print("\n" + "=" * 60)
    print(" 2. VERIFICACION DE OLLAMA LOCAL")
    print("=" * 60)
    host = llm._get_ollama_host()
    print(f" Host de conexion: {host}")
    print(f" Modelo esperado: {llm.modelo_ollama}")
    
    t0 = time.time()
    if not llm._ollama_ok and not llm._probar_ollama():
        duracion = time.time() - t0
        print(f" [AVISO] No se pudo conectar a Ollama en {host} ({duracion:.2f}s)")
        print("         Para iniciarlo, abra una terminal y ejecute:")
        print(f"         ollama run {llm.modelo_ollama}")
        return False
    
    try:
        mensajes = [{"role": "user", "content": "Di 'Ollama funcionando' en 2 palabras."}]
        r = llm.ollama_client.chat(model=llm.modelo_ollama, messages=mensajes, options={"temperature": 0.3})
        duracion = time.time() - t0
        print(f" [OK] Ollama {llm.modelo_ollama} respondio en {duracion:.2f}s:")
        print(f"      \"{r['message']['content'].strip()}\"")
        return True
    except Exception as e:
        duracion = time.time() - t0
        print(f" [FALLO] Ollama fallo al generar respuesta ({duracion:.2f}s): {e}")
        return False

def probar_flujo_chat_con_imagen():
    print("\n" + "=" * 60)
    print(" 3. SIMULACION: FOTO DE ROYA -> 'Que hago con este tipo de enfermedad?'")
    print("=" * 60)
    bot = ChatbotCaficultura()
    # Simular imagen registrada desde el escaner
    bot.registrar_imagen(
        ruta="salidas/hoja_roya_test.jpg",
        clase="Roya",
        confianza=0.98,
        justificacion="Manchas cloroticas en haz y polvillo anaranjado en enves caracteristico de Hemileia vastatrix.",
        modo="Gemini Vision AI"
    )
    
    pregunta = "Que hago con este tipo de enfermedad?"
    print(f" Usuario pregunta: '{pregunta}'")
    t0 = time.time()
    respuesta, intent = bot.responder(pregunta)
    duracion = time.time() - t0
    
    print(f"\n Intencion detectada: [{intent}] ({duracion:.2f}s)")
    print(" Respuesta del asistente:")
    print("-" * 60)
    print(respuesta)
    print("-" * 60)
    assert intent == "Consultar_Tratamiento_Recomendacion", f"Esperado Consultar_Tratamiento_Recomendacion, obtenido {intent}"
    assert "lluvia" not in respuesta.lower() or "fungicida" in respuesta.lower(), "La respuesta no debio ser la pregunta de lluvia"
    print(" [OK] Flujo superado con exito. El asistente respondio con manejo agronomico.")

def main():
    print("*" * 60)
    print("   VERIFICADOR DE CONECTIVIDAD IA - ASISTENTE CAFICULTURA")
    print("*" * 60)
    llm = OraculoAgronomoLLM()
    
    g_ok = probar_gemini(llm)
    o_ok = probar_ollama(llm)
    
    print("\n" + "=" * 60)
    print(" RESUMEN DE MOTORES")
    print("=" * 60)
    print(f" - Gemini API: {'DISPONIBLE' if g_ok else 'NO DISPONIBLE'}")
    print(f" - Ollama Local: {'DISPONIBLE' if o_ok else 'NO DISPONIBLE'}")
    
    probar_flujo_chat_con_imagen()
    print("\n Diagnostico completado.")

if __name__ == "__main__":
    main()
