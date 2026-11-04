"""
modulos/ui_theme.py
Sistema de diseno inspirado en la arquitectura Axiom/shadcn:
- Riel lateral conmutador (modo expandido con nombres o modo compacto con solo iconos).
- Los iconos NUNCA se ocultan; se ocultan unicamente los nombres de los modulos.
- Oculta el boton nativo que colapsaba el sidebar a 0px.
- Eliminacion de solapamientos entre perfil y ajustes.
- Correccion de foco en la barra de chat (sin recuadros internos).
- Entrada fluida y layout alternado de conversacion.
"""
import urllib.parse
from datetime import datetime
import streamlit as st

MDI_PATHS = {
    "brand": "M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z",
    "plus": "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
    "Chat": "M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H5.17L4,17.17V4H20V16M6,9H18V11H6V9M6,12H14V14H6V12M6,6H18V8H6V6Z",
    "Escaner": "M5,15H3V19A2,2 0 0,0 5,21H9V19H5M5,5H9V3H5A2,2 0 0,0 3,5V9H5M19,3H15V5H19V9H21V5A2,2 0 0,0 19,3M19,19H15V21H19A2,2 0 0,0 21,19V15H19M12,8A4,4 0 0,0 8,12A4,4 0 0,0 12,16A4,4 0 0,0 16,12A4,4 0 0,0 12,8M12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14Z",
    "Mercado": "M16,11.78L20.24,4.45L21.97,5.45L16.74,14.5L10.23,10.75L5.46,19H22V21H2V3H4V17.54L9.5,8L16,11.78Z",
    "Calculadoras": "M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19M6.2,7.7H11.2V9.2H6.2V7.7M13,15.8H18V17.3H13V15.8M13,13.2H18V14.7H13V13.2M8,18H9.5V16H11.5V14.5H9.5V12.5H8V14.5H6V16H8V18M14.1,10.9L15.5,9.5L16.9,10.9L18,9.8L16.6,8.4L18,7L16.9,5.9L15.5,7.3L14.1,5.9L13,7L14.4,8.4L13,9.8L14.1,10.9Z",
    "Reportes": "M6,2A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2H6M6,4H13V9H18V20H6V4M8,12V14H16V12H8M8,16V18H13V16H8Z",
    "Metricas": "M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19M9,17H7V10H9V17M13,17H11V7H13V17M17,17H15V13H17V17Z",
    "ajustes": "M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",
    "leaf": "M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z",
    "sprout": "M2,22V20C2,15.58 5.58,12 10,12C10.68,12 11.35,12.09 12,12.25V7.41C10.74,7.76 9.61,8.44 8.7,9.35L7.29,7.94C8.59,6.64 10.22,5.71 12,5.28V2H14V5.28C15.78,5.71 17.41,6.64 18.71,7.94L17.3,9.35C16.39,8.44 15.26,7.76 14,7.41V12.25C14.65,12.09 15.32,12 16,12C20.42,12 24,15.58 24,20V22H2M12,14.33C11.36,14.12 10.69,14 10,14C6.69,14 4,16.69 4,20H20C20,16.69 17.31,14 14,14C13.31,14 12.64,14.12 12,14.33Z",
    "cash": "M3,6H21V18H3V6M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9M7,8A2,2 0 0,1 5,10V14A2,2 0 0,1 7,16H17A2,2 0 0,1 19,14V10A2,2 0 0,1 17,8H7Z",
    "cloud": "M19.35,10.04C18.67,6.59 15.64,4 12,4C9.11,4 6.6,5.64 5.35,8.04C2.34,8.36 0,10.91 0,14A6,6 0 0,0 6,20H19A5,5 0 0,0 24,15C24,12.36 21.95,10.22 19.35,10.04Z",
    "history": "M13,3A9,9 0 0,0 4,12H1L4.89,15.89L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.38,18.22 8.16,16.96L6.74,18.38C8.36,20 10.56,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3M12,8V13L16.28,15.54L17,14.33L13.5,12.25V8H12Z",
    "menu": "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z",
    "rail_collapse": "M15.41,16.59L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.59Z",
    "rail_expand": "M8.59,16.59L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.59Z",
}


def _mdi_data_uri(name: str) -> str:
    path = MDI_PATHS.get(name, MDI_PATHS["Chat"])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="black" d="{path}"/></svg>'
    return f"url(\"data:image/svg+xml,{urllib.parse.quote(svg)}\")"


def mdi_svg_inline(name: str, size: int = 16) -> str:
    path = MDI_PATHS.get(name, MDI_PATHS["Chat"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="currentColor" aria-hidden="true" style="flex-shrink:0;">'
        f'<path d="{path}"/></svg>'
    )


def aplicar_estilos_tema(modo_claro: bool = False, sidebar_compacto: bool = False):
    """Inyecta CSS con soporte para modo oscuro/claro y riel compacto."""
    if modo_claro:
        tokens = """
        --background: #fbfbfa;
        --foreground: #18181b;
        --card: #ffffff;
        --card-foreground: #18181b;
        --user-bubble: #f4f4f5;
        --bot-bubble: #ffffff;
        --sidebar: #f5f4f0;
        --muted: #f4f4f5;
        --muted-active: #e4e4e7;
        --muted-foreground: #71717a;
        --border: #e4e4e7;
        --border-strong: #a1a1aa;
        --primary: #18181b;
        --primary-foreground: #fafafa;
        --primary-hover: #27272a;
        --ring: #18181b;
        """
    else:
        tokens = """
        --background: #09090b;
        --foreground: #fafafa;
        --card: #121215;
        --card-foreground: #fafafa;
        --user-bubble: #18181b;
        --bot-bubble: #121215;
        --sidebar: #09090b;
        --muted: #18181b;
        --muted-active: #27272a;
        --muted-foreground: #a1a1aa;
        --border: #27272a;
        --border-strong: #52525b;
        --primary: #fafafa;
        --primary-foreground: #09090b;
        --primary-hover: #e4e4e7;
        --ring: #d4d4d8;
        """

    icon_plus = _mdi_data_uri("plus")
    icon_chat = _mdi_data_uri("Chat")
    icon_scan = _mdi_data_uri("Escaner")
    icon_mkt = _mdi_data_uri("Mercado")
    icon_calc = _mdi_data_uri("Calculadoras")
    icon_rep = _mdi_data_uri("Reportes")
    icon_met = _mdi_data_uri("Metricas")
    icon_adj = _mdi_data_uri("ajustes")
    icon_leaf = _mdi_data_uri("leaf")
    icon_sprout = _mdi_data_uri("sprout")
    icon_cash = _mdi_data_uri("cash")
    icon_cloud = _mdi_data_uri("cloud")
    icon_hist = _mdi_data_uri("history")
    icon_menu = _mdi_data_uri("menu")

    # Reglas específicas según si el sidebar está en modo riel compacto o completo
    if sidebar_compacto:
        compact_css = """
        /* MODO RIEL COMPACTO: Ancho optimizado (88px) y centrado exacto sin desbordamiento */
        section.stSidebar,
        .stSidebar,
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"][data-collapsed="true"],
        section[data-testid="stSidebar"][data-collapsed="false"],
        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: 88px !important;
            min-width: 88px !important;
            max-width: 88px !important;
            transform: none !important;
            margin-left: 0 !important;
            left: 0 !important;
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            flex-shrink: 0 !important;
            overflow-x: hidden !important;
            box-sizing: border-box !important;
        }

        /* Ocultar scrollbars que en Windows provocan recorte en el lado derecho */
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebar"] .block-container {
            overflow-x: hidden !important;
            scrollbar-width: none !important;
            -ms-overflow-style: none !important;
        }
        [data-testid="stSidebar"]::-webkit-scrollbar,
        [data-testid="stSidebarContent"]::-webkit-scrollbar,
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar,
        [data-testid="stSidebar"] .block-container::-webkit-scrollbar {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding: 0.85rem 0.25rem !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.45rem !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            width: 100% !important;
        }

        .axiom-brand,
        .axiom-brand span,
        .sidebar-section-title,
        [class*="st-key-recent_"],
        .st-key-sidebar_new_chat button div,
        .st-key-sidebar_new_chat button p,
        [data-testid="stSidebar"] [class*="st-key-nav_"] button div,
        [data-testid="stSidebar"] [class*="st-key-nav_"] button p,
        [data-testid="stSidebar"] [data-testid="stPopover"] > button div,
        [data-testid="stSidebar"] [data-testid="stPopover"] > button p,
        [data-testid="stSidebar"] [data-testid="stPopover"] > button span {
            display: none !important;
        }

        /* Contenedores de botones centrados */
        [data-testid="stSidebar"] .stButton,
        [data-testid="stSidebar"] [data-testid="stPopover"] {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0 auto !important;
        }

        /* Iconos de 48x48px centrados con espacio seguro a ambos lados */
        .st-key-sidebar_toggle_rail button,
        .st-key-sidebar_new_chat button,
        [data-testid="stSidebar"] [class*="st-key-nav_"] button,
        [data-testid="stSidebar"] [data-testid="stPopover"] > button {
            width: 48px !important;
            min-width: 48px !important;
            max-width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            padding: 0 !important;
            margin: 0 auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 0.5rem !important;
            box-sizing: border-box !important;
            text-align: center !important;
        }

        /* Boton toggle hamburguesa en modo compacto */
        .st-key-sidebar_toggle_rail button {
            background-color: var(--muted) !important;
            border: 1px solid var(--border) !important;
            color: var(--foreground) !important;
            margin-bottom: 0.35rem !important;
        }
        .st-key-sidebar_toggle_rail button:hover {
            background-color: var(--muted-active) !important;
            border-color: var(--border-strong) !important;
            transform: scale(1.05) !important;
        }
        .st-key-sidebar_toggle_rail button::before {
            width: 26px !important;
            height: 26px !important;
        }

        /* Boton Nueva Consulta (+) */
        .st-key-sidebar_new_chat button {
            background-color: var(--muted) !important;
            border: 1px solid var(--border) !important;
            margin-bottom: 0.35rem !important;
        }
        .st-key-sidebar_new_chat button:hover {
            background-color: var(--muted-active) !important;
            border-color: var(--border-strong) !important;
            transform: scale(1.05) !important;
        }
        .st-key-sidebar_new_chat button::before {
            width: 26px !important;
            height: 26px !important;
        }

        /* Botones de Navegación en riel */
        [data-testid="stSidebar"] [class*="st-key-nav_"] button {
            background-color: transparent !important;
            border: 1px solid transparent !important;
        }
        [data-testid="stSidebar"] [class*="st-key-nav_"] button::before {
            width: 26px !important;
            height: 26px !important;
        }
        [data-testid="stSidebar"] [class*="st-key-nav_"] button:hover {
            transform: none !important;
            background-color: var(--muted) !important;
            color: var(--foreground) !important;
        }
        [data-testid="stSidebar"] [class*="st-key-nav_"] button[kind="primary"] {
            background-color: var(--muted-active) !important;
            border: 1px solid var(--border-strong) !important;
            color: var(--foreground) !important;
        }

        /* Boton de Ajustes Popover */
        [data-testid="stSidebar"] [data-testid="stPopover"] > button {
            background-color: var(--muted) !important;
            border: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] [data-testid="stPopover"] > button::before {
            width: 24px !important;
            height: 24px !important;
        }

        /* Separador centrado */
        [data-testid="stSidebar"] hr {
            width: 48px !important;
            margin: 0.35rem auto !important;
            border-color: var(--border) !important;
        }
        """
    else:
        compact_css = """
        section.stSidebar,
        .stSidebar,
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"][data-collapsed="true"],
        section[data-testid="stSidebar"][data-collapsed="false"],
        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: 290px !important;
            min-width: 290px !important;
            max-width: 290px !important;
            transform: none !important;
            margin-left: 0 !important;
            left: 0 !important;
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            flex-shrink: 0 !important;
        }
        """

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        {tokens}
        --radius: 0.5rem;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
    }}

    @keyframes shadcnFadeUp {{
        from {{
            opacity: 0;
            transform: translate3d(0, 8px, 0);
        }}
        to {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    @keyframes chatSlideLeft {{
        from {{
            opacity: 0;
            transform: translate3d(-14px, 4px, 0);
        }}
        to {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    @keyframes chatSlideRight {{
        from {{
            opacity: 0;
            transform: translate3d(14px, 4px, 0);
        }}
        to {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    html, body, .stApp {{
        background-color: var(--background) !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        -webkit-font-smoothing: antialiased;
    }}

    header[data-testid="stHeader"] {{
        background-color: transparent !important;
        border-bottom: none !important;
    }}
    .stDeployButton, [data-testid="stDeployButton"], [data-testid="stToolbar"], #MainMenu, footer {{
        display: none !important;
    }}

    /* Sidebar permanente */
    section.stSidebar,
    .stSidebar,
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"][data-collapsed="true"],
    section[data-testid="stSidebar"][data-collapsed="false"],
    section[data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="true"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: none !important;
        margin-left: 0 !important;
        left: 0 !important;
        position: relative !important;
        flex-shrink: 0 !important;
        box-shadow: none !important;
        background-color: var(--sidebar) !important;
        border-right: 1px solid var(--border) !important;
        transition: width 0.2s var(--ease-out-expo) !important;
    }}

    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: none !important;
        width: 100% !important;
    }}

    /* Ocultar botones nativos y manejador de redimensionamiento que puedan colapsar el sidebar a 0px */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarResizeHandle"] {{
        display: none !important;
    }}

    /* Columnas internas dentro del sidebar sin overflow ni anchos minimos excesivos */
    [data-testid="stSidebar"] [data-testid="column"] {{
        min-width: 0 !important;
    }}

    /* El area principal ocupa fluidamente el resto de la pantalla */
    [data-testid="stMain"],
    section.main {{
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }}

    /* Contenedor principal con max-width amplio y responsive */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2.25rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1220px !important;
        width: 100% !important;
    }}

    [data-testid="stSidebar"] .block-container {{
        padding: 1.25rem 1rem !important;
        max-width: 100% !important;
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        gap: 0.35rem !important;
    }}

    .axiom-brand {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--foreground);
    }}

    /* Fila superior de la marca con boton conmutador de riel (<< / >>) */
    .brand-top-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.2rem 0.4rem 0.75rem 0.4rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }}

    /* Boton hamburguesa para alternar riel/menu lateral */
    .st-key-sidebar_toggle_rail button {{
        background-color: transparent !important;
        color: var(--muted-foreground) !important;
        border: 1px solid transparent !important;
        border-radius: 0.375rem !important;
        min-height: 36px !important;
        width: 36px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: background-color 0.15s ease, color 0.15s ease, transform 0.15s ease !important;
        cursor: pointer !important;
    }}
    .st-key-sidebar_toggle_rail button::before {{
        content: "";
        display: inline-block;
        width: 24px;
        height: 24px;
        flex-shrink: 0;
        background-color: currentColor;
        -webkit-mask-image: {icon_menu};
        mask-image: {icon_menu};
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
    }}
    .st-key-sidebar_toggle_rail button div,
    .st-key-sidebar_toggle_rail button p,
    .st-key-sidebar_toggle_rail button span {{
        display: none !important;
    }}
    .st-key-sidebar_toggle_rail button:hover {{
        background-color: var(--muted) !important;
        color: var(--foreground) !important;
        transform: scale(1.05) !important;
    }}

    /* Boton superior 'Nueva consulta' en sidebar */
    .st-key-sidebar_new_chat button {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.75rem !important;
        background-color: var(--muted) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0.45rem !important;
        min-height: 44px !important;
        padding: 0.55rem 0.95rem !important;
        font-size: 0.96rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.55rem !important;
        transition: all 0.15s var(--ease-out-expo) !important;
    }}
    .st-key-sidebar_new_chat button::before {{
        content: "";
        display: inline-block;
        width: 24px;
        height: 24px;
        flex-shrink: 0;
        background-color: currentColor;
        -webkit-mask-image: {icon_plus};
        mask-image: {icon_plus};
        -webkit-mask-size: contain;
        mask-size: contain;
    }}
    .st-key-sidebar_new_chat button:hover {{
        background-color: var(--muted-active) !important;
        border-color: var(--border-strong) !important;
    }}
    .st-key-sidebar_new_chat button * {{
        color: var(--foreground) !important;
    }}

    /* Modulos del Sidebar con iconos MDI alineados a la izquierda */
    [data-testid="stSidebar"] [class*="st-key-nav_"] button {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        gap: 0.95rem !important;
        background-color: transparent !important;
        color: var(--muted-foreground) !important;
        border: 1px solid transparent !important;
        border-radius: 0.45rem !important;
        min-height: 44px !important;
        padding: 0.55rem 0.95rem !important;
        font-size: 0.98rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        cursor: pointer !important;
        transition: background-color 0.16s var(--ease-out-expo), color 0.16s var(--ease-out-expo), transform 0.16s var(--ease-out-expo) !important;
    }}
    [data-testid="stSidebar"] [class*="st-key-nav_"] button > div {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        margin: 0 !important;
    }}
    [data-testid="stSidebar"] [class*="st-key-nav_"] button:hover {{
        background-color: var(--muted) !important;
        color: var(--foreground) !important;
        transform: translateX(3px) !important;
    }}
    [data-testid="stSidebar"] [class*="st-key-nav_"] button[kind="primary"] {{
        background-color: var(--muted-active) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border-strong) !important;
        font-weight: 600 !important;
    }}

    /* Iconos MDI en la navegacion lateral */
    [data-testid="stSidebar"] [class*="st-key-nav_"] button::before {{
        content: "";
        display: inline-block;
        width: 26px;
        height: 26px;
        flex-shrink: 0;
        background-color: currentColor;
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
    }}
    .st-key-nav_Chat button::before {{ -webkit-mask-image: {icon_chat}; mask-image: {icon_chat}; }}
    .st-key-nav_Escaner button::before {{ -webkit-mask-image: {icon_scan}; mask-image: {icon_scan}; }}
    .st-key-nav_Mercado button::before {{ -webkit-mask-image: {icon_mkt}; mask-image: {icon_mkt}; }}
    .st-key-nav_Calculadoras button::before {{ -webkit-mask-image: {icon_calc}; mask-image: {icon_calc}; }}
    .st-key-nav_Reportes button::before {{ -webkit-mask-image: {icon_rep}; mask-image: {icon_rep}; }}
    .st-key-nav_Metricas button::before {{ -webkit-mask-image: {icon_met}; mask-image: {icon_met}; }}

    /* Seccion RECENTS en Sidebar */
    .sidebar-section-title {{
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted-foreground);
        padding: 1.1rem 0.65rem 0.35rem 0.65rem;
        margin: 0;
    }}
    [class*="st-key-recent_"] button {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        gap: 0.65rem !important;
        background-color: transparent !important;
        color: var(--muted-foreground) !important;
        border: 1px solid transparent !important;
        border-radius: 0.375rem !important;
        min-height: 34px !important;
        padding: 0.3rem 0.65rem !important;
        font-size: 0.86rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: all 0.15s ease !important;
    }}
    [class*="st-key-recent_"] button::before {{
        content: "";
        display: inline-block;
        width: 17px;
        height: 17px;
        flex-shrink: 0;
        background-color: currentColor;
        -webkit-mask-image: {icon_hist};
        mask-image: {icon_hist};
        -webkit-mask-size: contain;
        mask-size: contain;
    }}
    [class*="st-key-recent_"] button:hover {{
        background-color: var(--muted) !important;
        color: var(--foreground) !important;
    }}

    /* Boton popover Ajustes en sidebar (limpio, sin colisiones) */
    [data-testid="stSidebar"] [data-testid="stPopover"] > button {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.65rem !important;
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        min-height: 42px !important;
        padding: 0.5rem 0.85rem !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: var(--foreground) !important;
        box-shadow: none !important;
        border-radius: 0.45rem !important;
        margin-top: 0.65rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stPopover"] > button::before {{
        content: "";
        display: inline-block;
        width: 19px;
        height: 19px;
        flex-shrink: 0;
        background-color: currentColor;
        -webkit-mask-image: {icon_adj};
        mask-image: {icon_adj};
        -webkit-mask-size: contain;
        mask-size: contain;
    }}
    [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {{
        background-color: var(--muted) !important;
        border-color: var(--border-strong) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stPopover"] > button * {{
        color: var(--foreground) !important;
    }}

    /* Cabecera superior minimalista */
    .axiom-topbar {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--foreground);
    }}
    .axiom-topbar-tag {{
        font-size: 0.75rem;
        color: var(--muted-foreground);
        background-color: var(--muted);
        border: 1px solid var(--border);
        border-radius: 9999px;
        padding: 0.15rem 0.55rem;
        font-family: var(--font-mono);
    }}

    /* Estado inicial hero */
    .axiom-hero-wrap {{
        max-width: 680px;
        margin: 2.25rem auto 1.25rem auto;
        text-align: center;
        animation: shadcnFadeUp 0.35s var(--ease-out-expo) both;
    }}
    .axiom-hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.76rem;
        color: var(--muted-foreground);
        background-color: var(--muted);
        border: 1px solid var(--border);
        border-radius: 9999px;
        padding: 0.2rem 0.65rem;
        margin-bottom: 0.75rem;
        font-family: var(--font-mono);
    }}
    .axiom-hero-title {{
        font-size: clamp(1.6rem, 2.8vw, 2.2rem);
        font-weight: 600;
        letter-spacing: -0.03em;
        color: var(--foreground);
        margin: 0 0 1.5rem 0;
        line-height: 1.2;
    }}

    .axiom-composer-container {{
        max-width: 680px;
        margin: 0 auto 1.75rem auto;
    }}

    .quick-start-label {{
        max-width: 680px;
        margin: 0 auto 0.65rem auto;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted-foreground);
        text-align: left;
    }}

    /* Tarjetas de inicio rapido */
    .quick-start-grid {{
        max-width: 680px;
        margin: 0 auto;
    }}
    [class*="st-key-qs_"] button {{
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: center !important;
        text-align: left !important;
        padding: 0.85rem 1rem !important;
        min-height: 80px !important;
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
        cursor: pointer !important;
        white-space: pre-wrap !important;
        animation: shadcnFadeUp 0.4s var(--ease-out-expo) both !important;
        transition: all 0.16s var(--ease-out-expo) !important;
    }}
    [class*="st-key-qs_"] button p {{
        margin: 0 !important;
        line-height: 1.35 !important;
        color: var(--muted-foreground) !important;
        font-weight: 400 !important;
    }}
    [class*="st-key-qs_"] button strong {{
        font-size: 0.88rem !important;
        color: var(--foreground) !important;
        display: block !important;
        margin-bottom: 0.25rem !important;
    }}
    [class*="st-key-qs_"] button::before {{
        content: "";
        display: inline-block;
        width: 17px;
        height: 17px;
        margin-bottom: 0.35rem;
        background-color: var(--foreground);
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
    }}
    .st-key-qs_diag button::before {{ -webkit-mask-image: {icon_leaf}; mask-image: {icon_leaf}; }}
    .st-key-qs_fert button::before {{ -webkit-mask-image: {icon_sprout}; mask-image: {icon_sprout}; }}
    .st-key-qs_mkt button::before {{ -webkit-mask-image: {icon_cash}; mask-image: {icon_cash}; }}
    .st-key-qs_clim button::before {{ -webkit-mask-image: {icon_cloud}; mask-image: {icon_cloud}; }}

    [class*="st-key-qs_"] button:hover {{
        background-color: var(--muted) !important;
        border-color: var(--border-strong) !important;
        transform: translateY(-2px) !important;
    }}
    [class*="st-key-qs_"] button:active {{
        transform: scale(0.985) !important;
    }}

    /* Ocultar iconos / avatares de los mensajes de chat */
    [data-testid="stChatMessage"] [data-testid*="Avatar"],
    [data-testid="stChatMessage"] [data-testid*="avatar"],
    [data-testid="stChatMessage"] > div:first-child:not([data-testid="stChatMessageContent"]) {{
        display: none !important;
    }}

    /* Mensajes alineados por rol: Usuario a la derecha, Asistente a la izquierda */
    .chat-flow-container {{
        max-width: 860px;
        margin: 0 auto;
    }}
    [data-testid="stChatMessage"] {{
        border-radius: var(--radius) !important;
        padding: 0.85rem 1.15rem !important;
        margin-bottom: 0.75rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.14);
        gap: 0 !important;
    }}
    [data-testid="stChatMessage"] > div[data-testid="stChatMessageContent"] {{
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 !important;
    }}
    /* Mensajes del Usuario (lado DERECHO) */
    [data-testid="stChatMessage"]:has(.chat-side-user) {{
        width: fit-content !important;
        min-width: 140px !important;
        max-width: 78% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        background-color: var(--user-bubble) !important;
        border: 1px solid var(--border) !important;
        border-top-right-radius: 2px !important;
        border-top-left-radius: var(--radius) !important;
        border-bottom-right-radius: var(--radius) !important;
        border-bottom-left-radius: var(--radius) !important;
        animation: chatSlideRight 0.3s var(--ease-out-expo) both !important;
    }}
    .chat-side-user {{
        text-align: right !important;
    }}
    .chat-side-user .chat-role-tag {{
        text-align: right !important;
    }}

    /* Mensajes del Asistente (lado IZQUIERDO) */
    [data-testid="stChatMessage"]:has(.chat-side-bot) {{
        width: fit-content !important;
        min-width: 220px !important;
        max-width: 84% !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        background-color: var(--bot-bubble) !important;
        border: 1px solid var(--border-strong) !important;
        border-top-left-radius: 2px !important;
        border-top-right-radius: var(--radius) !important;
        border-bottom-left-radius: var(--radius) !important;
        border-bottom-right-radius: var(--radius) !important;
        animation: chatSlideLeft 0.32s var(--ease-out-expo) both !important;
    }}
    .chat-side-bot {{
        text-align: left !important;
    }}
    .chat-side-bot .chat-role-tag {{
        text-align: left !important;
    }}
    .chat-role-tag {{
        font-family: var(--font-mono);
        font-size: 0.68rem;
        font-weight: 500;
        color: var(--muted-foreground);
        margin-bottom: 0.25rem;
        display: block;
    }}

    /* Foco en chat input */
    [data-testid="stChatInput"] {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        background-color: var(--card) !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }}
    [data-testid="stChatInput"]:focus-within {{
        border-color: var(--border-strong) !important;
        box-shadow: 0 0 0 1px var(--border-strong) !important;
    }}
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus-visible,
    [data-testid="stChatInput"] textarea:active {{
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
        background-color: transparent !important;
    }}
    [data-testid="stChatInputSubmitButton"] {{
        border-radius: 0.375rem !important;
    }}

    /* Boton de adjuntar integrado en st.chat_input */
    [data-testid="stChatInput"] [data-testid*="FileUploader"],
    [data-testid="stChatInput"] button[aria-label*="attach"],
    [data-testid="stChatInput"] button[aria-label*="upload"] {{
        color: var(--muted-foreground) !important;
    }}

    /* Tarjetas y tablas responsive */
    .shadcn-card {{
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.15rem 1.25rem;
        margin-bottom: 0.85rem;
        animation: shadcnFadeUp 0.34s var(--ease-out-expo) both;
        transition: border-color 0.18s var(--ease-out-expo);
    }}
    .shadcn-card:hover {{
        border-color: var(--border-strong);
    }}
    .shadcn-label {{
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--muted-foreground);
        margin-bottom: 0.2rem;
    }}
    .shadcn-value {{
        font-family: var(--font-mono);
        font-size: 1.45rem;
        font-weight: 600;
        color: var(--foreground);
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }}
    .shadcn-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin-top: 0.4rem;
    }}
    .shadcn-table th {{
        text-align: left;
        font-weight: 500;
        color: var(--muted-foreground);
        border-bottom: 1px solid var(--border);
        padding: 0.5rem 0.4rem;
    }}
    .shadcn-table td {{
        padding: 0.5rem 0.4rem;
        border-bottom: 1px solid var(--border);
        color: var(--foreground);
    }}
    .shadcn-table tr:last-child td {{
        border-bottom: none;
    }}
    .shadcn-table .num {{
        text-align: right;
        font-family: var(--font-mono);
        font-variant-numeric: tabular-nums;
    }}

    /* Metricas */
    [data-testid="stMetric"] {{
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.85rem 1rem;
        animation: shadcnFadeUp 0.34s var(--ease-out-expo) both;
        transition: border-color 0.18s var(--ease-out-expo), transform 0.18s var(--ease-out-expo);
    }}
    [data-testid="stMetric"]:hover {{
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }}
    [data-testid="stMetricValue"] {{
        font-family: var(--font-mono) !important;
        font-variant-numeric: tabular-nums !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.78rem !important;
        color: var(--muted-foreground) !important;
    }}

    /* Botones primarios (alto contraste WCAG AAA para Continuar en el chat y acciones clave) */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid*="primary"],
    .stMain button[kind="primary"],
    .stMain [data-testid="baseButton-primary"],
    [data-testid="stMain"] button[kind="primary"],
    [data-testid="stMain"] [data-testid="baseButton-primary"],
    section.main button[kind="primary"],
    section.main [data-testid="baseButton-primary"] {{
        background-color: var(--primary) !important;
        color: var(--primary-foreground) !important;
        border: 1px solid var(--primary) !important;
        border-radius: var(--radius) !important;
        min-height: 42px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.16s var(--ease-out-expo) !important;
        cursor: pointer !important;
    }}
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid*="primary"] *,
    .stMain button[kind="primary"] *,
    .stMain [data-testid="baseButton-primary"] *,
    [data-testid="stMain"] button[kind="primary"] *,
    [data-testid="stMain"] [data-testid="baseButton-primary"] *,
    section.main button[kind="primary"] *,
    section.main [data-testid="baseButton-primary"] * {{
        color: var(--primary-foreground) !important;
        font-weight: 600 !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid*="primary"]:hover,
    .stMain button[kind="primary"]:hover,
    .stMain [data-testid="baseButton-primary"]:hover,
    [data-testid="stMain"] button[kind="primary"]:hover,
    [data-testid="stMain"] [data-testid="baseButton-primary"]:hover,
    section.main button[kind="primary"]:hover,
    section.main [data-testid="baseButton-primary"]:hover {{
        background-color: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
        color: var(--primary-foreground) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
    }}
    .stButton > button[kind="primary"]:hover *,
    .stButton > button[data-testid*="primary"]:hover *,
    .stMain button[kind="primary"]:hover *,
    .stMain [data-testid="baseButton-primary"]:hover *,
    [data-testid="stMain"] button[kind="primary"]:hover *,
    [data-testid="stMain"] [data-testid="baseButton-primary"]:hover *,
    section.main button[kind="primary"]:hover *,
    section.main [data-testid="baseButton-primary"]:hover * {{
        color: var(--primary-foreground) !important;
    }}
    .stButton > button[kind="primary"]:active,
    .stButton > button[data-testid*="primary"]:active,
    .stMain button[kind="primary"]:active,
    .stMain [data-testid="baseButton-primary"]:active,
    [data-testid="stMain"] button[kind="primary"]:active,
    [data-testid="stMain"] [data-testid="baseButton-primary"]:active {{
        transform: translateY(0) scale(0.99) !important;
    }}

    /* Botones secundarios y de descarga en area principal */
    .stMain button[kind="secondary"],
    .stMain [data-testid="baseButton-secondary"],
    [data-testid="stMain"] button[kind="secondary"],
    [data-testid="stMain"] [data-testid="baseButton-secondary"],
    section.main button[kind="secondary"],
    section.main [data-testid="baseButton-secondary"],
    .stMain .stDownloadButton > button,
    [data-testid="stMain"] .stDownloadButton > button {{
        background-color: var(--card) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius) !important;
        min-height: 40px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.16s var(--ease-out-expo) !important;
        cursor: pointer !important;
    }}
    .stMain button[kind="secondary"] *,
    .stMain [data-testid="baseButton-secondary"] *,
    [data-testid="stMain"] button[kind="secondary"] *,
    [data-testid="stMain"] [data-testid="baseButton-secondary"] *,
    section.main button[kind="secondary"] *,
    section.main [data-testid="baseButton-secondary"] *,
    .stMain .stDownloadButton > button *,
    [data-testid="stMain"] .stDownloadButton > button * {{
        color: var(--foreground) !important;
        font-weight: 500 !important;
    }}
    .stMain button[kind="secondary"]:hover,
    .stMain [data-testid="baseButton-secondary"]:hover,
    [data-testid="stMain"] button[kind="secondary"]:hover,
    [data-testid="stMain"] [data-testid="baseButton-secondary"]:hover,
    section.main button[kind="secondary"]:hover,
    section.main [data-testid="baseButton-secondary"]:hover,
    .stMain .stDownloadButton > button:hover,
    [data-testid="stMain"] .stDownloadButton > button:hover {{
        background-color: var(--muted-active) !important;
        border-color: var(--foreground) !important;
        color: var(--foreground) !important;
        transform: translateY(-1px) !important;
    }}
    .stMain button[kind="secondary"]:hover *,
    .stMain [data-testid="baseButton-secondary"]:hover *,
    [data-testid="stMain"] button[kind="secondary"]:hover *,
    [data-testid="stMain"] [data-testid="baseButton-secondary"]:hover *,
    section.main button[kind="secondary"]:hover *,
    section.main [data-testid="baseButton-secondary"]:hover *,
    .stMain .stDownloadButton > button:hover *,
    [data-testid="stMain"] .stDownloadButton > button:hover * {{
        color: var(--foreground) !important;
    }}

    button:focus-visible,
    select:focus-visible,
    [role="button"]:focus-visible {{
        outline: 2px solid var(--ring) !important;
        outline-offset: 2px !important;
    }}

    hr {{
        margin: 0.85rem 0 !important;
        border-color: var(--border) !important;
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 0.75rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }}
        [data-testid="stChatMessage"]:has(.chat-side-user),
        [data-testid="stChatMessage"]:has(.chat-side-bot) {{
            max-width: 90% !important;
        }}
        .stButton > button, .stDownloadButton > button, [data-testid="stPopover"] > button, [class*="st-key-qs_"] button {{
            min-height: 44px !important;
        }}
    }}

    {compact_css}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_brand_top_row(sidebar_compacto: bool = False):
    """Renderiza la marca en el tope del sidebar con icono MDI."""
    icon = mdi_svg_inline("brand", size=26 if not sidebar_compacto else 30)
    label_html = "<span>Caficultura</span>" if not sidebar_compacto else ""
    st.markdown(
        f'<div class="axiom-brand">{icon}{label_html}</div>',
        unsafe_allow_html=True,
    )


def render_topbar(titulo: str, tag_contexto: str = ""):
    """Renderiza el titulo de la vista superior con icono MDI."""
    icon = mdi_svg_inline(titulo, size=24)
    st.markdown(
        f'<div class="axiom-topbar">{icon}<span>{titulo}</span></div>',
        unsafe_allow_html=True,
    )


def render_hero_greeting(nombre_rol: str, lote_str: str):
    """Renderiza el saludo centrado inspirado en la referencia Axiom."""
    hora = datetime.now().hour
    saludo = "Buenos dias" if hora < 12 else ("Buenas tardes" if hora < 19 else "Buenas noches")
    html = f"""
    <div class="axiom-hero-wrap">
        <div class="axiom-hero-badge">{lote_str}</div>
        <h1 class="axiom-hero-title">{saludo}, {nombre_rol}</h1>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
