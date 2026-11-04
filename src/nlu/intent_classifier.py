"""
src/nlu/intent_classifier.py
Modulo de NLU: Clasificador de intenciones y extractor de entidades.
"""
import re
from src.utils.preprocessing import normalizar_texto

NO_SE = (
    "no se", "no sé", "no lo se", "no lo sé", "no estoy seguro",
    "no estoy segura", "no tengo", "no tengo idea", "no recuerdo",
    "desconozco", "?", "??", "???", "nose", "ns",
)

SUPERFICIE_FACTORES = {
    "manzana": 1.0, "mz": 1.0,
    "hectarea": 1.4184, "hectárea": 1.4184, "ha": 1.4184,
    "m2": 0.00014184, "m²": 0.00014184, "metro": 0.00014184,
    "acre": 0.5735,
}

_DEPTO_ALIASES = {
    "boaco": "Boaco", "carazo": "Carazo", "chinandega": "Chinandega",
    "chontales": "Chontales", "esteli": "Esteli", "estelí": "Esteli",
    "granada": "Granada", "jinotega": "Jinotega", "leon": "Leon",
    "león": "Leon", "madriz": "Madriz", "managua": "Managua",
    "masaya": "Masaya", "matagalpa": "Matagalpa", "nueva segovia": "Nueva Segovia",
    "rio san juan": "Rio San Juan", "río san juan": "Rio San Juan",
    "rivas": "Rivas", "racen": "RACCN", "raccn": "RACCN",
    "costa caribe norte": "RACCN", "bilwi": "RACCN",
    "racas": "RACCS", "raccs": "RACCS", "costa caribe sur": "RACCS",
    "bluefields": "RACCS",
}

_SINTOMAS_MAP = {
    "manchas naranjas":  "manchas_naranjas",
    "mancha naranja":    "manchas_naranjas",
    "polvo amarillo":    "polvo_amarillo",
    "pustulas":          "pustulas",
    "pústulas":          "pustulas",
    "manchas negras":    "manchas_negras",
    "lesiones hundidas": "lesiones_hundidas",
    "muerte de ramas":   "muerte_ramas",
    "manchas circulares":"manchas_circulares",
    "borde cafe":        "borde_cafe",
    "borde café":        "borde_cafe",
    "centro gris":       "centro_gris",
    "hojas amarillas":   "hojas_amarillas",
    "clorosis uniforme": "clorosis_uniforme",
    "telarana blanca":   "telarana_blanca",
    "telaraña blanca":   "telarana_blanca",
    "hilos blancos":     "hilos_blancos",
    "mancha cafe rojiza":"mancha_cafe_rojiza",
    "mancha café rojiza":"mancha_cafe_rojiza",
    "halo amarillo":     "halo_amarillo",
    "mancha grasosa":    "mancha_grasosa",
    "raiz negra":        "raiz_negra",
    "raíz negra":        "raiz_negra",
    "granos perforados": "granos_perforados",
    "broca visible":     "broca_visible",
    "galerias hoja":     "galerias_hoja",
    "minas hoja":        "minas_hoja",
}

INTENTS = {
    "Confirmar_Accion": [
        r"^s[ií]$", r"^confirmo\b", r"^confirmar\b", r"^de acuerdo\b",
        r"^adelante\b", r"^ok$", r"^proceda\b", r"^acepto\b",
    ],
    "Cancelar_Operacion": [
        r"^cancel", r"^olv[ií]dalo", r"^detente", r"^para$",
    ],
    "Generar_Reporte_PDF": [
        r"generar reporte", r"\breporte\b", r"\bpdf\b", r"\bdocumento\b",
    ],
    "Optimizar_Plan_Fertilizacion_Riego": [
        r"optimizar", r"fertiliz", r"\bdosis\b", r"plan de riego",
        r"plan nutric", r"plan de fertilizaci[oó]n",
    ],
    "Sincronizar_Clima_Entorno": [
        r"\bclima\b", r"\btiempo\b", r"va a llover", r"temperatura actual",
    ],
    "Consultar_Precios_Mercado": [
        r"\bprecio", r"\bmercado\b", r"c[oó]rdoba", r"tipo de cambio",
        r"cuanto cuesta", r"cotizaci[oó]n",
    ],
    "Solicitar_Ayuda": [
        r"^ayuda\b", r"qu[eé] puedes", r"funciones", r"c[oó]mo funciona",
    ],
    "Consultar_Diagnostico_Sintoma": [
        r"mancha", r"s[ií]ntoma", r"enfermed", r"pustul", r"pústul", r"roya",
        r"antracnosis", r"ojo de gallo", r"hoja.{0,10}amarilla", r"polvo amarillo",
        r"broca", r"minador", r"nematodo", r"telara", r"telaraña",
        r"ra[ií]z", r"clorosis", r"deficien", r"puntos negros", r"halo amarillo",
        r"lesiones hundidas", r"muerte de ramas", r"granos perforados",
    ],
}


class IntentClassifier:
    """Clasificador de intenciones y extractor de entidades del dominio cafetero."""

    def __init__(self):
        self.intents = INTENTS
        self.sintomas = _SINTOMAS_MAP
        self.deptos = _DEPTO_ALIASES

    def predecir_intencion(self, texto: str) -> str:
        """Determina la intención priorizando comandos e intenciones directas."""
        t = normalizar_texto(texto)
        for intent, patrones in self.intents.items():
            for p in patrones:
                if re.search(p, t):
                    return intent
        return "Consultar_Oraculo_LLM_Fallback"

    def detectar_intent(self, texto: str):
        """Alias retrocompatible para detección de intención."""
        return self.predecir_intencion(texto)

    def extraer_entidades(self, texto: str, flujo_pendiente: str = None) -> dict:
        """Extrae entidades semánticas clave a partir de la entrada del usuario."""
        t = normalizar_texto(texto)
        stripped = t.strip()
        ents = {}

        # Detección de "no sé" durante un flujo pendiente de clima
        if flujo_pendiente in ("temp", "hr", "lluvia") and stripped in NO_SE:
            ents["_auto_clima"] = True
            return ents

        # Superficie de la finca
        m = re.search(
            r"(\d+(?:[.,]\d+)?)\s*(manzana|mz|hectarea|hectárea|ha|m2|m²|metro|acre)",
            t,
        )
        if m:
            valor = float(m.group(1).replace(",", "."))
            unidad = m.group(2).lower()
            ents["superficie_manzanas"] = round(valor * SUPERFICIE_FACTORES.get(unidad, 1.0), 4)
            ents["superficie_original"] = {"valor": valor, "unidad": unidad}
        else:
            m = re.search(r"(\d+(?:\.\d+)?)\s*manzana", t)
            if m:
                ents["superficie_manzanas"] = float(m.group(1))
                ents["superficie_original"] = {"valor": float(m.group(1)), "unidad": "manzana"}

        # Temperatura (°C)
        m = re.search(r"(\d+(?:\.\d+)?)\s*[°]?\s*(?:c\b|grados)", t)
        if m:
            ents["temperatura"] = float(m.group(1))
        elif flujo_pendiente == "temp":
            m = re.search(r"(\d+(?:\.\d+)?)", t)
            if m:
                ents["temperatura"] = float(m.group(1))

        # Humedad relativa (%)
        m = re.search(r"(\d+)\s*%\s*(?:de\s*)?humedad", t)
        if m:
            ents["humedad_relativa"] = float(m.group(1))
        elif flujo_pendiente == "hr":
            m = re.search(r"(\d+)", t)
            if m:
                ents["humedad_relativa"] = float(m.group(1))

        # Lluvia previa (24h)
        if any(w in t for w in ("llovio", "llovió", "si llovio", "si, llovio", "sí, llovió")):
            ents["lluvia_previa"] = True
        elif flujo_pendiente == "lluvia":
            if stripped in ("si", "sí", "s", "yes", "afirmativo"):
                ents["lluvia_previa"] = True
            elif stripped in ("no", "n", "negativo"):
                ents["lluvia_previa"] = False

        # Síntoma observado
        for kw, val in self.sintomas.items():
            if kw in t:
                ents["sintoma_observado"] = val
                break

        # Fase fenológica
        for kw, val in {
            "floracion": "floracion", "floración": "floracion",
            "llenado de grano": "llenado_grano", "llenado_grano": "llenado_grano",
            "maduración": "madurez", "madurez": "madurez",
            "crecimiento": "crecimiento", "vegetativo": "vegetativo",
        }.items():
            if kw in t:
                ents["fase_fenologica"] = val
                break

        # Departamento
        for alias, canon in self.deptos.items():
            if alias in t:
                ents["departamento_zona"] = canon
                break

        # Tipo de insumo (@tipo_insumo)
        if any(w in t for w in ("fertiliz", "urea", "npk", "18-46-0", "ferticafe", "ferticafé")):
            ents["tipo_insumo"] = "fertilizante"
        elif any(w in t for w in ("fungicid", "clorotalonil", "cobre", "triadimefon", "triadimefón", "mancozeb", "benomil")):
            ents["tipo_insumo"] = "fungicida"
        elif any(w in t for w in ("insecticid", "beauveria", "trichoderma", "paecilomyces")):
            ents["tipo_insumo"] = "biologico"
        elif any(w in t for w in ("riego", "agua", "m3")):
            ents["tipo_insumo"] = "agua"

        # Confirmación
        if stripped in ("si", "sí", "confirmo", "de acuerdo", "adelante", "ok", "proceda", "acepto"):
            ents["confirmacion"] = True
        elif stripped in ("no", "cancela", "negativo", "olvidalo"):
            ents["confirmacion"] = False

        return ents
