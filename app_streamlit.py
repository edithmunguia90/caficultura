import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st

from modulos.chatbot import ChatbotCaficultura, DEPARTAMENTOS
from modulos.clima_api import ModuloClima
from modulos.db import consultar_historial, obtener_stats
from modulos.kpis import calcular_csat, calcular_kpis, registrar_turno
from modulos.llm_fallback import OraculoAgronomoLLM
from modulos.precios import actualizar_precios, leer_precios_actuales
from modulos.reporte_pdf import exportar_a_descargas, generar_reporte
from modulos.sugerencias import sugerencias_iniciales, sugerencias_para_contexto
from modulos.ui_theme import aplicar_estilos_tema, render_status_pill
from modulos.vision_cnn import ClasificadorVisionCNN

st.set_page_config(
    page_title="Asistente Caficultura - UNA",
    layout="wide",
    initial_sidebar_state="expanded"
)

aplicar_estilos_tema()

if "bot" not in st.session_state:
    st.session_state.bot = ChatbotCaficultura()
    st.session_state.chat_historial = []
    st.session_state.cnn = ClasificadorVisionCNN()
    st.session_state.llm = OraculoAgronomoLLM()
    st.session_state.csat_enviado = False
    st.session_state.last_upload = None
    st.session_state.reporte_bytes = None
    st.session_state.reporte_nombre = None
    st.session_state.sugerencias_ultimas = set()
    st.session_state.clima_api = ModuloClima()
    st.session_state.last_perfil = None
    st.session_state.last_depto = None


def _cargar_reporte_en_sesion(respuesta: str):
    m = re.search(r"([\w/\\:.\-]+\.pdf)", respuesta)
    if not m:
        return
    ruta = m.group(1).strip().rstrip(".").rstrip(",")
    if os.path.exists(ruta):
        try:
            with open(ruta, "rb") as f:
                st.session_state.reporte_bytes = f.read()
            st.session_state.reporte_nombre = os.path.basename(ruta)
        except Exception:
            pass


def _reiniciar_sesion(perfil_key: str, depto: str, sup_val: float, sup_uni: str):
    st.session_state.bot = ChatbotCaficultura()
    st.session_state.bot.set_perfil(perfil_key)
    st.session_state.bot.set_departamento(depto)
    st.session_state.bot.set_superficie(sup_val, sup_uni)
    st.session_state.chat_historial = []
    st.session_state.csat_enviado = False
    st.session_state.last_upload = None
    st.session_state.reporte_bytes = None
    st.session_state.reporte_nombre = None
    st.session_state.sugerencias_ultimas = set()


# Panel de Control Lateral
with st.sidebar:
    st.title("Asistente Cafetalero")
    st.caption("Plataforma de Decisiones Agronomicas - UNA")
    st.write("")

    st.subheader("Perfil de Operacion")
    perfil_label = st.radio(
        "Rol activo en finca:",
        [
            "Pequeno facilitador tradicional",
            "Extensionista tecnica de campo",
            "Administrador de finca o cooperativa",
        ],
        index=0,
        label_visibility="collapsed",
    )

    if "Pequeno" in perfil_label:
        perfil_key = "pequeno_productor"
        nivel_detalle = "simple"
    elif "Extensionista" in perfil_label:
        perfil_key = "extensionista_tecnico"
        nivel_detalle = "tecnico"
    else:
        perfil_key = "administrador_finca"
        nivel_detalle = "gerencial"

    if (
        st.session_state.get("last_perfil") is not None
        and st.session_state["last_perfil"] != perfil_key
    ):
        depto_actual_ini = st.session_state.bot.ctx.get("departamento_zona", "Matagalpa")
        sup_orig_ini = st.session_state.bot.ctx.get(
            "superficie_original", {"valor": 1.0, "unidad": "manzana"}
        )
        _reiniciar_sesion(
            perfil_key,
            depto_actual_ini,
            float(sup_orig_ini.get("valor", 1.0)),
            sup_orig_ini.get("unidad", "manzana"),
        )
        st.session_state.last_perfil = perfil_key
        st.rerun()

    st.session_state["last_perfil"] = perfil_key
    st.session_state.bot.set_perfil(perfil_key)

    st.write("")
    st.subheader("Datos de la Finca")
    depto_actual = st.session_state.bot.ctx.get("departamento_zona", "Matagalpa")
    idx_default = (
        DEPARTAMENTOS.index(depto_actual) if depto_actual in DEPARTAMENTOS else 11
    )
    depto = st.selectbox("Departamento / Region", DEPARTAMENTOS, index=idx_default)
    st.session_state.bot.set_departamento(depto)
    st.session_state.clima_api.set_departamento(depto)

    sup_orig = st.session_state.bot.ctx.get(
        "superficie_original", {"valor": 1.0, "unidad": "manzana"}
    )
    unidades = ["manzana", "ha", "m2", "acre"]
    uni_actual = sup_orig.get("unidad", "manzana")
    idx_uni = unidades.index(uni_actual) if uni_actual in unidades else 0

    col_sup1, col_sup2 = st.columns([2, 1])
    with col_sup1:
        sup_val = st.number_input(
            "Superficie",
            min_value=0.01,
            max_value=10000.0,
            value=float(sup_orig.get("valor", 1.0)),
            step=0.5,
            key="sup_input",
        )
    with col_sup2:
        sup_uni = st.selectbox(
            "Unidad", unidades, index=idx_uni, key="sup_unidad"
        )
    st.session_state.bot.set_superficie(sup_val, sup_uni)
    st.caption(f"Area equivalente: {st.session_state.bot.ctx['superficie_manzanas']:.4f} mz")

    st.write("")
    st.subheader("Conectividad de Modulos")
    p_info = leer_precios_actuales()
    es_mercado_vivo = bool(p_info.get("es_en_vivo") or p_info.get("cafe_en_vivo"))

    if st.session_state.llm.gemini_client:
        llm_badge = render_status_pill("IA", "En linea", "success")
    elif st.session_state.llm._ollama_ok:
        llm_badge = render_status_pill("IA", "Local (Ollama)", "info")
    else:
        llm_badge = render_status_pill("IA", "Reglas locales", "warning")

    mercado_badge = (
        render_status_pill("Mercado", "En vivo", "success")
        if es_mercado_vivo
        else render_status_pill("Mercado", "Respaldo local", "warning")
    )
    vision_badge = render_status_pill("Vision", "Multimodal activo", "success")

    st.markdown(
        f"<div>{llm_badge}{mercado_badge}{vision_badge}</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    if st.button("Reiniciar sesion", use_container_width=True):
        _reiniciar_sesion(perfil_key, depto, sup_val, sup_uni)
        st.rerun()


# Pestañas de Navegación Principal
tab_nombres = ["Conversacion", "Diagnostico Foliar", "Mercado y Precios", "Herramientas"]
if nivel_detalle in ("tecnico", "gerencial"):
    tab_nombres.append("Historial")
if nivel_detalle == "gerencial":
    tab_nombres.append("Administracion")

tabs = st.tabs(tab_nombres)
tab_chat = tabs[0]
tab_img = tabs[1]
tab_precios = tabs[2]
tab_herramientas = tabs[3]

idx_historial = 4 if len(tab_nombres) > 4 else None
idx_admin = 5 if len(tab_nombres) > 5 else None


# PESTAÑA 1: Conversación y Diagnóstico Guiado
with tab_chat:
    st.subheader("Consulta Agronomica")
    st.caption(
        f"Zona activa: {depto} | Area evaluada: {st.session_state.bot.ctx['superficie_manzanas']:.2f} mz | Perfil: {perfil_key}"
    )

    # Descarga directa de reporte si fue generado
    if st.session_state.reporte_bytes:
        with st.container():
            st.success(f"Reporte tecnico generado: {st.session_state.reporte_nombre}")
            st.download_button(
                label=f"Descargar reporte ({st.session_state.reporte_nombre})",
                data=st.session_state.reporte_bytes,
                file_name=st.session_state.reporte_nombre,
                mime="application/pdf",
                key=f"dl_{st.session_state.reporte_nombre}_{len(st.session_state.chat_historial)}",
                use_container_width=True,
            )

    # Flujo de mensajes
    for rol, texto, intent in st.session_state.chat_historial:
        with st.chat_message("user" if rol == "usuario" else "assistant"):
            st.markdown(texto)
            if rol == "asistente" and nivel_detalle == "tecnico" and intent:
                st.caption(f"Intencion: {intent}")

    # Sugerencias contextuales
    ultimas = st.session_state.get("sugerencias_ultimas", set())
    if st.session_state.chat_historial:
        pool = sugerencias_para_contexto(
            st.session_state.bot.ctx, n=4, excluir_ultimas=ultimas
        )
    else:
        pool = sugerencias_iniciales(nivel_detalle, n=4)

    sugerencias = pool[:4]
    if sugerencias:
        st.session_state["sugerencias_ultimas"] = ultimas.union(set(sugerencias))
        cols = st.columns(len(sugerencias))
        for i, sug in enumerate(sugerencias):
            with cols[i]:
                label = sug if len(sug) <= 32 else sug[:30] + "..."
                if st.button(
                    label,
                    use_container_width=True,
                    key=f"sug_{i}_{len(st.session_state.chat_historial)}",
                ):
                    r, intent = st.session_state.bot.responder(sug)
                    st.session_state.chat_historial.append(("usuario", sug, None))
                    st.session_state.chat_historial.append(("asistente", r, intent))
                    if intent == "Generar_Reporte_PDF":
                        _cargar_reporte_en_sesion(r)
                    st.rerun()

    # Entrada de texto conversacional
    prompt = st.chat_input("Escriba su consulta agronomica...")
    if prompt:
        st.session_state.chat_historial.append(("usuario", prompt, None))
        with st.spinner("Analizando requerimiento..."):
            respuesta, intent = st.session_state.bot.responder(prompt)
        st.session_state.chat_historial.append(("asistente", respuesta, intent))
        if intent == "Generar_Reporte_PDF":
            _cargar_reporte_en_sesion(respuesta)
        st.rerun()


# PESTAÑA 2: Diagnóstico Visual Foliar Dedicado
with tab_img:
    st.subheader("Diagnostico Visual de Hojas")
    st.caption("Cargue una fotografia de campo para clasificar anomalias y sintomas foliares.")

    col_img_in, col_img_out = st.columns([1, 1], gap="medium")

    with col_img_in:
        archivo = st.file_uploader(
            "Seleccione una fotografia (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            key="tab_img_uploader",
        )
        if archivo is not None:
            st.image(archivo, caption="Fotografia analizada", use_container_width=True)

    with col_img_out:
        if archivo is not None:
            os.makedirs("salidas", exist_ok=True)
            nombre_img = f"foliar_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
            ruta = os.path.join("salidas", nombre_img)
            with open(ruta, "wb") as f:
                f.write(archivo.getbuffer())

            try:
                with st.spinner("Ejecutando clasificacion fitopatologica..."):
                    resultado = st.session_state.cnn.clasificar_imagen(
                        ruta,
                        sintoma_textual=st.session_state.bot.ctx.get("sintoma_observado"),
                    )

                st.markdown("#### Resultado del Analisis")
                enfermedad = resultado.get("clase", "No determinada").replace("_", " ")
                confianza = resultado.get("confianza", 0.0)

                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Condicion detectada", enfermedad)
                col_res2.metric("Nivel de confianza", f"{confianza * 100:.1f}%")

                st.progress(float(confianza))

                if resultado.get("justificacion"):
                    st.write(f"**Observaciones:** {resultado['justificacion']}")
                if resultado.get("nota_cruce"):
                    st.info(resultado["nota_cruce"])

                # Registro formal en sesion
                st.session_state.bot.registrar_imagen(
                    ruta,
                    resultado["clase"],
                    resultado["confianza"],
                    nota_cruce=resultado.get("nota_cruce"),
                    modo=resultado.get("modo", "Local"),
                    justificacion=resultado.get("justificacion", ""),
                )

                if st.button(
                    "Vincular hallazgo a la conversacion activa",
                    use_container_width=True,
                ):
                    st.session_state.chat_historial.append(
                        ("usuario", f"[Fotografia adjunta: {archivo.name}]", None)
                    )
                    st.session_state.chat_historial.append(
                        (
                            "asistente",
                            f"Evaluacion de imagen foliar:\n- Clase: {resultado['clase']}\n- Confianza: {confianza*100:.1f}%\n- Detalle: {resultado.get('justificacion', 'Sintomatologia evaluada.')}",
                            "Analizar_Imagen_Hoja",
                        )
                    )
                    st.success("Hallazgo incorporado al hilo conversacional.")

                if nivel_detalle in ("tecnico", "gerencial"):
                    with st.expander("Metadatos tecnicos"):
                        st.json(resultado)

            except Exception as e:
                st.error(f"Error durante el analisis de la muestra: {e}")
        else:
            st.info("Suba una muestra foliar clara con luz adecuada para iniciar la evaluacion.")


# PESTAÑA 3: Mercado y Variables Economicas
with tab_precios:
    st.subheader("Mercado e Insumos Agricolas")
    p = leer_precios_actuales()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Cafe Oro (USD / qq)", f"${p['precio_cafe_oro_qq_usd']:.2f}")
    col_m2.metric("Tipo de Cambio Oficial", f"C$ {p['tipo_cambio_usd_nio']:.2f}")
    col_m3.metric("Jornal Mano de Obra", f"C$ {p['costo_mano_obra_dia_nio']:.0f}")

    st.write("")
    st.markdown("#### Cotizacion de Insumos Principales")
    col_i1, col_i2, col_i3 = st.columns(3)
    col_i1.metric("Urea 46% (C$ / qq)", f"C$ {p['precio_urea_qq_nio']:.2f}")
    col_i2.metric("Cloruro de Potasio KCl", f"C$ {p['precio_kcl_qq_nio']:.2f}")
    col_i3.metric("Fungicida Protector (C$ / L)", f"C$ {p['precio_fungicida_litro_nio']:.2f}")

    st.write("")
    col_btn, col_txt = st.columns([1, 2])
    with col_btn:
        if st.button("Sincronizar cotizaciones en vivo"):
            with st.spinner("Actualizando fuentes de mercado..."):
                nuevos = actualizar_precios()
            st.success(f"Precio actualizado: ${nuevos['precio_cafe_oro_qq_usd']}/qq")
            st.rerun()
    with col_txt:
        st.caption(f"Ultimo registro: {p.get('ultima_actualizacion', 'Hoy')}")


# PESTAÑA 4: Herramientas y Calculadoras Agronomicas
with tab_herramientas:
    st.subheader("Herramientas de Calculo en Campo")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(
        [
            "Analisis de Rentabilidad",
            "Calendario Fenologico",
            "Dosificacion de Nutrientes",
            "Conversion de Unidades",
        ]
    )

    precios_actuales = leer_precios_actuales()

    with sub_tab1:
        st.markdown("##### Evaluacion Economica del Ciclo Productivo")
        col_a, col_b = st.columns(2)
        with col_a:
            r_sup = st.number_input(
                "Superficie del lote (mz)",
                min_value=0.1,
                value=float(st.session_state.bot.ctx["superficie_manzanas"]),
                step=0.5,
                key="r_sup",
            )
            r_rend = st.number_input(
                "Rendimiento proyectado (qq oro / mz)",
                min_value=1.0,
                value=20.0,
                step=0.5,
                key="r_rend",
            )
            r_precio = st.number_input(
                "Precio de venta (USD / qq)",
                min_value=50.0,
                value=float(precios_actuales["precio_cafe_oro_qq_usd"]),
                step=1.0,
                key="r_precio",
            )
        with col_b:
            r_costo = st.number_input(
                "Costos operativos estimados (C$ / mz)",
                min_value=0.0,
                value=15000.0,
                step=500.0,
                key="r_costo",
            )
            r_cambio = st.number_input(
                "Tipo de cambio (C$ / USD)",
                min_value=1.0,
                value=float(precios_actuales["tipo_cambio_usd_nio"]),
                step=0.1,
                key="r_cambio",
            )

        ingreso_qq_nio = r_precio * r_cambio
        ingreso_total = ingreso_qq_nio * r_rend * r_sup
        costo_total = r_costo * r_sup
        beneficio = ingreso_total - costo_total
        margen = (beneficio / ingreso_total * 100) if ingreso_total > 0 else 0
        punto_eq = r_costo / ingreso_qq_nio if ingreso_qq_nio > 0 else 0

        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingreso Bruto Total", f"C$ {ingreso_total:,.0f}")
        c2.metric("Costo Total del Lote", f"C$ {costo_total:,.0f}")
        c3.metric(
            "Margen de Utilidad",
            f"C$ {beneficio:,.0f}",
            delta=f"{margen:.1f}% margen",
        )
        c4.metric(
            "Punto de Equilibrio",
            f"{punto_eq:.1f} qq/mz",
            help="Rendimiento minimo para cubrir la inversion operativa",
        )

    with sub_tab2:
        st.markdown("##### Calendario Fenologico y Labores Recomendadas")
        mes = st.selectbox(
            "Mes de evaluacion:",
            [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            ],
        )

        calendario = {
            "Enero": ("Floracion temprana", ["Aplicar fertilizante foliar (boro + zinc)", "Monitorear roya post-floracion", "Control manual de malezas"]),
            "Febrero": ("Floracion principal", ["Aplicar fungicida preventivo", "Fertilizacion nitrogenada inicial", "Regulacion de sombra"]),
            "Marzo": ("Llenado de grano inicial", ["Fertilizacion potasica complementaria", "Monitoreo preventivo de roya", "Poda sanitaria"]),
            "Abril": ("Llenado de grano activo", ["Riego auxiliar en caso de deficit", "Monitoreo de antracnosis"]),
            "Mayo": ("Maduracion de frutos", ["Mantenimiento preventivo de beneficios humedos", "Suspension de agroquimicos"]),
            "Junio": ("Inicio de cosecha", ["Corte selectivo de frutos maduros", "Registro de quintales recolectados"]),
            "Julio": ("Pico de recoleccion", ["Cosecha continua y control estricto de secado"]),
            "Agosto": ("Cierre de cosecha", ["Limpieza de lotes y preparacion de tejido vegetal"]),
            "Septiembre": ("Poda y recuperacion", ["Poda sanitaria y analisis de fertilidad de suelos"]),
            "Octubre": ("Epoca de precipitacion", ["Monitoreo intensivo de ojo de gallo y roya"]),
            "Noviembre": ("Condiciones de alta humedad", ["Drenajes de agua y manejo de sombra"]),
            "Diciembre": ("Crecimiento vegetativo", ["Formulacion del plan de fertilizacion para el siguiente ciclo"]),
        }

        fase, labores = calendario[mes]
        st.write(f"**Fase:** {fase}")
        for lab in labores:
            st.markdown(f"- {lab}")

    with sub_tab3:
        st.markdown("##### Formulacion Rapida de Fertilizacion")
        f_sup = st.number_input(
            "Superficie a tratar (mz)",
            min_value=0.1,
            value=float(st.session_state.bot.ctx["superficie_manzanas"]),
            step=0.5,
            key="f_sup",
        )
        f_dosis = st.number_input(
            "Dosis recomendada (qq / mz)", min_value=0.1, value=2.0, step=0.5, key="f_dosis"
        )
        f_tipo = st.selectbox(
            "Fertilizante comercial:",
            ["Urea 46% (N)", "18-46-0 (P)", "KCl (K)", "Formula 12-24-12"],
        )

        precios_ref = {
            "Urea 46% (N)": precios_actuales.get("precio_urea_qq_nio", 1650.0),
            "18-46-0 (P)": 1800.0,
            "KCl (K)": precios_actuales.get("precio_kcl_qq_nio", 1400.0),
            "Formula 12-24-12": 1750.0,
        }
        costo_unit = precios_ref.get(f_tipo, 1600.0)
        total_qq = f_sup * f_dosis
        costo_tot = total_qq * costo_unit

        st.write("")
        c_f1, c_f2 = st.columns(2)
        c_f1.metric("Volumen total requerido", f"{total_qq:.2f} qq")
        c_f2.metric("Presupuesto estimado", f"C$ {costo_tot:,.2f}")

    with sub_tab4:
        st.markdown("##### Conversor de Medidas Agrarias")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            sup_in = st.number_input("Manzanas", min_value=0.0, value=1.0, step=0.5, key="conv_mz")
            st.write(f"• {sup_in * 1.4184:.4f} hectareas")
            st.write(f"• {sup_in * 14184:,.0f} m²")
            st.write(f"• {sup_in * 1.7443:.4f} acres")
        with col_c2:
            usd_in = st.number_input("Dolares (USD)", min_value=0.0, value=100.0, step=10.0, key="conv_usd")
            tasa = precios_actuales.get("tipo_cambio_usd_nio", 36.62)
            st.write(f"• **C$ {usd_in * tasa:,.2f}** cordobas (tasa: {tasa:.2f})")

    # Modulo de Retroalimentacion y Evaluacion de Satisfaccion
    st.write("")
    with st.expander("Encuesta de Utilidad del Asistente (CSAT)"):
        if not st.session_state.csat_enviado:
            csat_val = st.slider(
                "Califique el soporte recibido (1=Pobre, 5=Excelente):",
                min_value=1,
                max_value=5,
                value=5,
                key="csat_slider",
            )
            if st.button("Registrar valoracion"):
                registrar_turno(
                    sesion_uuid=st.session_state.bot.sesion_uuid,
                    intent="CSAT_Feedback",
                    entidades={"csat": int(csat_val)},
                    respuesta=f"Calificacion registrada: {csat_val}",
                    tiempo_seg=0.0,
                )
                st.session_state.csat_enviado = True
                st.success(f"Agradecemos su calificacion: {csat_val}/5")
                st.rerun()
        else:
            st.info("Su evaluacion ya fue registrada en esta sesion.")


# PESTAÑA 5: Historial de Consultas
if idx_historial is not None:
    with tabs[idx_historial]:
        st.subheader("Registro de Sesiones Previas")
        hist = consultar_historial(limite=30)
        if hist:
            df = pd.DataFrame(hist)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No se han registrado sesiones previas.")


# PESTAÑA 6: Panel Administrativo
if idx_admin is not None:
    with tabs[idx_admin]:
        st.subheader("Indicadores Operativos del Sistema")
        stats = obtener_stats()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sesiones Totales", stats["total_sesiones"])
        col2.metric("Mensajes Atendidos", stats["total_mensajes"])
        col3.metric("Casos Contingencia", stats["total_fallbacks"])
        col4.metric("Tasa Contingencia", f"{stats['tasa_fallback']*100:.1f}%")

        st.write("")
        st.markdown("#### Desempeño Conversacional")
        kpis = calcular_kpis()
        if "error" not in kpis:
            col_k1, col_k2 = st.columns(2)
            col_k1.json(kpis)
            with col_k2:
                csat_avg = calcular_csat()
                if csat_avg is not None:
                    st.metric("CSAT Promedio", f"{csat_avg:.2f} / 5.0")

        st.write("")
        st.markdown("#### Generacion de Reporte Integral")
        if st.button("Exportar Resumen Consolidado en PDF"):
            bot = st.session_state.bot
            datos = {
                "sesion_id": bot.sesion_uuid,
                "zona": bot.ctx.get("departamento_zona", "Matagalpa"),
                "superficie_manzanas": bot.ctx.get("superficie_manzanas", 1.0),
                "clima": bot.ctx.get("clima", {}),
                "diagnosticos": bot.ctx.get("diagnosticos", []),
                "riesgo": bot.ctx.get("riesgo", {}),
                "optimizacion": bot.ctx.get("optimizacion", {}),
                "imagenes": bot.ctx.get("imagenes_analizadas", []),
            }
            ruta = generar_reporte(datos, nombre=f"admin_{bot.sesion_uuid}.pdf")
            exportar_a_descargas(ruta)
            with open(ruta, "rb") as f:
                st.download_button(
                    label="Descargar PDF generado",
                    data=f.read(),
                    file_name=os.path.basename(ruta),
                    mime="application/pdf",
                    use_container_width=True,
                )

st.caption(
    f"UNA | Sesion: {st.session_state.bot.sesion_uuid} | Departamento: {depto} | Area: {st.session_state.bot.ctx['superficie_manzanas']:.2f} mz | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
