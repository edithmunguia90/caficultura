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
from modulos.ui_theme import (
    aplicar_estilos_tema,
    render_brand_top_row,
    render_hero_greeting,
    render_topbar,
)
from modulos.vision_cnn import ClasificadorVisionCNN

st.set_page_config(
    page_title="Caficultura",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "bot" not in st.session_state:
    st.session_state.bot = ChatbotCaficultura()
    st.session_state.chat_historial = []
    st.session_state.cnn = ClasificadorVisionCNN()
    st.session_state.llm = OraculoAgronomoLLM()
    st.session_state.csat_enviado = False
    st.session_state.last_upload = None
    st.session_state.reporte_bytes = None
    st.session_state.reporte_nombre = None
    st.session_state.clima_api = ModuloClima()
    st.session_state.vista_activa = "Chat"
    st.session_state.modo_claro = False
    st.session_state.sidebar_compact = False
    st.session_state.session_id_count = 0
    st.session_state.scan_res = None
    st.session_state.scan_id = None

aplicar_estilos_tema(
    modo_claro=st.session_state.modo_claro,
    sidebar_compacto=st.session_state.sidebar_compact,
)

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001FA00-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)


def _sin_emojis(texto: str) -> str:
    return _EMOJI_RE.sub("", texto or "").strip()


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
    st.session_state.scan_res = None
    st.session_state.scan_id = None
    st.session_state.session_id_count = st.session_state.get("session_id_count", 0) + 1


def _enviar_consulta(texto: str):
    texto_limpio = _sin_emojis(texto)
    st.session_state.chat_historial.append(("usuario", texto_limpio, None))
    respuesta, intent = st.session_state.bot.responder(texto_limpio)
    st.session_state.chat_historial.append(("asistente", _sin_emojis(respuesta), intent))
    if intent == "Generar_Reporte_PDF":
        _cargar_reporte_en_sesion(respuesta)


def _procesar_entrada_chat(prompt_obj):
    if not prompt_obj:
        return
    texto = (
        prompt_obj.text.strip()
        if hasattr(prompt_obj, "text")
        else (str(prompt_obj).strip() if isinstance(prompt_obj, str) else "")
    )
    archivos = prompt_obj.files if hasattr(prompt_obj, "files") else []

    for arch in archivos:
        os.makedirs("salidas", exist_ok=True)
        nombre_img = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arch.name}"
        ruta_img = os.path.join("salidas", nombre_img)
        with open(ruta_img, "wb") as f:
            f.write(arch.getbuffer())

        with st.spinner("Analizando muestra foliar..."):
            res_img = st.session_state.cnn.clasificar_imagen(
                ruta_img,
                sintoma_textual=st.session_state.bot.ctx.get("sintoma_observado"),
            )

        st.session_state.bot.registrar_imagen(
            ruta_img,
            res_img["clase"],
            res_img["confianza"],
            nota_cruce=res_img.get("nota_cruce"),
            modo=res_img.get("modo", "Local"),
            justificacion=res_img.get("justificacion", ""),
        )

        detalle_txt = (
            f"\n- Detalle: {_sin_emojis(res_img.get('justificacion'))}"
            if res_img.get("justificacion")
            else ""
        )
        st.session_state.chat_historial.append(
            ("usuario", f"[Muestra adjunta: {arch.name}]", None)
        )
        st.session_state.chat_historial.append(
            (
                "asistente",
                f"**Diagnostico foliar:** `{res_img['clase']}` ({res_img['confianza']*100:.1f}%){detalle_txt}",
                "Analizar_Imagen_Hoja",
            )
        )

    if texto:
        _enviar_consulta(texto)


perfil_actual = st.session_state.bot.ctx.get("perfil", "pequeno_productor")
depto_actual = st.session_state.bot.ctx.get("departamento_zona", "Matagalpa")
sup_orig = st.session_state.bot.ctx.get(
    "superficie_original", {"valor": 1.0, "unidad": "manzana"}
)

MAPA_PERFILES = {
    "Productor": ("pequeno_productor", "simple", "P"),
    "Tecnico": ("extensionista_tecnico", "tecnico", "T"),
    "Administrador": ("administrador_finca", "gerencial", "A"),
}
INV_PERFILES = {v[0]: k for k, v in MAPA_PERFILES.items()}
etiqueta_perfil_actual = INV_PERFILES.get(perfil_actual, "Productor")
_, nivel_detalle, inicial_rol = MAPA_PERFILES[etiqueta_perfil_actual]

# ==========================================
# BARRA LATERAL (CONMUTADOR DE RIEL COMPACTO)
# ==========================================
with st.sidebar:
    # Encabezado con conmutador: nunca oculta los iconos, solo oculta los nombres
    col_b_logo, col_b_rail = st.columns([3, 1] if not st.session_state.sidebar_compact else [1, 1])
    with col_b_logo:
        render_brand_top_row(sidebar_compacto=st.session_state.sidebar_compact)
    with col_b_rail:
        icon_toggle = ">>" if st.session_state.sidebar_compact else "<<"
        tooltip_toggle = (
            "Expandir menu (mostrar nombres)"
            if st.session_state.sidebar_compact
            else "Modo compacto (ocultar nombres, mantener iconos)"
        )
        if st.button(
            icon_toggle,
            key="sidebar_toggle_rail",
            help=tooltip_toggle,
            use_container_width=True,
        ):
            st.session_state.sidebar_compact = not st.session_state.sidebar_compact
            st.rerun()

    # Boton de nueva consulta
    txt_new = "" if st.session_state.sidebar_compact else "Nueva consulta"
    if st.button(
        txt_new,
        key="sidebar_new_chat",
        use_container_width=True,
        help="Iniciar nueva consulta",
    ):
        s_orig = st.session_state.bot.ctx.get(
            "superficie_original", {"valor": 1.0, "unidad": "manzana"}
        )
        _reiniciar_sesion(
            perfil_actual,
            depto_actual,
            float(s_orig.get("valor", 1.0)),
            s_orig.get("unidad", "manzana"),
        )
        st.session_state.vista_activa = "Chat"
        st.rerun()

    modulos_nav = [
        "Chat",
        "Escaner",
        "Mercado",
        "Calculadoras",
        "Reportes",
    ]
    if nivel_detalle == "gerencial":
        modulos_nav.append("Metricas")

    if st.session_state.vista_activa not in modulos_nav:
        st.session_state.vista_activa = "Chat"

    for item in modulos_nav:
        es_activo = st.session_state.vista_activa == item
        lbl = "" if st.session_state.sidebar_compact else item
        if st.button(
            lbl,
            key=f"nav_{item}",
            use_container_width=True,
            help=item,
            type="primary" if es_activo else "secondary",
        ):
            st.session_state.vista_activa = item
            st.rerun()

    # Historial reciente (solo visible en modo expandido)
    if not st.session_state.sidebar_compact:
        hist_reciente = consultar_historial(limite=3)
        if hist_reciente:
            st.markdown('<p class="sidebar-section-title">Recientes</p>', unsafe_allow_html=True)
            for idx_h, h in enumerate(hist_reciente):
                txt_msg = _sin_emojis(h.get("mensaje_usuario", "")).strip()
                if txt_msg:
                    etiqueta_corta = (txt_msg[:22] + "...") if len(txt_msg) > 22 else txt_msg
                    if st.button(
                        etiqueta_corta,
                        key=f"recent_{idx_h}",
                        use_container_width=True,
                        help=txt_msg,
                    ):
                        st.session_state.vista_activa = "Chat"
                        _enviar_consulta(txt_msg)
                        st.rerun()

    # Ajustes integrados (sin elementos HTML encimados ni solapamiento)
    st.divider()
    lbl_ajustes = (
        ""
        if st.session_state.sidebar_compact
        else f"{etiqueta_perfil_actual} ({depto_actual})"
    )
    with st.popover(
        lbl_ajustes,
        use_container_width=True,
        help="Configurar finca, perfil y tema",
    ):
        st.markdown("**Ajustes de lote y operacion**")
        opciones_rol = list(MAPA_PERFILES.keys())
        idx_rol = opciones_rol.index(etiqueta_perfil_actual)
        nuevo_rol_label = st.selectbox("Perfil operativo", opciones_rol, index=idx_rol)
        nuevo_perfil_key, _, _ = MAPA_PERFILES[nuevo_rol_label]

        idx_depto = (
            DEPARTAMENTOS.index(depto_actual) if depto_actual in DEPARTAMENTOS else 11
        )
        nuevo_depto = st.selectbox("Departamento", DEPARTAMENTOS, index=idx_depto)

        unidades = ["manzana", "ha", "m2", "acre"]
        uni_actual = sup_orig.get("unidad", "manzana")
        idx_uni = unidades.index(uni_actual) if uni_actual in unidades else 0

        c_s1, c_s2 = st.columns([2, 1])
        with c_s1:
            nuevo_sup_val = st.number_input(
                "Superficie",
                min_value=0.01,
                max_value=10000.0,
                value=float(sup_orig.get("valor", 1.0)),
                step=0.5,
            )
        with c_s2:
            nueva_sup_uni = st.selectbox("Unidad", unidades, index=idx_uni)

        st.session_state.bot.set_departamento(nuevo_depto)
        st.session_state.clima_api.set_departamento(nuevo_depto)
        st.session_state.bot.set_superficie(nuevo_sup_val, nueva_sup_uni)

        if nuevo_perfil_key != perfil_actual:
            _reiniciar_sesion(
                nuevo_perfil_key, nuevo_depto, nuevo_sup_val, nueva_sup_uni
            )
            st.rerun()

        toggle_claro = st.toggle(
            "Tema claro",
            value=st.session_state.modo_claro,
            key="toggle_tema_claro",
        )
        if toggle_claro != st.session_state.modo_claro:
            st.session_state.modo_claro = toggle_claro
            st.rerun()

# Variables activas
depto = st.session_state.bot.ctx.get("departamento_zona", "Matagalpa")
superficie_mz = st.session_state.bot.ctx.get("superficie_manzanas", 1.0)
perfil_key = st.session_state.bot.ctx.get("perfil", "pequeno_productor")
_, nivel_detalle, _ = MAPA_PERFILES[INV_PERFILES.get(perfil_key, "Productor")]

# ==========================================
# CABECERA SUPERIOR
# ==========================================
col_top_title, col_top_actions = st.columns([7, 3])
with col_top_title:
    render_topbar(st.session_state.vista_activa)

with col_top_actions:
    c_a1, c_a2 = st.columns([1, 1])
    with c_a1:
        if st.session_state.reporte_bytes:
            st.download_button(
                label="PDF",
                data=st.session_state.reporte_bytes,
                file_name=st.session_state.reporte_nombre,
                mime="application/pdf",
                use_container_width=True,
            )
    with c_a2:
        if st.button("Nueva sesion", key="top_new_session", use_container_width=True):
            s_orig = st.session_state.bot.ctx.get(
                "superficie_original", {"valor": 1.0, "unidad": "manzana"}
            )
            _reiniciar_sesion(
                perfil_actual,
                depto_actual,
                float(s_orig.get("valor", 1.0)),
                s_orig.get("unidad", "manzana"),
            )
            st.session_state.vista_activa = "Chat"
            st.rerun()

# ==========================================
# VISTA 1: CHAT
# ==========================================
if st.session_state.vista_activa == "Chat":
    if not st.session_state.chat_historial:
        render_hero_greeting(
            nombre_rol=etiqueta_perfil_actual,
            lote_str=f"Lote: {depto} / {superficie_mz:.1f} mz",
        )

        st.markdown('<div class="axiom-composer-container">', unsafe_allow_html=True)
        with st.container():
            prompt_c = st.chat_input(
                "¿En que puedo ayudarte hoy?",
                accept_file=True,
                file_type=["jpg", "jpeg", "png"],
                key=f"chat_in_center_{st.session_state.session_id_count}",
            )
            if prompt_c:
                _procesar_entrada_chat(prompt_c)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="quick-start-label">Sugerencias de inicio</div>', unsafe_allow_html=True)
        st.markdown('<div class="quick-start-grid">', unsafe_allow_html=True)
        c_q1, c_q2 = st.columns(2, gap="medium")
        with c_q1:
            if st.button(
                "**Diagnostico foliar**\nIdentifica sintomas de roya, ojo de gallo o deficiencias",
                key="qs_diag",
                use_container_width=True,
            ):
                _enviar_consulta("Tengo manchas naranjas en hojas")
                st.rerun()
            if st.button(
                "**Plan de fertilizacion**\nFormula requerimientos de Urea, KCl y NPK segun tu lote",
                key="qs_fert",
                use_container_width=True,
            ):
                _enviar_consulta(f"Optimizar fertilizacion para {superficie_mz:g} manzanas")
                st.rerun()
        with c_q2:
            if st.button(
                "**Precios y mercado**\nCotizacion de cafe oro Contrato C y tipo de cambio",
                key="qs_mkt",
                use_container_width=True,
            ):
                _enviar_consulta("¿Cual es el precio actual del cafe?")
                st.rerun()
            if st.button(
                "**Pronostico del clima**\nCondiciones agroclimaticas en tu departamento",
                key="qs_clim",
                use_container_width=True,
            ):
                _enviar_consulta(f"¿Como esta el clima en {depto}?")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown('<div class="chat-flow-container">', unsafe_allow_html=True)
        for rol, texto, intent in st.session_state.chat_historial:
            es_usuario = rol == "usuario"
            with st.chat_message("user" if es_usuario else "assistant"):
                clase_lado = "chat-side-user" if es_usuario else "chat-side-bot"
                etiqueta_rol = "Usuario" if es_usuario else "Asistente"
                st.markdown(
                    f'<div class="{clase_lado}"><span class="chat-role-tag">{etiqueta_rol}</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_sin_emojis(texto))
        st.markdown("</div>", unsafe_allow_html=True)

        prompt_b = st.chat_input(
            "Escribe una consulta o adjunta una muestra...",
            accept_file=True,
            file_type=["jpg", "jpeg", "png"],
            key=f"chat_in_bottom_{st.session_state.session_id_count}",
        )
        if prompt_b:
            _procesar_entrada_chat(prompt_b)
            st.rerun()

# ==========================================
# VISTA 2: ESCANER FOLIAR
# ==========================================
elif st.session_state.vista_activa == "Escaner":
    archivo = st.file_uploader(
        "Subir fotografia de hoja (JPG, PNG)",
        type=["jpg", "jpeg", "png"],
        key="dedicated_img_uploader",
    )

    if archivo is not None:
        archivo_id = f"{archivo.name}_{archivo.size}"
        os.makedirs("salidas", exist_ok=True)
        nombre_img = f"tab_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
        ruta = os.path.join("salidas", nombre_img)

        # Solo clasificar una vez para evitar bucle infinito en "Continuar en el chat"
        if st.session_state.get("scan_id") != archivo_id:
            with open(ruta, "wb") as f:
                f.write(archivo.getbuffer())
            try:
                with st.spinner("Analizando muestra foliar..."):
                    resultado = st.session_state.cnn.clasificar_imagen(
                        ruta,
                        sintoma_textual=st.session_state.bot.ctx.get("sintoma_observado"),
                    )
                st.session_state.scan_res = resultado
                st.session_state.scan_id = archivo_id
                st.session_state.bot.registrar_imagen(
                    ruta,
                    resultado["clase"],
                    resultado["confianza"],
                    nota_cruce=resultado.get("nota_cruce"),
                    modo=resultado.get("modo", "Local"),
                    justificacion=resultado.get("justificacion", ""),
                )
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")
                st.session_state.scan_res = None

        resultado = st.session_state.get("scan_res")
        if resultado:
            enfermedad = resultado.get("clase", "Sana").replace("_", " ")
            confianza = float(resultado.get("confianza", 0.0))

            col_img_in, col_img_out = st.columns([1, 1.2], gap="large")
            with col_img_in:
                st.image(archivo, use_container_width=True)

            with col_img_out:
                st.markdown(
                    f"""
                    <div class="shadcn-card">
                        <div class="shadcn-label">Resultado fitopatologico</div>
                        <div class="shadcn-value">{enfermedad}</div>
                        <div class="shadcn-label" style="margin-top:0.35rem;">Certeza: {confianza * 100:.1f}% | Motor: {resultado.get('modo', 'Local')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if resultado.get("justificacion"):
                    st.caption(_sin_emojis(resultado["justificacion"]))

                if st.button("Continuar en el chat", type="primary", use_container_width=True):
                    st.session_state.chat_historial.append(
                        ("usuario", f"[Fotografia analizada: {archivo.name}]", None)
                    )
                    st.session_state.chat_historial.append(
                        (
                            "asistente",
                            f"Diagnostico visual registrado: **{enfermedad}** ({confianza*100:.1f}% de confianza). {_sin_emojis(resultado.get('justificacion', ''))}",
                            "Analizar_Imagen_Hoja",
                        )
                    )
                    st.session_state.vista_activa = "Chat"
                    st.rerun()

# ==========================================
# VISTA 3: MERCADO E INSUMOS
# ==========================================
elif st.session_state.vista_activa == "Mercado":
    p = leer_precios_actuales()
    precio_usd = float(p["precio_cafe_oro_qq_usd"])
    tasa_nio = float(p["tipo_cambio_usd_nio"])
    precio_qq_nio = precio_usd * tasa_nio
    urea_nio = float(p["precio_urea_qq_nio"])
    kcl_nio = float(p["precio_kcl_qq_nio"])
    fung_nio = float(p["precio_fungicida_litro_nio"])
    jornal_nio = float(p["costo_mano_obra_dia_nio"])

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Cafe Oro Contrato C", f"${precio_usd:.2f} USD/qq")
    c_m2.metric("Liquidacion Local", f"C$ {precio_qq_nio:,.0f} / qq")
    c_m3.metric("Tipo de Cambio BCN", f"C$ {tasa_nio:.2f} / USD")

    st.markdown(
        f"""
        <div class="shadcn-card" style="margin-top:0.75rem;">
            <div class="shadcn-label">Costos de insumos y mano de obra</div>
            <table class="shadcn-table">
                <thead>
                    <tr>
                        <th>Insumo o labor</th>
                        <th class="num">Costo C$</th>
                        <th class="num">Costo USD</th>
                        <th class="num">Relacion por 1 qq cafe</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Urea 46% (qq)</td>
                        <td class="num">C$ {urea_nio:,.2f}</td>
                        <td class="num">${urea_nio / tasa_nio:.2f}</td>
                        <td class="num">{precio_qq_nio / urea_nio:.2f} qq</td>
                    </tr>
                    <tr>
                        <td>Cloruro de Potasio KCl (qq)</td>
                        <td class="num">C$ {kcl_nio:,.2f}</td>
                        <td class="num">${kcl_nio / tasa_nio:.2f}</td>
                        <td class="num">{precio_qq_nio / kcl_nio:.2f} qq</td>
                    </tr>
                    <tr>
                        <td>Fungicida Sistemico (L)</td>
                        <td class="num">C$ {fung_nio:,.2f}</td>
                        <td class="num">${fung_nio / tasa_nio:.2f}</td>
                        <td class="num">{precio_qq_nio / fung_nio:.1f} L</td>
                    </tr>
                    <tr>
                        <td>Jornal diario de campo</td>
                        <td class="num">C$ {jornal_nio:,.2f}</td>
                        <td class="num">${jornal_nio / tasa_nio:.2f}</td>
                        <td class="num">{precio_qq_nio / jornal_nio:.1f} jornales</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Actualizar cotizaciones en vivo"):
        with st.spinner("Sincronizando precios..."):
            actualizar_precios()
        st.rerun()

# ==========================================
# VISTA 4: CALCULADORAS
# ==========================================
elif st.session_state.vista_activa == "Calculadoras":
    precios_actuales = leer_precios_actuales()

    herramienta = st.radio(
        "Herramienta",
        ["Rentabilidad", "Fertilizante", "Calendario", "Conversor"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if herramienta == "Rentabilidad":
        col_calc_in, col_calc_out = st.columns([1, 1.25], gap="large")
        with col_calc_in:
            r_sup = st.number_input(
                "Superficie (mz)", min_value=0.1, value=float(superficie_mz), step=0.5
            )
            r_rend = st.number_input(
                "Rendimiento esperado (qq/mz)", min_value=1.0, value=20.0, step=0.5
            )
            r_precio = st.number_input(
                "Precio venta (USD/qq)",
                min_value=50.0,
                value=float(precios_actuales["precio_cafe_oro_qq_usd"]),
                step=1.0,
            )
            r_costo = st.number_input(
                "Costo por manzana (C$/mz)", min_value=0.0, value=15000.0, step=500.0
            )

        with col_calc_out:
            r_cambio = float(precios_actuales["tipo_cambio_usd_nio"])
            ingreso_qq_nio = r_precio * r_cambio
            ingreso_total = ingreso_qq_nio * r_rend * r_sup
            costo_total = r_costo * r_sup
            beneficio = ingreso_total - costo_total
            punto_eq = r_costo / ingreso_qq_nio if ingreso_qq_nio > 0 else 0.0

            st.markdown(
                f"""
                <div class="shadcn-card">
                    <div class="shadcn-label">Utilidad neta estimada ({r_sup:.1f} mz)</div>
                    <div class="shadcn-value">C$ {beneficio:,.0f}</div>
                    <table class="shadcn-table">
                        <tbody>
                            <tr><td>Ingreso total bruto</td><td class="num">C$ {ingreso_total:,.0f}</td></tr>
                            <tr><td>Costo operativo total</td><td class="num">C$ {costo_total:,.0f}</td></tr>
                            <tr><td>Punto de equilibrio</td><td class="num">{punto_eq:.1f} qq/mz</td></tr>
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif herramienta == "Fertilizante":
        col_f_in, col_f_out = st.columns([1, 1.25], gap="large")
        with col_f_in:
            f_sup = st.number_input(
                "Area (mz)", min_value=0.1, value=float(superficie_mz), step=0.5
            )
            f_dosis = st.number_input(
                "Dosis (qq/mz)", min_value=0.1, value=2.0, step=0.5
            )
            f_tipo = st.selectbox(
                "Insumo",
                [
                    "Urea 46% (N)",
                    "18-46-0 (DAP)",
                    "Cloruro de Potasio KCl",
                    "Formula 12-24-12",
                ],
            )
            precios_ref = {
                "Urea 46% (N)": precios_actuales.get("precio_urea_qq_nio", 1650.0),
                "18-46-0 (DAP)": 1800.0,
                "Cloruro de Potasio KCl": precios_actuales.get(
                    "precio_kcl_qq_nio", 1400.0
                ),
                "Formula 12-24-12": 1750.0,
            }
            precio_edit = st.number_input(
                "Precio (C$/qq)",
                min_value=1.0,
                value=float(precios_ref[f_tipo]),
                step=25.0,
            )

        with col_f_out:
            total_qq = f_sup * f_dosis
            costo_tot = total_qq * precio_edit
            gramos_planta = (f_dosis * 45359.2) / 3500.0

            st.markdown(
                f"""
                <div class="shadcn-card">
                    <div class="shadcn-label">Presupuesto estimado de aplicacion</div>
                    <div class="shadcn-value">C$ {costo_tot:,.0f}</div>
                    <table class="shadcn-table">
                        <tbody>
                            <tr><td>Volumen de compra requerido</td><td class="num">{total_qq:.1f} qq</td></tr>
                            <tr><td>Dosis por planta (3,500 pl/mz)</td><td class="num">{gramos_planta:.0f} g / planta</td></tr>
                            <tr><td>Costo por manzana</td><td class="num">C$ {costo_tot / f_sup:,.0f} / mz</td></tr>
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif herramienta == "Calendario":
        mes = st.selectbox(
            "Mes del ciclo",
            [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            ],
        )
        calendario = {
            "Enero": ("Floracion temprana", ["Aplicacion foliar de boro y zinc", "Monitoreo de focos de roya"]),
            "Febrero": ("Floracion principal", ["Regulacion de sombra (40%-45%)", "Muestreo preventivo de broca"]),
            "Marzo": ("Llenado inicial", ["Primera fraccion NPK y enmiendas", "Colocacion de trampas"]),
            "Abril": ("Desarrollo de fruto", ["Fertilizacion nitrogenada", "Control preventivo de mancha de hierro"]),
            "Mayo": ("Llenado activo", ["Aplicacion potasica (KCl)", "Vigilancia de ojo de gallo"]),
            "Junio": ("Consistencia de endospermo", ["Inspeccion fitosanitaria", "Mantenimiento de drenajes"]),
            "Julio": ("Maduracion temprana", ["Deshije selectivo", "Regulacion de ventilacion"]),
            "Agosto": ("Pre-cosecha", ["Mantenimiento de beneficio humedo", "Suspension de fungicidas"]),
            "Septiembre": ("Inicio de recoleccion", ["Graniteo selectivo sanitario", "Monitoreo de humedad"]),
            "Octubre": ("Cosecha media", ["Recoleccion de cereza madura", "Control de fermentacion"]),
            "Noviembre": ("Cosecha plena", ["Recoleccion continua", "Secado de pergamino al 11%-12%"]),
            "Diciembre": ("Cierre de cosecha", ["Pepena y repela sanitaria", "Muestreo de suelo"]),
        }
        fase, labores = calendario[mes]
        filas = "".join(f"<tr><td>{lab}</td></tr>" for lab in labores)
        st.markdown(
            f"""
            <div class="shadcn-card">
                <div class="shadcn-label">Mes de {mes}</div>
                <div class="shadcn-value" style="font-size:1.15rem;">{fase}</div>
                <table class="shadcn-table"><tbody>{filas}</tbody></table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif herramienta == "Conversor":
        c_u1, c_u2 = st.columns(2, gap="large")
        with c_u1:
            sup_in = st.number_input("Manzanas (mz)", min_value=0.0, value=float(superficie_mz), step=0.5)
            qq_in = st.number_input("Quintales (qq)", min_value=0.0, value=10.0, step=1.0)
        with c_u2:
            st.markdown(
                f"""
                <div class="shadcn-card">
                    <table class="shadcn-table">
                        <tbody>
                            <tr><td>{sup_in:.1f} mz</td><td class="num">{sup_in * 0.7026:.2f} ha / {sup_in * 1.736:.2f} acres</td></tr>
                            <tr><td>{qq_in:.1f} qq</td><td class="num">{qq_in * 45.36:.1f} kg / {qq_in * 100:.0f} lb</td></tr>
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==========================================
# VISTA 5: REPORTES
# ==========================================
elif st.session_state.vista_activa == "Reportes":
    bot = st.session_state.bot
    col_r1, col_r2 = st.columns([1, 1.6], gap="large")

    with col_r1:
        n_diag = len(bot.ctx.get("diagnosticos", []))
        n_img = len(bot.ctx.get("imagenes_analizadas", []))
        st.markdown(
            f"""
            <div class="shadcn-card">
                <div class="shadcn-label">Expediente de la sesion</div>
                <div class="shadcn-value" style="font-size:1.2rem;">{depto} ({superficie_mz:.1f} mz)</div>
                <table class="shadcn-table">
                    <tbody>
                        <tr><td>Diagnosticos registrados</td><td class="num">{n_diag}</td></tr>
                        <tr><td>Muestras foliares</td><td class="num">{n_img}</td></tr>
                    </tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Generar Reporte PDF", type="primary", use_container_width=True):
            datos_pdf = {
                "sesion_id": bot.sesion_uuid,
                "zona": depto,
                "superficie_manzanas": superficie_mz,
                "clima": bot.ctx.get("clima", {}),
                "diagnosticos": bot.ctx.get("diagnosticos", []),
                "riesgo": bot.ctx.get("riesgo", {}),
                "optimizacion": bot.ctx.get("optimizacion", {}),
                "imagenes": bot.ctx.get("imagenes_analizadas", []),
            }
            ruta_pdf = generar_reporte(
                datos_pdf, nombre=f"reporte_{bot.sesion_uuid}.pdf"
            )
            exportar_a_descargas(ruta_pdf)
            with open(ruta_pdf, "rb") as f:
                st.session_state.reporte_bytes = f.read()
            st.session_state.reporte_nombre = os.path.basename(ruta_pdf)
            st.rerun()

        if st.session_state.reporte_bytes:
            st.download_button(
                label="Descargar PDF",
                data=st.session_state.reporte_bytes,
                file_name=st.session_state.reporte_nombre,
                mime="application/pdf",
                use_container_width=True,
            )

    with col_r2:
        st.markdown("##### Historial de interacciones")
        hist = consultar_historial(limite=15)
        if hist:
            df = pd.DataFrame(hist)
            cols_map = {
                "timestamp": "Fecha",
                "intent": "Intencion",
                "mensaje_usuario": "Consulta",
            }
            cols_disp = [c for c in cols_map if c in df.columns]
            st.dataframe(
                df[cols_disp].rename(columns=cols_map),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Sin registros previos en la base de datos local.")

# ==========================================
# VISTA 6: METRICAS
# ==========================================
elif st.session_state.vista_activa == "Metricas":
    stats = obtener_stats()
    csat_avg = calcular_csat()
    c_a1, c_a2, c_a3 = st.columns(3)
    c_a1.metric("Sesiones Totales", stats["total_sesiones"])
    c_a2.metric("Mensajes Procesados", stats["total_mensajes"])
    c_a3.metric("Satisfaccion CSAT", f"{csat_avg:.1f} / 5.0" if csat_avg is not None else "-")
