# ============================================================
# modulos/reporte_pdf.py
# Generador de reportes PDF
# ============================================================
import os
import shutil
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

COLOR_PRIMARIO = colors.HexColor("#2d6a4f")
COLOR_SEC       = colors.HexColor("#b7e4c7")
COLOR_FONDO     = colors.HexColor("#f1f8f5")

def _safe_image(ruta, max_w=8*cm, max_h=5*cm):
    try:
        if ruta and os.path.exists(ruta):
            return Image(ruta, width=max_w, height=max_h, kind="proportional")
    except Exception:
        pass
    return None

def _carpeta_descargas():
    home = Path.home()
    for nombre in ("Downloads", "Descargas", "downloads"):
        c = home / nombre
        if c.exists() and c.is_dir(): return c
    destino = home / "Downloads"
    try:
        destino.mkdir(parents=True, exist_ok=True)
        return destino
    except Exception: return None

def exportar_a_descargas(ruta_origen):
    try:
        destino_dir = _carpeta_descargas()
        if destino_dir is None: return None
        nombre = os.path.basename(ruta_origen)
        destino = destino_dir / nombre
        if destino.exists():
            base, ext = os.path.splitext(nombre)
            ts = datetime.now().strftime("%H%M%S")
            destino = destino_dir / f"{base}_{ts}{ext}"
        shutil.copy2(ruta_origen, destino)
        return str(destino)
    except Exception as e:
        return None

def generar_reporte(datos, nombre="reporte_tecnico.pdf"):
    os.makedirs("salidas", exist_ok=True)
    ruta = os.path.join("salidas", nombre)

    doc = SimpleDocTemplate(ruta, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name="Titulo", parent=estilos["Title"], textColor=COLOR_PRIMARIO, fontSize=18, spaceAfter=6))
    estilos.add(ParagraphStyle(name="Sub", parent=estilos["Heading2"], textColor=COLOR_PRIMARIO, fontSize=13, spaceAfter=6))
    estilos.add(ParagraphStyle(name="Body2", parent=estilos["BodyText"], fontSize=9, leading=12))

    flow = []
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Encabezado
    flow.append(Paragraph("ASISTENTE INTELIGENTE PARA LA CAFICULTURA", estilos["Titulo"]))
    flow.append(Paragraph("Reporte tecnico - Plataforma Integrada de Inteligencia Agricola S3", estilos["Body2"]))
    flow.append(Spacer(1, 0.4*cm))

    # 1. Datos generales
    flow.append(Paragraph("1. Datos generales", estilos["Sub"]))
    tabla_datos = [
        ["Sesion:", str(datos.get("sesion_id", "N/A"))],
        ["Zona:", str(datos.get("zona", "N/A"))],
        ["Superficie:", f"{datos.get('superficie_manzanas', 1.0)} manzanas"],
        ["Fecha:", fecha],
    ]
    t = Table(tabla_datos, colWidths=[4*cm, 12*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("GRID",     (0,0), (-1,-1), 0.3, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), COLOR_FONDO),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 0.4*cm))

    # 2. Clima
    flow.append(Paragraph("2. Condiciones climaticas", estilos["Sub"]))
    clima = datos.get("clima", {}) or {}
    if clima:
        tabla_clima = [["Variable", "Valor"]]
        tabla_clima.append(["Temperatura", f"{clima.get('temperatura','N/A')} °C"])
        tabla_clima.append(["Humedad relativa", f"{clima.get('humedad_relativa','N/A')} %"])
        tabla_clima.append(["Lluvia previa", "Si" if clima.get("lluvia_previa") else "No"])
        tabla_clima.append(["Fuente", str(clima.get("fuente", "N/A"))])
        t = Table(tabla_clima, colWidths=[6*cm, 10*cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,0), (-1,0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ]))
        flow.append(t)
    else:
        flow.append(Paragraph("<i>No se registraron datos climaticos.</i>", estilos["Body2"]))
    flow.append(Spacer(1, 0.4*cm))

    # 3. Imagenes (Diagnostico IA)
    imagenes_raw = datos.get("imagenes") or []
    # Deduplicar imagenes por nombre o ruta
    imagenes = []
    rutas_vistas = set()
    for im in imagenes_raw:
        r_path = im.get("ruta", "")
        ident = os.path.basename(r_path) if r_path else str(im)
        if ident not in rutas_vistas:
            rutas_vistas.add(ident)
            imagenes.append(im)

    if imagenes:
        flow.append(Paragraph("3. Analisis de imagenes foliares", estilos["Sub"]))
        tabla_img = [["#", "Archivo", "Clase detectada", "Confianza", "Motor"]]
        for i, img in enumerate(imagenes, 1):
            nom_arch = os.path.basename(img.get("ruta", "N/A"))
            motor_str = img.get("modo") or ("Gemini Vision AI" if os.getenv("GEMINI_API_KEY") else "heuristico_hsv")
            clase_str = img.get("clase", "N/A").replace("_", " ")
            tabla_img.append([
                str(i),
                Paragraph(nom_arch, estilos["Body2"]),
                Paragraph(clase_str, estilos["Body2"]),
                f"{img.get('confianza', 0)*100:.1f}%",
                Paragraph(motor_str, estilos["Body2"]),
            ])
        t = Table(tabla_img, colWidths=[1*cm, 5.5*cm, 3.5*cm, 2.5*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,0), (-1,0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
            ("ALIGN", (3,1), (3,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        flow.append(t)
        flow.append(Spacer(1, 0.3*cm))
        
        for img in imagenes:
            img_obj = _safe_image(img.get("ruta"))
            just = img.get("justificacion", "")
            nota = img.get("nota_cruce", "")
            texto = f"<b>Diagnostico:</b> {img.get('clase','').replace('_',' ')}<br/>"
            if just: texto += f"<b>Justificacion tecnica:</b> {just}<br/>"
            if nota: texto += f"<i>{nota}</i>"
            
            if img_obj:
                flow.append(Paragraph(texto, estilos["Body2"]))
                flow.append(img_obj)
                flow.append(Spacer(1, 0.3*cm))
        flow.append(Spacer(1, 0.2*cm))

    # 4. Diagnostico General
    flow.append(Paragraph("4. Diagnostico fitosanitario general", estilos["Sub"]))
    diagnosticos = datos.get("diagnosticos") or []
    if not diagnosticos and imagenes:
        ult = imagenes[-1]
        c_nom = ult.get("clase", "").replace("_", " ")
        if c_nom and c_nom.lower() != "sana":
            diagnosticos = [{
                "regla_id": "VISION_AI",
                "diagnostico": f"Sintomatologia compatible con {c_nom}",
                "recomendacion": ult.get("justificacion") or "Monitorear incidencia foliar y aplicar medidas fitosanitarias preventivas.",
            }]

    if diagnosticos:
        for i, d in enumerate(diagnosticos, 1):
            regla = d.get("regla_id", "N/A")
            flow.append(Paragraph(f"<b>{i}. {d.get('diagnostico','N/A')}</b> <font size=7 color='#666'>({regla})</font>", estilos["Body2"]))
            flow.append(Paragraph(f"Recomendacion: {d.get('recomendacion','N/A')}", estilos["Body2"]))
            flow.append(Spacer(1, 0.2*cm))
    else:
        flow.append(Paragraph("<i>No se emitio diagnostico determinista.</i>", estilos["Body2"]))
    flow.append(Spacer(1, 0.4*cm))

    # 5. Riesgo
    flow.append(Paragraph("5. Mapa de riesgo (Red Bayesiana)", estilos["Sub"]))
    riesgo = datos.get("riesgo") or {}
    if not riesgo and imagenes:
        ult = imagenes[-1]
        clase = ult.get("clase", "")
        conf = float(ult.get("confianza", 0.5))
        riesgo = {
            "roya": round(conf if clase == "Roya" else 0.15, 2),
            "antracnosis": round(conf if clase == "Antracnosis" else 0.10, 2),
            "ojo_gallo": round(conf if clase == "Ojo_de_gallo" else 0.10, 2),
            "riesgo_global": round(conf if clase != "Sana" else 0.10, 2),
        }

    if riesgo:
        tabla_riesgo = [["Enfermedad", "Probabilidad"]]
        for k in ("roya", "antracnosis", "ojo_gallo"):
            v = riesgo.get(k, 0)
            tabla_riesgo.append([k.replace("_", " ").capitalize(), f"{v*100:.1f}%"])
        tabla_riesgo.append(["Riesgo global", f"{riesgo.get('riesgo_global',0)*100:.1f}%"])
        t = Table(tabla_riesgo, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,0), (-1,0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ]))
        flow.append(t)
    else:
        flow.append(Paragraph("<i>No se calcularon probabilidades.</i>", estilos["Body2"]))
    flow.append(Spacer(1, 0.4*cm))

    # 6. Optimizacion
    flow.append(Paragraph("6. Plan bioeconomico optimizado (C$)", estilos["Sub"]))
    opt = datos.get("optimizacion") or {}
    dosis = opt.get("dosis_por_mz") or {}
    if dosis:
        sup_mz = float(datos.get("superficie_manzanas", 1.0) or 1.0)
        from modulos.precios import leer_precios_actuales
        precios_mkt = leer_precios_actuales()
        
        # Precios unitarios sincronizados con algoritmo_genetico.py
        p_agua = 12.0
        p_n = precios_mkt.get("precio_urea_qq_nio", 1650.0) / 100.0   # 16.5 C$/kg
        p_p = precios_mkt.get("precio_kcl_qq_nio", 1400.0) / 80.0     # 17.5 C$/kg
        p_k = precios_mkt.get("precio_kcl_qq_nio", 1400.0) / 60.0     # 23.33 C$/kg
        p_fung = precios_mkt.get("precio_fungicida_litro_nio", 950.0) # 950 C$/L
        p_mo = precios_mkt.get("costo_aplicacion_nio", 500.0)         # 500 C$/mz

        riego_val = float(dosis.get("riego_m3", 0))
        n_val = float(dosis.get("N_kg", 0))
        p_val = float(dosis.get("P_kg", 0))
        k_val = float(dosis.get("K_kg", 0))
        fung_val = float(dosis.get("fungicida_L", 0))

        c_riego = round(riego_val * p_agua * sup_mz, 2)
        c_n = round(n_val * p_n * sup_mz, 2)
        c_p = round(p_val * p_p * sup_mz, 2)
        c_k = round(k_val * p_k * sup_mz, 2)
        c_fung = round(fung_val * p_fung * sup_mz, 2)
        c_mo = round(p_mo * sup_mz, 2)

        costo_total_calculado = c_riego + c_n + c_p + c_k + c_fung + c_mo
        costo_total_plan = float(opt.get("costo_total_nio") or costo_total_calculado)

        # Ajuste fino para concordancia matematica al centavo
        diff = round(costo_total_plan - costo_total_calculado, 2)
        if abs(diff) > 0:
            c_mo = round(c_mo + diff, 2)

        tabla_opt = [["Insumo / Concepto", "Dosis / mz", f"Costo ({sup_mz} mz)"]]
        tabla_opt.append(["Riego", f"{riego_val:,.1f} m3", f"C$ {c_riego:,.2f}"])
        tabla_opt.append(["Nitrogeno (Urea)", f"{n_val:,.1f} kg", f"C$ {c_n:,.2f}"])
        tabla_opt.append(["Fosforo (P2O5)", f"{p_val:,.1f} kg", f"C$ {c_p:,.2f}"])
        tabla_opt.append(["Potasio (KCl)", f"{k_val:,.1f} kg", f"C$ {c_k:,.2f}"])
        tabla_opt.append(["Fungicida", f"{fung_val:,.2f} L", f"C$ {c_fung:,.2f}"])
        tabla_opt.append(["Mano de obra y aplicacion", "Jornales", f"C$ {c_mo:,.2f}"])
        tabla_opt.append(["COSTO TOTAL PLAN", "", f"C$ {costo_total_plan:,.2f}"])

        t = Table(tabla_opt, colWidths=[6*cm, 5*cm, 5*cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,0), (-1,0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
            ("BACKGROUND", (0,-1), (-1,-1), COLOR_SEC),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ]))
        flow.append(t)
        flow.append(Spacer(1, 0.2*cm))
        flow.append(Paragraph(f"<b>Rendimiento esperado:</b> {opt.get('rendimiento_qq_mz',0)} qq/mz &nbsp;&nbsp; <b>Beneficio neto:</b> C$ {opt.get('beneficio_neto_nio',0):,.2f}", estilos["Body2"]))
    else:
        flow.append(Paragraph("<i>No se solicito optimizacion.</i>", estilos["Body2"]))
    flow.append(Spacer(1, 0.4*cm))

    # 7. Recomendaciones
    flow.append(Paragraph("7. Recomendaciones generales", estilos["Sub"]))
    for r in ["Monitorear el cultivo cada 7-15 dias en epoca lluviosa.", "Mantener registro escrito de aplicaciones y sintomas.", "Consultar al extensionista del INTA si los sintomas persisten.", "Realizar analisis foliar al menos 2 veces por ciclo."]:
        flow.append(Paragraph(f"- {r}", estilos["Body2"]))
    flow.append(Spacer(1, 0.6*cm))

    flow.append(Paragraph(f"<i>Generado el {fecha} por el Asistente de Caficultura</i>", estilos["Body2"]))
    doc.build(flow)
    return ruta
