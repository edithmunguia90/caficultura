"""Agente experto con fallback de modelos LLM (Gemini / Ollama local)."""
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

PROMPTS_PERFIL = {
    "pequeno_productor": "Eres un tecnico agronomo amigable. Usa un lenguaje muy sencillo y soluciones practicas.",
    "extensionista_tecnico": "Eres un Ingeniero Agronomo especialista en fitopatologia. Usa terminologia cientifica rigurosa.",
    "administrador_finca": "Eres un asesor agroeconomico. Enfoca tus respuestas en la rentabilidad y costos en Cordobas."
}

SYSTEM_PROMPT_BASE = "Tus respuestas deben ser claras, concisas y profesionales. No utilices emojis. NUNCA digas 'No sé'."

PROMPT_VISION = """
Eres un fitopatologo experto en cafe. Analiza la imagen de esta hoja y clasificala en UNA de las siguientes categorias exactas:
- Sana
- Roya
- Antracnosis
- Ojo_de_gallo
- Mancha_de_hierro
- Deficiencia_Nitrogeno

Devuelve UNICAMENTE un objeto JSON con esta estructura exacta, sin texto adicional ni bloques de codigo:
{"clase": "Roya", "confianza": 0.95, "justificacion": "Explicacion breve de los sintomas visuales."}
"""

class OraculoAgronomoLLM:
    def __init__(self, modelo_ollama="llama3.2:3b", perfil="pequeno_productor"):
        self.modelo_ollama = modelo_ollama
        self.perfil = perfil
        self.api_key_gemini = os.getenv("GEMINI_API_KEY", "").strip()
        
        self.gemini_client = None
        self.error_gemini = ""
        
        if self.api_key_gemini:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.api_key_gemini)
            except Exception as e:
                self.error_gemini = f"Error al iniciar cliente: {str(e)}"
        else:
            self.error_gemini = "No se encontro GEMINI_API_KEY en el archivo .env"

        self.ollama_client = None
        self._ollama_ok = self._probar_ollama()
        
        self.modelos_gemini = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash",
            "gemini-3-flash-preview",
            "gemini-3.7-flash",
        ]

    def set_perfil(self, perfil):
        self.perfil = perfil

    def _get_system_prompt(self):
        return f"{SYSTEM_PROMPT_BASE}\n\nROL: {PROMPTS_PERFIL.get(self.perfil, PROMPTS_PERFIL['pequeno_productor'])}"

    def _get_ollama_host(self):
        host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
        if host in ("0.0.0.0", "0.0.0.0:11434") or host.startswith("http://0.0.0.0") or host == "0.0.0.0":
            return "http://127.0.0.1:11434"
        if not host.startswith("http://") and not host.startswith("https://"):
            return f"http://{host}"
        return host

    def _probar_ollama(self):
        try:
            import ollama
            host = self._get_ollama_host()
            self.ollama_client = ollama.Client(host=host, timeout=25)
            self.ollama_client.list()
            return True
        except Exception:
            return False

    def obtener_estado_ia(self) -> dict:
        """Devuelve el estado detallado de los motores LLM (Gemini y Ollama)."""
        gemini_ok = bool(self.gemini_client)
        gemini_info = f"Activo ({self.modelos_gemini[0]})" if gemini_ok else (self.error_gemini or "Inactivo")

        self._ollama_ok = self._probar_ollama()
        host_ol = self._get_ollama_host()
        ollama_info = f"Activo ({self.modelo_ollama})" if self._ollama_ok else "No detectado en " + host_ol

        return {
            "gemini_ok": gemini_ok,
            "gemini_info": gemini_info,
            "ollama_ok": self._ollama_ok,
            "ollama_info": ollama_info,
            "motor_principal": "Gemini AI" if gemini_ok else ("Ollama Local" if self._ollama_ok else "Sin conexion"),
        }

    def _esta_corriendo(self):
        return bool(self.gemini_client) or self._ollama_ok

    def _generar_con_gemini(self, contents, system_prompt):
        """Intenta con multiples modelos de Gemini hasta que uno responda con exito."""
        if not self.gemini_client:
            raise Exception("Cliente Gemini no inicializado.")
        
        from google.genai import types
        ultimo_error = None
        
        for modelo in self.modelos_gemini:
            try:
                response = self.gemini_client.models.generate_content(
                    model=modelo, contents=contents,
                    config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.4)
                )
                return response.text
            except Exception as e:
                ultimo_error = str(e)
                if "503" in ultimo_error or "404" in ultimo_error or "UNAVAILABLE" in ultimo_error:
                    continue 
                else:
                    raise Exception(ultimo_error)
        
        raise Exception(f"Modelos no disponibles: {ultimo_error}")

    def consultar_oraculo(self, consulta, contexto_finca="", historial=None):
        if not self._esta_corriendo():
            return "El servicio de IA no esta disponible."

        contexto_completo = f"CONTEXTO ACTUAL: {contexto_finca}\n\nPREGUNTA: {consulta}"
        historial = historial or []
        system_prompt = self._get_system_prompt()

        if self.gemini_client:
            try:
                from google.genai import types
                contents = []
                for msg in historial[-6:]:
                    rol = "user" if msg["role"] == "user" else "model"
                    contents.append(types.Content(role=rol, parts=[types.Part(text=msg["content"])]))
                contents.append(types.Content(role="user", parts=[types.Part(text=contexto_completo)]))

                return self._generar_con_gemini(contents, system_prompt)
            except Exception as e:
                print(f"[llm] Fallo consulta Gemini: {e}. Probando fallback Ollama...")

        if self._ollama_ok or self._probar_ollama():
            try:
                mensajes = [{"role": "system", "content": system_prompt}]
                for msg in historial[-6:]:
                    mensajes.append({"role": msg["role"], "content": msg["content"]})
                mensajes.append({"role": "user", "content": contexto_completo})
                r = self.ollama_client.chat(model=self.modelo_ollama, messages=mensajes, options={"temperature": 0.4})
                return r["message"]["content"]
            except Exception as e:
                return f"Error de Ollama: {e}"
        return "No se pudo obtener respuesta."

    def analizar_imagen_con_ia(self, ruta_imagen):
        if not self.gemini_client:
            return {"error": self.error_gemini}

        try:
            from PIL import Image
            from google.genai import types
            
            img = Image.open(ruta_imagen)
            texto_respuesta = self._generar_con_gemini([PROMPT_VISION, img], "Eres un fitopatologo experto.")
            
            texto = texto_respuesta.strip()
            if texto.startswith("```json"):
                texto = texto[7:-3]
            elif texto.startswith("```"):
                texto = texto[3:-3]
                
            data = json.loads(texto)
            return {
                "clase": data.get("clase", "Sana").replace(" ", "_"),
                "confianza": float(data.get("confianza", 0.5)),
                "justificacion": data.get("justificacion", ""),
                "modo": "Gemini Vision AI"
            }
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                return {"error": "API de Gemini deshabilitada. Active el servicio en Google Cloud."}
            elif "503" in error_msg:
                return {"error": "Servidores saturados temporalmente. Intente de nuevo."}
            else:
                return {"error": f"Fallo en vision: {error_msg[:50]}..."}
