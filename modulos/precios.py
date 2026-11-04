# ============================================================
# modulos/precios.py
# Automatizacion de precios de cafe y tipo de cambio
# Referencia: IA.docx Pag. 40
# ============================================================
import json
import requests
import yfinance as yf
from datetime import datetime
from config import (
    RUTA_PRECIOS, TIPO_CAMBIO_USD_NIO, PRECIO_CAFE_QQ_USD,
    COSTO_MANO_OBRA_DIA_NIO,
)

VALORES_DEFECTO = {
    "tipo_cambio_usd_nio":       TIPO_CAMBIO_USD_NIO,
    "precio_cafe_oro_qq_usd":    PRECIO_CAFE_QQ_USD,
    "costo_mano_obra_dia_nio":   COSTO_MANO_OBRA_DIA_NIO,
    "precio_urea_qq_nio":        1650.0,
    "precio_kcl_qq_nio":         1400.0,
    "precio_fungicida_litro_nio": 950.0,
    "costo_aplicacion_nio":      500.0,
    "ultima_actualizacion":      "2026-09-08",
    "es_en_vivo":                False,
    "fuente_precio_cafe":        "Respaldo local",
    "fuente_tipo_cambio":        "Respaldo local",
}


# ------------------------------------------------------------
def obtener_tipo_cambio(detallado=False):
    """Consulta el tipo de cambio USD/NIO desde open.er-api.com (gratis)."""
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
        r.raise_for_status()
        tasa = float(r.json()["rates"]["NIO"])
        val, vivo, fuente = round(tasa, 4), True, "Open Exchange Rates (API en vivo)"
    except Exception as e:
        print(f"[precios] Fallo tipo de cambio en vivo: {e}. Usando respaldo.")
        val, vivo, fuente = TIPO_CAMBIO_USD_NIO, False, "Respaldo local (config)"

    if detallado:
        return val, vivo, fuente
    return val


# ------------------------------------------------------------
def obtener_precio_cafe(detallado=False):
    """
    Consulta el precio del cafe arabica (KC=F) en Yahoo Finance.
    yfinance devuelve el precio en centavos USD/libra.
    1 quintal = 100 libras, por lo que el valor crudo ya es USD/qq.
    """
    try:
        cafe = yf.Ticker("KC=F")
        hist = cafe.history(period="5d")
        if hist is not None and not hist.empty and "Close" in hist:
            raw = float(hist["Close"].dropna().iloc[-1])
            precio_qq = raw if raw > 10 else raw * 100.0
            if 100.0 <= precio_qq <= 500.0:
                val, vivo, fuente = round(precio_qq, 2), True, "Yahoo Finance (KC=F en vivo)"
                if detallado:
                    return val, vivo, fuente
                return val
    except Exception as e:
        print(f"[precios] Fallo consulta KC=F en Yahoo Finance: {e}")

    val, vivo, fuente = PRECIO_CAFE_QQ_USD, False, "Respaldo local (config)"
    if detallado:
        return val, vivo, fuente
    return val


# ------------------------------------------------------------
def actualizar_precios():
    """Actualiza el JSON con los precios mas recientes y estado de conexion."""
    datos = VALORES_DEFECTO.copy()
    precio_cafe, cafe_en_vivo, fuente_cafe = obtener_precio_cafe(detallado=True)
    tipo_cambio, cambio_en_vivo, fuente_cambio = obtener_tipo_cambio(detallado=True)

    datos["precio_cafe_oro_qq_usd"] = precio_cafe
    datos["tipo_cambio_usd_nio"]    = tipo_cambio
    datos["cafe_en_vivo"]           = cafe_en_vivo
    datos["cambio_en_vivo"]         = cambio_en_vivo
    datos["es_en_vivo"]             = bool(cafe_en_vivo and cambio_en_vivo)
    datos["fuente_precio_cafe"]     = fuente_cafe
    datos["fuente_tipo_cambio"]     = fuente_cambio
    datos["ultima_actualizacion"]   = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        with open(RUTA_PRECIOS, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[precios] Error guardando: {e}")

    return datos


# ------------------------------------------------------------
def leer_precios_actuales():
    """Lee el JSON o genera uno nuevo si no existe."""
    try:
        with open(RUTA_PRECIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return actualizar_precios()


# ------------------------------------------------------------
if __name__ == "__main__":
    print("Actualizando precios de mercado...")
    p = actualizar_precios()
    for k, v in p.items():
        print(f"{k:32s}: {v}")
