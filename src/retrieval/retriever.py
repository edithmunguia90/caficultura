"""
src/retrieval/retriever.py
Módulo de recuperación de información (RAG) para el Asistente Caficultura.
Permite búsqueda semántica/léxica sobre documentos base y FAQs agronómicas.
"""
import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any
from src.utils.preprocessing import normalizar_texto

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class RecuperadorConocimiento:
    """Recuperador de documentos y pasajes agronómicos para aumento de contexto (RAG)."""

    def __init__(self, ruta_documentos: Path = None):
        self.ruta_documentos = ruta_documentos or (BASE_DIR / "data" / "raw")
        self.documentos: List[Dict[str, Any]] = []
        self._cargar_corpus()

    def _cargar_corpus(self):
        """Carga documentos base desde data/raw y data/intents."""
        self.documentos = []

        # 1. Cargar contexto agronómico raw
        ruta_ctx = self.ruta_documentos / "contexto_agronomico.txt"
        if not ruta_ctx.exists():
            ruta_ctx = BASE_DIR / "datos" / "contexto_agronomico.txt"

        if ruta_ctx.exists():
            with open(ruta_ctx, "r", encoding="utf-8") as f:
                bloques = f.read().split("\n\n")
                for i, b in enumerate(bloques):
                    b_strip = b.strip()
                    if b_strip:
                        self.documentos.append({
                            "id": f"contexto_{i+1}",
                            "fuente": "contexto_agronomico.txt",
                            "texto": b_strip,
                            "tokens": set(normalizar_texto(b_strip).split()),
                        })

        # 2. Cargar FAQs/intents desde data/intents/intents.json
        ruta_intents = BASE_DIR / "data" / "intents" / "intents.json"
        if ruta_intents.exists():
            try:
                with open(ruta_intents, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("intents", []):
                        tag = item.get("intent", "general")
                        ejemplos = " ".join(item.get("ejemplos", []))
                        respuestas = " ".join(item.get("respuestas", []))
                        texto_completo = f"Intencion {tag}: {ejemplos} -> {respuestas}"
                        self.documentos.append({
                            "id": f"intent_{tag}",
                            "fuente": "intents.json",
                            "texto": texto_completo,
                            "tokens": set(normalizar_texto(texto_completo).split()),
                        })
            except Exception:
                pass

    def recuperar(self, consulta: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Recupera los fragmentos más relevantes para una consulta dada usando similitud Jaccard/BM25."""
        if not consulta or not self.documentos:
            return []

        tokens_q = set(normalizar_texto(consulta).split())
        if not tokens_q:
            return []

        puntuados = []
        for doc in self.documentos:
            interseccion = len(tokens_q.intersection(doc["tokens"]))
            if interseccion > 0:
                union = len(tokens_q.union(doc["tokens"]))
                score = interseccion / (union if union > 0 else 1.0)
                # Ponderar por coincidencia exacta
                score += (interseccion * 0.1)
                puntuados.append((score, doc))

        puntuados.sort(key=lambda x: x[0], reverse=True)
        resultados = []
        for score, doc in puntuados[:top_k]:
            resultados.append({
                "id": doc["id"],
                "fuente": doc["fuente"],
                "texto": doc["texto"],
                "score": round(score, 4),
            })
        return resultados

    def obtener_contexto_formateado(self, consulta: str, top_k: int = 2) -> str:
        """Devuelve un bloque de texto concatenado listo para ser inyectado en el prompt de LLM."""
        recuperados = self.recuperar(consulta, top_k=top_k)
        if not recuperados:
            return ""
        fragmentos = [f"[{r['fuente']}]: {r['texto']}" for r in recuperados]
        return "\n\n".join(fragmentos)

