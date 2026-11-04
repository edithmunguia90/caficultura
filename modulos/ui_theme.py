"""
modulos/ui_theme.py
Estilos y componentes visuales para la interfaz web.
Aplica principios de diseno limpio y ergonomico para entornos agricolas.
"""
import streamlit as st

def aplicar_estilos_tema():
    """Inyecta reglas CSS personalizadas para mejorar la legibilidad y reducir ruido visual."""
    css = """
    <style>
    :root {
        --color-primary: #15803d;
        --color-primary-hover: #166534;
        --color-accent: #a16207;
        --color-surface: #ffffff;
        --color-border: #e2e8f0;
        --color-text-main: #0f172a;
        --color-text-muted: #64748b;
    }

    /* Contenedores y espaciado general */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }

    /* Tarjetas de contenido */
    .agro-card {
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    /* Badges de estado del sistema */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .status-success {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .status-warning {
        background-color: #fef9c3;
        color: #854d0e;
        border: 1px solid #fef08a;
    }
    .status-info {
        background-color: #e0f2fe;
        color: #075985;
        border: 1px solid #bae6fd;
    }

    /* Estilo de sugerencias rapidas */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    .stButton > button:hover {
        border-color: var(--color-primary);
        color: var(--color-primary);
    }

    /* Reduccion de divisiones excesivas */
    hr {
        margin: 1.2rem 0;
        border-color: var(--color-border);
    }

    /* Mensajes de chat */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_status_pill(label: str, estado: str, variante: str = "success") -> str:
    """Genera un componente visual compacto para senalizar estado operativo."""
    clase_variante = {
        "success": "status-success",
        "warning": "status-warning",
        "info": "status-info"
    }.get(variante, "status-info")
    return f'<span class="status-badge {clase_variante}"><b>{label}:</b>&nbsp;{estado}</span>'

