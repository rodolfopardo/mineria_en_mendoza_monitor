"""
Social Monitor Dashboard - Monitor de Redes Sociales para Minería en Mendoza
Dashboard interactivo para análisis de impacto y riesgo sociopolítico
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

from database import SocialDatabase
from analysis.impact_analyzer import ImpactAnalyzer
from news_scraper import MineriaNewsScraper

# Importar scrapers solo si hay APIFY_TOKEN (para Streamlit Cloud)
SCRAPING_ENABLED = bool(os.getenv('APIFY_TOKEN'))
if SCRAPING_ENABLED:
    try:
        from scrapers import InstagramScraper, FacebookScraper, TikTokScraper, TwitterScraper
    except Exception:
        SCRAPING_ENABLED = False

# Configuración de página
st.set_page_config(
    page_title="Monitor Social - Minería Mendoza",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== SISTEMA DE AUTENTICACIÓN ==========
def check_password():
    """Verifica las credenciales del usuario"""

    def login_form():
        """Muestra el formulario de login con estilo de Identidad Central"""

        # CSS personalizado para la página de login
        st.markdown("""
        <style>
            .stApp {
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
            }
            .login-container {
                max-width: 500px;
                margin: 0 auto;
                padding: 40px;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            .login-title {
                font-size: 1.8rem;
                font-weight: bold;
                background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0 5px 0;
            }
            .login-subtitle {
                color: #64748b;
                font-size: 0.95rem;
            }
            .feature-box {
                background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
                padding: 25px;
                border-radius: 15px;
                margin: 30px 0;
                color: white;
            }
            .feature-title {
                font-size: 1.1rem;
                font-weight: bold;
                margin-bottom: 15px;
                color: #06b6d4;
            }
            .feature-list {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            .feature-list li {
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                font-size: 0.9rem;
            }
            .feature-list li:last-child {
                border-bottom: none;
            }
            .feature-list li::before {
                content: "✓ ";
                color: #06b6d4;
                font-weight: bold;
            }
            .cta-link {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 25px;
                background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
                color: white !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            .cta-link:hover {
                transform: scale(1.05);
            }
            .footer-text {
                text-align: center;
                color: rgba(255,255,255,0.6);
                font-size: 0.8rem;
                margin-top: 30px;
            }
            /* Ocultar elementos de Streamlit en login */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)

        # Contenedor principal centrado
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)

            # Logo y título
            st.markdown("""
            <div class="login-header">
                <img src="https://www.identidadcentral.com/favicon.png" width="100" style="border-radius: 50%; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.3);">
                <h1 class="login-title">Monitor Social</h1>
                <p class="login-subtitle">Minería en Mendoza</p>
                <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 10px;">
                    Plataforma de inteligencia para el seguimiento y análisis<br>
                    del debate público sobre minería en la provincia de Mendoza
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Formulario de login
            with st.form("login_form"):
                st.markdown("#### Acceso a la plataforma")
                username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

                if submitted:
                    # Credenciales válidas
                    valid_users = {
                        "identidadcentral": "hipo",
                        "valentina": "mineria"
                    }
                    if username in valid_users and password == valid_users[username]:
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")

            # Caja de características
            st.markdown("""
            <div class="feature-box">
                <div class="feature-title">¿Qué ofrece esta plataforma?</div>
                <ul class="feature-list">
                    <li>Monitoreo en tiempo real del debate minero en redes sociales</li>
                    <li>Análisis de narrativas a favor y en contra de la minería</li>
                    <li>Seguimiento de medios de comunicación y noticias sobre proyectos mineros</li>
                    <li>Evaluación de riesgo sociopolítico para el sector</li>
                    <li>Detección de convocatorias a movilización antiminera</li>
                    <li>Identificación de actores clave e influencers en el debate</li>
                    <li>Cobertura de sesiones legislativas y votaciones sobre minería</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            # CTA
            st.markdown("""
            <div style="text-align: center;">
                <p style="color: white; margin-bottom: 10px;">¿Necesitás un monitor para tu organización?</p>
                <a href="https://www.identidadcentral.com/#contacto" target="_blank" class="cta-link">
                    Contactar a Identidad Central
                </a>
            </div>
            """, unsafe_allow_html=True)

            # Footer
            st.markdown("""
            <p class="footer-text">
                Desarrollado por <a href="https://www.identidadcentral.com" target="_blank" style="color: #06b6d4;">Identidad Central</a><br>
                Consultora de Investigación de Opinión Pública y Gestión de Identidad Digital
            </p>
            """, unsafe_allow_html=True)

    # Verificar si ya está autenticado
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_form()
        return False

    return True

# Verificar autenticación antes de mostrar el dashboard
if not check_password():
    st.stop()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .risk-high {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .risk-medium {
        background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
        color: #212529;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .risk-low {
        background: linear-gradient(135deg, #28a745 0%, #218838 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
    }
    .platform-instagram { color: #E1306C; }
    .platform-facebook { color: #1877F2; }
    .platform-tiktok { color: #000000; }
    .platform-twitter { color: #1DA1F2; }
</style>
""", unsafe_allow_html=True)

# Inicializar componentes
db = SocialDatabase()
analyzer = ImpactAnalyzer()
news_scraper = MineriaNewsScraper()

# Sidebar
with st.sidebar:
    # Logo de Identidad Central
    st.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <a href="https://www.identidadcentral.com/" target="_blank">
            <img src="https://www.identidadcentral.com/favicon.png"
                 alt="Identidad Central" width="80" style="border-radius: 50%;">
        </a>
        <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: bold; color: #1f4e79;">Identidad Central</p>
    </div>
    """, unsafe_allow_html=True)
    st.title("Monitor Social")
    st.markdown("**Minería en Mendoza**")
    st.markdown("---")

    # Navegación
    page = st.radio(
        "Navegación",
        [
            "Análisis 48 Horas",
            "Análisis PSJCobre",
            "Datos de Medios",
            "Análisis por Plataforma",
            "Detector de Convocatorias"
        ],
        index=0
    )

    st.markdown("---")

    # Filtro de período
    st.subheader("Período de análisis")
    period_days = st.selectbox(
        "Seleccionar período:",
        [2, 7, 14, 30, 60, 90, 365],
        index=0,  # Por defecto últimas 48 horas
        format_func=lambda x: "Últimas 48 horas" if x == 2 else (f"Últimos {x} días" if x < 365 else "Todo el histórico")
    )

    st.markdown("---")

    # Botón de actualización
    if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
        with st.spinner("Actualizando datos de redes sociales..."):
            st.session_state['updating'] = True

    # Info
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; font-size: 0.75em; color: #888;">
        <a href="https://www.identidadcentral.com/" target="_blank" style="color: #1f4e79; text-decoration: none;">
            Identidad Central
        </a><br>
        Monitor Social v1.0
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ========== PÁGINA: EN VIVO: SESIÓN DIPUTADOS ==========
if page == "En Vivo: Sesión Diputados":
    st.markdown('<p class="main-header">📺 Sesión Legislativa - Votación San Jorge</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sesión Histórica: Aprobación del Proyecto PSJ Cobre Mendocino - 26 de Noviembre 2025</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Banner de sesión finalizada
    st.markdown("""
    <div style="background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;">
        <h2 style="color: white; margin: 0;">
            ✅ SESIÓN FINALIZADA
        </h2>
        <p style="color: white; margin: 10px 0 0 0; font-size: 18px;">
            Cámara de Diputados de Mendoza - 26 de Noviembre 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Video de YouTube embebido
    st.markdown("""
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 10px;">
        <iframe
            src="https://www.youtube.com/embed/OvG4zIP7Abc"
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 10px;"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
        </iframe>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs para organizar contenido
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Textual", "📜 Transcripción", "📋 Contexto"])

    with tab1:
        st.subheader("Análisis de la Sesión Legislativa")

        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duración", "~5 horas")
        with col2:
            st.metric("Segmentos", "7,781")
        with col3:
            st.metric("Palabras", "45,027")
        with col4:
            st.metric("Resultado", "APROBADO")

        st.markdown("---")

        # Diputados que más participaron
        st.subheader("Diputados con más intervenciones")

        # Resultado oficial de la votación
        st.success("**Resultado: APROBADO** - 32 votos A FAVOR vs 13 EN CONTRA")

        diputados_data = {
            'Diputado/a': [
                'José Luis Ramón', 'Germán Gómez', 'Emanuel Fugazzotto', 'Jimena Cogo',
                'Enrique Thomas', 'Valentina Morán', 'Gabriela Lizana', 'Alberto López',
                'Rolando Scanio', 'Érica Pulido', 'Jorge A. Difonso', 'Cintia Gómez',
                'María E. de Marchi', 'Franco Ambrosini', 'Gustavo Cairo', 'Mauricio Di Césare'
            ],
            'Bloque': [
                'Protectora', 'Partido Justicialista', 'Partido Verde', 'PRO',
                'PRO Libertad', 'Partido Justicialista', 'Frente Renovador', 'UCR',
                'La Unión Mendocina', 'UCR', 'La Unión Mendocina', 'PRO',
                'UCR', 'UCR', 'La Libertad Avanza', 'UCR'
            ],
            'Intervenciones': [16, 10, 9, 6, 5, 4, 4, 4, 3, 2, 2, 2, 1, 1, 1, 1],
            'Posición': [
                'En contra', 'En contra', 'En contra', 'A favor',
                'A favor', 'En contra', 'En contra', 'A favor',
                'En contra', 'A favor', 'En contra', 'A favor',
                'A favor', 'A favor', 'A favor', 'A favor'
            ]
        }
        df_diputados = pd.DataFrame(diputados_data)

        col_dip, col_bloq = st.columns(2)

        with col_dip:
            fig_dip = px.bar(
                df_diputados,
                x='Intervenciones',
                y='Diputado/a',
                orientation='h',
                color='Posición',
                color_discrete_map={'A favor': '#28a745', 'En contra': '#dc3545'},
                title='Diputados más activos en el debate'
            )
            fig_dip.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_dip, use_container_width=True)

        with col_bloq:
            st.markdown("### Votación por Bloque")
            bloques_votacion = {
                'Bloque': [
                    'UCR (20)', 'PRO / PRO Libertad (8)', 'Otros aliados (4)',
                    'Partido Justicialista (8)', 'La Unión Mendocina (2)',
                    'Partido Verde (1)', 'Protectora (1)', 'Frente Renovador (1)'
                ],
                'Votos': ['A favor', 'A favor', 'A favor', 'En contra', 'En contra', 'En contra', 'En contra', 'En contra'],
                'Cantidad': [20, 8, 4, 8, 2, 1, 1, 1]
            }
            df_bloques = pd.DataFrame(bloques_votacion)
            st.dataframe(df_bloques, hide_index=True, use_container_width=True)

            st.markdown("**Votaron EN CONTRA (13):**")
            st.markdown("""
            - **PJ**: Germán Gómez, Verónica Valverde, Gustavo Perret, Valentina Morán, Juan Pablo Gulino, Natalia Vicencio, Roxana Escudero, Julio Villafañe
            - **La Unión Mendocina**: Jorge Difonso, Rolando Scanio
            - **Otros**: José Luis Ramón, Emanuel Fugazzotto, Gabriela Lizana
            """)

        st.markdown("---")

        # Frecuencia de términos
        st.subheader("Frecuencia de Términos Clave")

        # Datos del análisis
        terminos_data = {
            'Término': ['minero/a', 'ambiental', 'minería', 'desarrollo', 'impacto',
                       'aprobado', 'agua', 'regalías', 'cobre', 'San Jorge',
                       'CONICET', 'trabajo', 'inversión', '7722', 'empleo',
                       'glaciares', 'científico', 'comunidad', 'contaminación'],
            'Menciones': [164, 160, 108, 83, 67, 64, 56, 52, 47, 36,
                         34, 31, 28, 20, 20, 17, 14, 13, 7]
        }
        df_terminos = pd.DataFrame(terminos_data)

        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            fig = px.bar(
                df_terminos.head(15),
                x='Menciones',
                y='Término',
                orientation='h',
                title='Top 15 Términos más mencionados',
                color='Menciones',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.dataframe(df_terminos, hide_index=True, use_container_width=True)

        st.markdown("---")

        # Argumentos a favor y en contra
        st.subheader("Argumentos del Debate")

        col_favor, col_contra = st.columns(2)

        with col_favor:
            st.markdown("""
            <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745;">
                <h4 style="color: #155724; margin-top: 0;">🟢 Argumentos A FAVOR</h4>
                <ul style="color: #155724;">
                    <li><strong>Regalías</strong>: 15 menciones</li>
                    <li><strong>Desarrollo económico</strong>: 11 menciones</li>
                    <li><strong>Generación de empleo</strong>: 4 menciones</li>
                    <li><strong>Controles ambientales</strong>: 2 menciones</li>
                    <li><strong>Tecnología moderna</strong>: 1 mención</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_contra:
            st.markdown("""
            <div style="background-color: #f8d7da; padding: 15px; border-radius: 10px; border-left: 4px solid #dc3545;">
                <h4 style="color: #721c24; margin-top: 0;">🔴 Argumentos EN CONTRA</h4>
                <ul style="color: #721c24;">
                    <li><strong>Ley 7722</strong>: 8 menciones</li>
                    <li><strong>Daño ambiental</strong>: 5 menciones</li>
                    <li><strong>Sustancias tóxicas</strong>: 2 menciones</li>
                    <li><strong>Ambiente periglacial</strong>: 1 mención</li>
                    <li><strong>Informe CONICET</strong>: citado múltiples veces</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Detalle de intervenciones por diputado
        st.subheader("Detalle de Intervenciones por Diputado")

        intervenciones_detalle = {
            'Diputado/a': [
                'José Luis Ramón',
                'Emanuel Fugazzotto',
                'Gabriela Lizana',
                'Rolando Scanio',
                'Germán Gómez',
                'Jorge A. Difonso',
                'Valentina Morán',
                'Enrique Thomas',
                'Alberto López',
                'Érica Pulido',
                'Jimena Cogo',
                'Cintia Gómez',
                'Gustavo Cairo'
            ],
            'Bloque': [
                'Protectora',
                'Partido Verde',
                'Frente Renovador',
                'La Unión Mendocina',
                'Partido Justicialista',
                'La Unión Mendocina',
                'Partido Justicialista',
                'PRO Libertad',
                'UCR',
                'UCR',
                'PRO',
                'PRO',
                'La Libertad Avanza'
            ],
            'Principales argumentos': [
                'Informe CONICET, principio precautorio, "van a agujerear una montaña", denunció censura del informe científico',
                'Principio precautorio, Fondo Compensador insuficiente, regalías deberían ser 5% no 3%, comparó con Noruega',
                'DIA incompleta según estándares internacionales, faltan estudios hídricos, cuestionó cierre/post-cierre de mina',
                'Falencias técnicas, DGI e informe UNCUYO señalan incumplimientos, pidió más tiempo para consenso',
                'PJ no es antiminero pero faltan garantías, pidió construir consenso político, citó fallos Corte sobre DIAs',
                'Firmó dictamen en minoría, cuestionó procedimiento',
                'Firmó dictamen en minoría',
                'Presentó orden del día, defendió diversificación económica, "nuevas reglas de juego"',
                'Presentó ley de regalías, seguridad jurídica, distribución 12% departamento + 15% fondo desarrollo',
                'Presentó Fondo Compensación Ambiental, "el que contamina paga", estándares internacionales',
                'Habló del impacto positivo en Malargüe, trabajo en territorio',
                'Defendió Malargüe Distrito Minero, audiencias públicas, 70% voces a favor',
                'Comparó con Chile, potencial del cobre, "sueldo de Chile"'
            ],
            'Posición': [
                'En contra', 'En contra', 'En contra', 'En contra', 'En contra', 'En contra', 'En contra',
                'A favor', 'A favor', 'A favor', 'A favor', 'A favor', 'A favor'
            ]
        }

        df_detalle = pd.DataFrame(intervenciones_detalle)

        # Mostrar tabla con colores
        st.dataframe(
            df_detalle.style.apply(
                lambda x: ['background-color: #d4edda' if v == 'A favor' else 'background-color: #f8d7da' for v in x],
                subset=['Posición']
            ),
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")

        # Análisis de narrativas
        st.subheader("Narrativas Identificadas")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **🟢 Narrativa Pro-Minería:**
            - Desarrollo económico (83 menciones)
            - Inversión (28 menciones)
            - Empleo/Trabajo (51 menciones)
            - Regalías para comunidades (52 menciones)
            """)

        with col2:
            st.markdown("""
            **🔴 Narrativa Ambientalista:**
            - Agua (56 menciones)
            - Impacto ambiental (67 menciones)
            - CONICET/Científico (48 menciones)
            - Glaciares (17 menciones)
            - Ley 7722 (20 menciones)
            """)

    with tab2:
        st.subheader("Transcripción Completa")

        st.info("La transcripción fue generada automáticamente usando subtítulos de YouTube.")

        # Leer transcripción
        transcript_path = os.path.join(os.path.dirname(__file__), "transcripts", "transcript_OvG4zIP7Abc_20251127_104147.txt")

        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            # Botón de descarga
            st.download_button(
                label="📥 Descargar Transcripción Completa (TXT)",
                data=transcript_text,
                file_name="transcripcion_sesion_san_jorge_26nov2025.txt",
                mime="text/plain"
            )

            st.markdown("---")

            # Mostrar preview
            st.markdown("**Vista previa (primeras 200 líneas):**")
            lines = transcript_text.split('\n')[:200]
            st.text_area(
                "Transcripción",
                value='\n'.join(lines),
                height=400,
                disabled=True
            )
        else:
            st.warning("Transcripción no disponible todavía.")

    with tab3:
        st.subheader("Contexto de la Sesión")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 📋 Temas tratados

            1. **PSJ Cobre Mendocino (San Jorge)**
               - Declaración de Impacto Ambiental
               - Proyecto de cobre en Uspallata

            2. **Regalías Mineras**
               - Nueva distribución de regalías

            3. **Fondo de Compensación Ambiental**
               - Creación de fondo para comunidades

            4. **MDMO II (Malargüe)**
               - Segundo proyecto minero en Malargüe
            """)

        with col2:
            st.markdown("""
            ### 📊 Resultado de la votación

            **PSJ Cobre Mendocino: APROBADO**

            **Bloques a favor:**
            - Cambia Mendoza
            - Parte del PJ

            **Bloques en contra:**
            - Frente de Izquierda
            - Sectores ambientalistas
            """)

        st.markdown("---")

        st.markdown("""
        ### 🗺️ Contexto Histórico

        Esta fue una sesión histórica para Mendoza. Después de **14 años** del rechazo inicial al proyecto San Jorge (2011),
        la Legislatura aprobó la Declaración de Impacto Ambiental del proyecto minero ahora rebautizado como
        **"PSJ Cobre Mendocino"**.

        El proyecto prevé la extracción de cobre en la zona de Uspallata, cerca del límite con Chile.

        El debate incluyó referencias al informe del **CONICET** presentado el día anterior, que cuestionaba
        aspectos técnicos del proyecto.
        """)

    # Link al video original
    st.markdown("""
    ---
    📺 **Ver en YouTube:** [Sesión completa - Legislatura de Mendoza](https://www.youtube.com/watch?v=OvG4zIP7Abc)
    """)


# ========== PÁGINA: DASHBOARD PRINCIPAL ==========
elif page == "Dashboard Principal":
    st.markdown('<p class="main-header">📊 Monitor de Redes Sociales</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análisis de impacto y riesgo sociopolítico - Minería en Mendoza</p>', unsafe_allow_html=True)
    st.markdown("---")

    # ===== TOTALES DE LA BASE DE DATOS =====
    st.subheader("Base de Datos - Totales Históricos")

    # Obtener totales de la BD
    total_posts_db = db.get_post_count()
    total_news_db = db.get_article_count('news_results')
    total_top_stories_db = db.get_article_count('top_stories')

    col_db1, col_db2, col_db3, col_db4 = st.columns(4)

    with col_db1:
        st.metric("Posts Totales", f"{total_posts_db:,}", help="Total de publicaciones en la base de datos")
    with col_db2:
        st.metric("Noticias", f"{total_news_db:,}", help="Noticias de medios recopiladas")
    with col_db3:
        st.metric("Top Stories", f"{total_top_stories_db:,}", help="Top Stories de Google News")
    with col_db4:
        st.metric("Período Análisis", f"{period_days} días", help="Período seleccionado para el análisis")

    st.markdown("---")

    # Generar reporte
    report = analyzer.generate_full_report(days=period_days)

    # ===== EVALUACIÓN DE RIESGO =====
    st.subheader("Evaluación de Riesgo")

    risk_level = report['risk_evaluation']['risk_level']
    risk_class = f"risk-{risk_level.lower()}"

    col_risk, col_metrics = st.columns([1, 2])

    with col_risk:
        st.markdown(f"""
        <div class="{risk_class}">
            <h2 style="margin:0;">RIESGO {risk_level}</h2>
            <p style="margin:5px 0;">{report['risk_evaluation']['risk_score']}/12 puntos ({report['risk_evaluation']['risk_percentage']}%)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(report['risk_evaluation']['risk_description'])

    with col_metrics:
        # Factores de riesgo
        st.markdown("**Factores evaluados:**")

        factor_data = []
        for factor, score in report['risk_evaluation']['risk_factors']:
            factor_data.append({
                'Factor': factor,
                'Puntuación': score,
                'Nivel': '🔴' if score == 3 else '🟡' if score == 2 else '🟢'
            })

        df_factors = pd.DataFrame(factor_data)
        st.dataframe(df_factors, hide_index=True, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== MÉTRICAS CONSOLIDADAS =====
    st.subheader("Métricas Consolidadas")

    metrics = report['risk_evaluation']['metrics']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Publicaciones",
            f"{metrics['total_posts']:,}",
            help="Publicaciones analizadas en el período"
        )

    with col2:
        st.metric(
            "Total Interacciones",
            f"{metrics['total_engagement']:,}",
            help="Likes + Comentarios + Shares"
        )

    with col3:
        st.metric(
            "Alcance Estimado",
            f"{metrics['estimated_reach']:,}",
            help="Personas potencialmente alcanzadas"
        )

    with col4:
        st.metric(
            "Convocatorias Detectadas",
            len(report['risk_evaluation']['mobilization_calls']),
            help="Llamados a movilización identificados"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== MÉTRICAS POR PLATAFORMA =====
    st.subheader("Distribución por Plataforma")

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        if metrics['by_platform']:
            platform_df = pd.DataFrame([
                {
                    'Plataforma': platform.upper(),
                    'Posts': data['posts'],
                    'Engagement': data['engagement']
                }
                for platform, data in metrics['by_platform'].items()
            ])

            fig = px.pie(
                platform_df,
                values='Engagement',
                names='Plataforma',
                title='Distribución de Engagement por Plataforma',
                color='Plataforma',
                color_discrete_map={
                    'INSTAGRAM': '#E1306C',
                    'FACEBOOK': '#1877F2',
                    'TIKTOK': '#000000',
                    'TWITTER': '#1DA1F2'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de plataformas disponibles")

    with col_table:
        if metrics['by_platform']:
            st.markdown("**Desglose por red:**")
            for platform, data in metrics['by_platform'].items():
                st.markdown(f"""
                **{platform.upper()}**
                - Posts: {data['posts']}
                - Likes: {data['likes']:,}
                - Comentarios: {data['comments']:,}
                - Compartidos: {data['shares']:,}
                """)
        else:
            st.info("Sin datos")

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== NARRATIVAS PRINCIPALES =====
    st.subheader("Principales Narrativas Detectadas")

    narrative_analysis = report['narrative_analysis']

    col_narr, col_cloud = st.columns([1, 1])

    with col_narr:
        st.markdown("**Consignas más frecuentes:**")
        for narrative, count in narrative_analysis['narratives'][:7]:
            if count > 0:
                st.markdown(f"- *\"{narrative}\"* ({count} menciones)")

        if not any(c > 0 for _, c in narrative_analysis['narratives']):
            st.info("No se detectaron narrativas conocidas en el período")

    with col_cloud:
        # Nube de palabras
        if narrative_analysis['word_frequency']:
            word_freq = dict(narrative_analysis['word_frequency'])

            wordcloud = WordCloud(
                width=600,
                height=300,
                background_color='white',
                colormap='Blues',
                max_words=50,
                relative_scaling=0.5
            ).generate_from_frequencies(word_freq)

            fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
            ax_wc.imshow(wordcloud, interpolation='bilinear')
            ax_wc.axis('off')
            st.pyplot(fig_wc)
            plt.close()
        else:
            st.info("No hay suficientes datos para la nube de palabras")

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== TOP PUBLICACIONES =====
    st.subheader("Publicaciones de Mayor Impacto")

    top_posts = report['top_posts']

    if top_posts:
        for i, post in enumerate(top_posts[:5], 1):
            reach_emoji = "🔴" if post.get('reach_level') == 'ALTO' else "🟡" if post.get('reach_level') == 'MEDIO' else "🟢"

            with st.expander(f"{reach_emoji} #{i} - @{post.get('author_username', 'N/A')} ({post.get('platform', 'N/A').upper()}) - {post.get('engagement_total', 0):,} interacciones"):
                col_info, col_metrics = st.columns([2, 1])

                with col_info:
                    st.markdown(f"**Contenido:**")
                    content = post.get('content', '')[:300]
                    st.markdown(f">{content}{'...' if len(post.get('content', '')) > 300 else ''}")
                    st.markdown(f"[Ver publicación]({post.get('post_url', '#')})")

                with col_metrics:
                    st.metric("Likes", f"{post.get('likes', 0):,}")
                    st.metric("Comentarios", f"{post.get('comments', 0):,}")
                    st.metric("Compartidos", f"{post.get('shares', 0):,}")
    else:
        st.info("No hay publicaciones para mostrar. Ejecuta el scraper para obtener datos.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== CUENTAS CON MAYOR IMPACTO =====
    st.subheader("Cuentas con Mayor Impacto")

    top_accounts = report['top_accounts']

    if top_accounts:
        accounts_df = pd.DataFrame(top_accounts[:10])
        accounts_df['username'] = accounts_df['username'].apply(lambda x: f"@{x}")

        fig_accounts = px.bar(
            accounts_df,
            x='username',
            y='total_engagement',
            color='platform',
            title='Top 10 Cuentas por Engagement',
            labels={'username': 'Cuenta', 'total_engagement': 'Engagement Total', 'platform': 'Plataforma'},
            color_discrete_map={
                'instagram': '#E1306C',
                'facebook': '#1877F2',
                'tiktok': '#000000',
                'twitter': '#1DA1F2'
            }
        )
        st.plotly_chart(fig_accounts, use_container_width=True)
    else:
        st.info("No hay datos de cuentas disponibles")


# ========== PÁGINA: ANÁLISIS 48 HORAS ==========
elif page == "Análisis 48 Horas":
    st.header("Analisis Cualitativo - Ultimas 48 Horas")

    # Mostrar fecha de actualización prominente
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
                padding: 15px 20px;
                border-radius: 10px;
                margin-bottom: 20px;">
        <p style="color: white; margin: 0; font-size: 14px;">
            <strong>Actualizado:</strong> 07 de diciembre de 2025 |
            <strong>Período:</strong> 6-7 de diciembre 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ===== INDICADOR DE EBULLICIÓN SOCIAL =====
    st.markdown("""
    <div style="background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 25px;
                border: 2px solid #fbbf24;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h3 style="color: white; margin: 0 0 5px 0; font-size: 18px;">NIVEL DE EBULLICIÓN SOCIAL</h3>
                <p style="color: #fef3c7; margin: 0; font-size: 14px;">Indicador de tensión sociopolítica minera en Mendoza</p>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 48px; font-weight: bold; color: white;">CRÍTICO</span>
            </div>
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
            <div style="display: flex; justify-content: space-between; color: #fef3c7; font-size: 13px;">
                <span>📈 <strong>Tendencia:</strong> EN ASCENSO (vs período anterior)</span>
                <span>⚠️ <strong>Score de riesgo:</strong> 12/12 (100%)</span>
                <span>🔥 <strong>Alcance estimado:</strong> 10M personas</span>
            </div>
        </div>
        <div style="margin-top: 10px; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
            <p style="color: white; margin: 0; font-size: 13px;">
                <strong>Factores críticos:</strong> Represión del martes 9 en puerta del Senado • 68 noticias nuevas en 24hs •
                El Senado postergó votación al lunes 9 • Convocatoria masiva confirmada • Operativo policial máximo anunciado
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    **Resumen ejecutivo** de la conversación digital sobre minería en Mendoza,
    integrando redes sociales y medios de comunicación. Análisis cualitativo basado en datos extraídos.
    """)

    # ===== LO QUE MÁS SE HABLÓ =====
    st.markdown("---")
    st.subheader("Lo que mas se hablo")

    st.warning("**Temas dominantes en la conversación (6-7 diciembre)**")

    st.markdown("""
- **"La represión será televisada":** Página 12 y medios nacionales cubren el violento operativo policial del martes en el Senado de Mendoza. Imágenes de manifestantes encerrados en "corralito" generan indignación masiva.

- **Cornejo cruza el Rubicón:** Los medios describen la estrategia del gobernador como "a todo o nada por la megaminería". El oficialismo forzó el debate en comisiones con fuerte operativo de seguridad.

- **Senado postergó votación al lunes 9:** Tras horas de tensión, se suspendió la sesión definitiva. Las asambleas convocan a nueva movilización masiva para el lunes.

- **"El 9 vamos con todo al Senado":** Convocatoria viral en redes sociales. Las asambleas de todo Mendoza preparan una jornada de máxima movilización para presionar a los senadores.

- **Cobertura mediática nacional sin precedentes:** El conflicto mendocino llega a medios nacionales e internacionales. Noticias Ambientales y El Grito del Sur publican investigaciones sobre el plan del Gobierno para modificar la Ley de Glaciares.
    """)

    # ===== LO QUE DICEN LOS MEDIOS =====
    st.markdown("---")
    st.subheader("Lo que dicen los medios (últimas 48 horas)")

    st.markdown("**Cobertura mediática del conflicto minero - 68 noticias nuevas**")

    col_med1, col_med2 = st.columns(2)

    with col_med1:
        st.markdown("**Medios pro-minería/oficialistas:**")
        st.markdown("""
- **Los Andes:** "El Senado se prepara para debatir los proyectos mineros con un fuerte operativo policial". Cobertura del operativo de seguridad.

- **MDZ Online:** Cobertura del avance de los proyectos en comisiones. Énfasis en el apoyo del gobierno nacional.

- **Sitio Andino:** "Mendoza fortalece su presencia global en minería en Londres". Cobertura de la misión comercial de Latorre.

- **El Economista:** "Mendoza pisa fuerte en Londres: abre la puerta a inversiones en minerales críticos". Foco en oportunidades de inversión.
        """)

    with col_med2:
        st.markdown("**Medios críticos/ambientalistas:**")
        st.markdown("""
- **Página 12:** "La represión será televisada". Cobertura del operativo policial y la represión a manifestantes.

- **Canal Abierto:** "Cornejo cruza el Rubicón: a todo o nada por la megaminería". Análisis crítico de la estrategia oficialista.

- **Noticias Ambientales:** "Una multitudinaria protesta en Mendoza reaviva el rechazo social al proyecto San Jorge". Cobertura de las movilizaciones.

- **Radio Regional:** "Mendoza: la marcha del martes será multitudinaria en contra de la minería". Convocatoria confirmada.
        """)

    st.info("**Tendencia:** La cobertura mediática alcanzó volumen histórico (68 noticias en 24hs). Los medios nacionales tomaron el conflicto mendocino. La represión del martes generó repudio generalizado y amplificó la convocatoria para el lunes 9.")

    # ===== ALERTA DE CONVOCATORIAS =====
    st.markdown("---")
    st.subheader("Riesgo de Convocatorias y Movilizaciones")

    st.error("""
    **ALERTA MÁXIMA - LUNES 9: Votación definitiva en el Senado**

    **Convocatoria confirmada:** "El 9 vamos con todo al Senado" se viralizó en redes. Se espera la movilización más grande desde 2019.
    """)

    st.markdown("""
- **LUNES 9: Votación definitiva + Marcha masiva:** El Senado postergó la votación al lunes. Las asambleas refuerzan la convocatoria. Hashtag #El9VamosConTodo trending en Mendoza.

- **Represión del martes escaló el conflicto:** El operativo policial con "corralito" y detenciones generó repudio masivo. Imágenes virales multiplicaron el alcance del rechazo.

- **Sesiones extraordinarias nacionales confirmadas:** Milei convocará al Congreso para modificar la Ley de Glaciares. El conflicto mendocino se nacionaliza definitivamente.

- **Coordinación interprovincial activa:** Asambleas de San Juan, Catamarca, La Rioja y provincias cordilleranas en alerta. Posibles acciones coordinadas el lunes.

**CRÍTICO: El lunes 9 será el día decisivo. Si el Senado aprueba, se espera escalada inmediata. Si rechaza o posterga, descompresión temporal.**
    """)

    # ===== PUNTOS DE DOLOR =====
    st.markdown("---")
    st.subheader("Puntos de Dolor - Lo que genera rechazo")

    st.markdown("**Temas que generan mayor resistencia emocional**")

    with st.expander("El agua como identidad mendocina", expanded=True):
        st.markdown('"Mendoza es hija del agua" no es solo una consigna, es un valor identitario profundo. Cualquier amenaza percibida al recurso hídrico activa una respuesta visceral.')

    with st.expander("Desconfianza institucional", expanded=True):
        st.markdown('La censura al documento del CONICET refuerza la narrativa de que "nos ocultan información". La falta de transparencia percibida alimenta teorías conspirativas.')

    with st.expander("Imposición desde arriba", expanded=True):
        st.markdown('El sentimiento de que "se decide de espaldas al pueblo" genera frustración. La velocidad del tratamiento legislativo se percibe como atropello.')

    with st.expander("Miedo al precedente", expanded=True):
        st.markdown('"Si aprueban San Jorge, después vienen todos los demás". El temor es que sea el primer dominó que abre la puerta a la megaminería generalizada.')

    # ===== OPORTUNIDADES - LO POSITIVO =====
    st.markdown("---")
    st.subheader("Oportunidades - Narrativas aprovechables")

    st.success("**Espacios para construcción de consenso**")

    with st.expander("Desarrollo económico local", expanded=True):
        st.markdown('Existe apertura al diálogo cuando se habla de empleo genuino y desarrollo para las comunidades locales. El argumento económico tiene receptividad si se territorializa.')

    with st.expander("Regalías y beneficios concretos", expanded=True):
        st.markdown('La discusión sobre regalías (3-5%) genera interés. La gente quiere saber qué gana Mendoza concretamente, más allá de promesas abstractas.')

    with st.expander("Controles y fiscalización", expanded=True):
        st.markdown('El tema de "quién y cómo controla" a San Jorge aparece como preocupación genuina. Hay espacio para comunicar mecanismos de control creíbles.')

    with st.expander("Transición energética", expanded=True):
        st.markdown('El cobre como mineral estratégico para energías limpias es un argumento que resuena en sectores progresistas. Oportunidad de reencuadrar el debate.')

    # ===== CONCLUSIÓN =====
    st.markdown("---")
    st.subheader("Sintesis y Recomendaciones")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Estado de situación - 7 de diciembre**")
        st.markdown("""
El conflicto entró en **fase crítica**. La represión del martes escaló la tensión y amplificó
la convocatoria para el lunes 9. El Senado postergó la votación definitiva aumentando la incertidumbre.

La cobertura mediática alcanzó **volumen histórico** (68 noticias en 24hs). Medios nacionales como
Página 12 titularon "La represión será televisada", nacionalizando el conflicto mendocino.
        """)

        st.markdown("**Próximos días críticos**")
        st.markdown("""
- **LUNES 9:** Votación definitiva en Senado + marcha masiva
- **Sesiones extraordinarias** nacionales por Ley de Glaciares
- **Posible "Mendozazo"** si se aprueba San Jorge
- **Operativo policial reforzado** anticipado por el gobierno
        """)

    with col2:
        st.markdown("**Recomendaciones operativas**")
        st.markdown("""
- **Monitoreo 24/7** desde el domingo hasta el lunes por la noche
- **Alerta sobre hashtags:** #El9VamosConTodo, #NoALaMina, #LaRepresiónSeráTelevisada
- **Seguimiento de redes en tiempo real** durante la sesión del Senado
- **Monitoreo de medios nacionales** que amplificarán cualquier incidente
        """)

        st.markdown("**Escenarios posibles para el lunes 9**")
        st.markdown("""
- **Si se aprueba:** Escalada inmediata. Posible intento de ingreso al Senado. Alta probabilidad de incidentes.
- **Si se rechaza/posterga:** Descompresión temporal. Victoria simbólica del movimiento.
- **Variable crítica:** Nivel de represión policial y cobertura mediática en vivo.
        """)

    # Timestamp con más detalle
    st.markdown("---")
    st.caption(f"Análisis generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Fuentes: {db.get_post_count():,} posts de redes + {db.get_article_count('news_results')} noticias de medios")


# ========== PÁGINA: ANÁLISIS PSJCobre ==========
elif page == "Análisis PSJCobre":
    st.header("Análisis de Cuenta @PSJCobreMendocino")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #E1306C 0%, #F77737 50%, #FCAF45 100%);
                padding: 15px 20px; border-radius: 10px; margin-bottom: 20px;">
        <p style="color: white; margin: 0; font-size: 14px;">
            <strong>Instagram Analytics</strong> | Análisis de rendimiento de la cuenta oficial del proyecto
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Cargar datos del CSV
    try:
        psjcobre_df = pd.read_csv('data/psjcobre_instagram.csv')

        # Procesar datos
        psjcobre_df['fecha'] = pd.to_datetime(psjcobre_df['timestamp'])
        psjcobre_df['dia_semana'] = psjcobre_df['fecha'].dt.day_name()
        psjcobre_df['hora'] = psjcobre_df['fecha'].dt.hour
        psjcobre_df['engagement'] = psjcobre_df['likesCount'] + psjcobre_df['commentsCount']

        # ===== MÉTRICAS PRINCIPALES =====
        st.subheader("Métricas Principales")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Posts", f"{len(psjcobre_df):,}")
        with col2:
            st.metric("Total Likes", f"{psjcobre_df['likesCount'].sum():,}")
        with col3:
            st.metric("Promedio Likes", f"{psjcobre_df['likesCount'].mean():.0f}")
        with col4:
            total_views = psjcobre_df['videoViewCount'].sum()
            st.metric("Video Views", f"{total_views:,.0f}" if pd.notna(total_views) else "N/A")

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            total_plays = psjcobre_df['videoPlayCount'].sum()
            st.metric("Video Plays", f"{total_plays:,.0f}" if pd.notna(total_plays) else "N/A")
        with col6:
            videos_count = len(psjcobre_df[psjcobre_df['type'] == 'Video'])
            st.metric("Videos/Reels", f"{videos_count}")
        with col7:
            carruseles = len(psjcobre_df[psjcobre_df['type'] == 'Sidecar'])
            st.metric("Carruseles", f"{carruseles}")
        with col8:
            imagenes = len(psjcobre_df[psjcobre_df['type'] == 'Image'])
            st.metric("Imágenes", f"{imagenes}")

        # ===== EXPLICACIÓN VIDEO PLAYS vs VIDEO VIEWS =====
        st.markdown("---")
        st.subheader("Video Plays vs Video Views - ¿Qué significa?")

        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            st.info("""
            **📱 Video Plays (Reproducciones automáticas)**

            Son las veces que el video comenzó a reproducirse automáticamente
            cuando alguien scrolleó por el feed. Instagram reproduce videos
            automáticamente sin sonido.

            **Total Plays:** {:,}
            """.format(int(total_plays) if pd.notna(total_plays) else 0))

        with col_exp2:
            st.success("""
            **👁️ Video Views (Visualizaciones reales)**

            Son las reproducciones donde el usuario realmente vio el video
            (generalmente 3+ segundos o interactuó). Representa interés genuino.

            **Total Views:** {:,}
            """.format(int(total_views) if pd.notna(total_views) else 0))

        # Ratio
        if pd.notna(total_plays) and total_plays > 0 and pd.notna(total_views):
            ratio = (total_views / total_plays) * 100
            st.warning(f"""
            **📊 Tasa de Retención:** {ratio:.1f}%

            De cada 100 personas que ven el video pasar en su feed, solo {ratio:.0f} lo miran realmente.
            {"✅ Buen ratio (>10%)" if ratio > 10 else "⚠️ Ratio bajo - Mejorar hooks iniciales" if ratio > 5 else "🔴 Ratio muy bajo - Revisar primeros 3 segundos"}
            """)

        # ===== TABLA COMPARATIVA DE VIDEOS =====
        st.markdown("---")
        st.subheader("Análisis de Videos - Plays vs Views")

        videos_df = psjcobre_df[psjcobre_df['type'] == 'Video'][['fecha', 'likesCount', 'videoPlayCount', 'videoViewCount', 'caption']].copy()
        videos_df = videos_df.dropna(subset=['videoPlayCount', 'videoViewCount'])
        videos_df['Retención %'] = (videos_df['videoViewCount'] / videos_df['videoPlayCount'] * 100).round(1)
        videos_df['caption_short'] = videos_df['caption'].str[:60] + '...'
        videos_df = videos_df.sort_values('videoPlayCount', ascending=False)

        st.dataframe(
            videos_df[['fecha', 'caption_short', 'likesCount', 'videoPlayCount', 'videoViewCount', 'Retención %']].head(15).rename(columns={
                'fecha': 'Fecha',
                'caption_short': 'Contenido',
                'likesCount': 'Likes',
                'videoPlayCount': 'Plays (auto)',
                'videoViewCount': 'Views (real)',
                'Retención %': 'Retención %'
            }),
            use_container_width=True,
            hide_index=True
        )

        # ===== TOP POSTS MÁS VIRALES =====
        st.markdown("---")
        st.subheader("🔥 Top 10 Posts Más Virales")

        top_posts = psjcobre_df.nlargest(10, 'engagement')[['fecha', 'type', 'likesCount', 'commentsCount', 'engagement', 'videoViewCount', 'caption']].copy()
        top_posts['caption_preview'] = top_posts['caption'].str[:80] + '...'

        for i, (idx, row) in enumerate(top_posts.iterrows(), 1):
            with st.expander(f"#{i} - {row['type']} | {row['likesCount']:,} likes | {row['fecha'].strftime('%Y-%m-%d')}"):
                st.write(f"**Likes:** {row['likesCount']:,}")
                st.write(f"**Comments:** {row['commentsCount']:,}")
                if pd.notna(row['videoViewCount']) and row['videoViewCount'] > 0:
                    st.write(f"**Video Views:** {row['videoViewCount']:,.0f}")
                st.write(f"**Caption:** {row['caption'][:300] if pd.notna(row['caption']) else 'Sin caption'}...")

        # ===== GRÁFICO: TIPOS DE CONTENIDO =====
        st.markdown("---")
        st.subheader("Distribución por Tipo de Contenido")

        tipos = psjcobre_df['type'].value_counts()

        fig_tipos = go.Figure(data=[go.Pie(
            labels=tipos.index,
            values=tipos.values,
            hole=0.4,
            marker_colors=['#E1306C', '#F77737', '#FCAF45']
        )])
        fig_tipos.update_layout(title="Posts por Tipo", height=400)
        st.plotly_chart(fig_tipos, use_container_width=True)

        # ===== GRÁFICO: ACTIVIDAD POR DÍA DE LA SEMANA =====
        st.markdown("---")
        st.subheader("📅 Actividad por Día de la Semana")

        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_es = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                   'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}

        actividad_dia = psjcobre_df.groupby('dia_semana').size().reindex(dias_orden)
        actividad_dia.index = [dias_es[d] for d in actividad_dia.index]

        fig_dias = go.Figure(data=[go.Bar(
            x=actividad_dia.index,
            y=actividad_dia.values,
            marker_color='#E1306C'
        )])
        fig_dias.update_layout(
            title="Cantidad de Posts por Día",
            xaxis_title="Día de la Semana",
            yaxis_title="Cantidad de Posts",
            height=400
        )
        st.plotly_chart(fig_dias, use_container_width=True)

        # ===== GRÁFICO: ENGAGEMENT POR DÍA =====
        st.subheader("💡 Engagement Promedio por Día")

        eng_dia = psjcobre_df.groupby('dia_semana')['engagement'].mean().reindex(dias_orden)
        eng_dia.index = [dias_es[d] for d in eng_dia.index]

        fig_eng = go.Figure(data=[go.Bar(
            x=eng_dia.index,
            y=eng_dia.values,
            marker_color='#F77737'
        )])
        fig_eng.update_layout(
            title="Engagement Promedio por Día (Likes + Comments)",
            xaxis_title="Día de la Semana",
            yaxis_title="Engagement Promedio",
            height=400
        )
        st.plotly_chart(fig_eng, use_container_width=True)

        # Insight
        mejor_dia = eng_dia.idxmax()
        peor_dia = eng_dia.idxmin()
        st.info(f"**💡 Insight:** El mejor día para publicar es **{mejor_dia}** (engagement promedio: {eng_dia.max():.0f}). El peor día es **{peor_dia}** ({eng_dia.min():.0f}).")

        # ===== GRÁFICO: ACTIVIDAD POR HORA =====
        st.markdown("---")
        st.subheader("⏰ Actividad por Hora del Día")

        actividad_hora = psjcobre_df.groupby('hora').size()

        fig_hora = go.Figure(data=[go.Bar(
            x=[f"{h:02d}:00" for h in actividad_hora.index],
            y=actividad_hora.values,
            marker_color='#FCAF45'
        )])
        fig_hora.update_layout(
            title="Posts por Hora del Día",
            xaxis_title="Hora",
            yaxis_title="Cantidad de Posts",
            height=400
        )
        st.plotly_chart(fig_hora, use_container_width=True)

        # ===== HASHTAGS MÁS USADOS =====
        st.markdown("---")
        st.subheader("#️⃣ Hashtags Más Usados")

        hashtag_cols = [col for col in psjcobre_df.columns if col.startswith('hashtags/')]
        all_hashtags = []
        for col in hashtag_cols:
            all_hashtags.extend(psjcobre_df[col].dropna().tolist())

        from collections import Counter
        hashtag_counts = Counter(all_hashtags)
        top_hashtags = dict(hashtag_counts.most_common(15))

        fig_hash = go.Figure(data=[go.Bar(
            x=list(top_hashtags.values()),
            y=[f"#{h}" for h in top_hashtags.keys()],
            orientation='h',
            marker_color='#833AB4'
        )])
        fig_hash.update_layout(
            title="Top 15 Hashtags",
            xaxis_title="Veces usado",
            yaxis_title="",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig_hash, use_container_width=True)

        # ===== EVOLUCIÓN TEMPORAL =====
        st.markdown("---")
        st.subheader("📈 Evolución Temporal de Publicaciones")

        psjcobre_df['mes'] = psjcobre_df['fecha'].dt.to_period('M').astype(str)
        posts_por_mes = psjcobre_df.groupby('mes').size()
        likes_por_mes = psjcobre_df.groupby('mes')['likesCount'].sum()

        fig_evol = go.Figure()
        fig_evol.add_trace(go.Bar(
            x=posts_por_mes.index,
            y=posts_por_mes.values,
            name='Posts',
            marker_color='#E1306C'
        ))
        fig_evol.update_layout(
            title="Posts por Mes",
            xaxis_title="Mes",
            yaxis_title="Cantidad",
            height=400
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # ===== RECOMENDACIONES =====
        st.markdown("---")
        st.subheader("📋 Recomendaciones de Mejora")

        col_rec1, col_rec2 = st.columns(2)

        with col_rec1:
            st.error("""
            **🔴 Problemas Detectados:**

            1. **0 comentarios en todos los posts** - Indica bajo engagement real o comentarios desactivados

            2. **Ratio de retención bajo** - Los videos no retienen a la audiencia después del autoplay

            3. **Poca actividad en fin de semana** - Se pierde audiencia que está más activa sábados y domingos

            4. **Contenido muy institucional** - Falta contenido humano y testimonial
            """)

        with col_rec2:
            st.success("""
            **✅ Recomendaciones:**

            1. **Mejorar los primeros 3 segundos** - Hook más fuerte para retener viewers

            2. **Activar y responder comentarios** - Generar conversación

            3. **Publicar más los martes** - Es el día con mejor engagement (299 prom)

            4. **Horarios óptimos:** 13:00-16:00 y 20:00-21:00

            5. **Más contenido de personas reales** - Testimoniales, día a día de trabajadores

            6. **Usar trending audios** en Reels para más alcance
            """)

        # Tabla de temáticas
        st.markdown("---")
        st.subheader("📊 Temáticas Identificadas")

        tematicas = {
            'Temática': [
                'Institucional/Corporativo',
                'Audiencia Pública',
                'Capacitaciones/Cursos',
                'Testimoniales de personas',
                'Desarrollo local',
                'Medio ambiente/Sostenibilidad',
                'Eventos y participación'
            ],
            'Hashtags relacionados': [
                '#PSJCobreMendocino, #MineríaResponsable',
                '#AudienciaPública, #ParticipaciónCiudadana',
                '#Capacitación, #DesarrolloLocal',
                'Videos con personas reales',
                '#DesarrolloLocal, #Uspallata',
                '#DesarrolloSostenible, #MineríaSostenible',
                '#MujeresEnRedes, eventos locales'
            ],
            'Performance': [
                '⭐⭐ Bajo engagement',
                '⭐⭐⭐ Engagement medio',
                '⭐⭐⭐⭐ Alto engagement',
                '⭐⭐⭐⭐⭐ Máximo engagement',
                '⭐⭐⭐ Engagement medio',
                '⭐⭐ Bajo engagement',
                '⭐⭐⭐⭐ Alto engagement'
            ],
            'Recomendación': [
                'Reducir, humanizar más',
                'Mantener pero con más videos',
                'Aumentar, funciona bien',
                'PRIORIZAR - Es lo que mejor funciona',
                'Aumentar con casos reales',
                'Reencuadrar con datos concretos',
                'Mantener, genera comunidad'
            ]
        }

        st.dataframe(pd.DataFrame(tematicas), use_container_width=True, hide_index=True)

        st.caption(f"Datos actualizados: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total posts analizados: {len(psjcobre_df)}")

    except FileNotFoundError:
        st.error("No se encontró el archivo de datos de PSJCobre. Asegurate de que el CSV esté en la ubicación correcta.")
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")


# ========== PÁGINA: DIPUTADOS EN TWITTER ==========
elif page == "Diputados en Twitter":
    st.header("Diputados de Mendoza en Twitter/X")

    st.markdown("""
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #1DA1F2;">
        <p style="margin: 0; color: #333;">
            Seguimiento de las cuentas de Twitter/X de los diputados que participaron en el debate
            sobre el proyecto minero San Jorge (26 de noviembre de 2025).
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Datos de los diputados con Twitter
    diputados_twitter = {
        'Diputado/a': [
            'José Luis Ramón', 'Emanuel Fugazzotto', 'Gabriela Lizana',
            'Rolando Scanio', 'Germán Gómez', 'Enrique Thomas', 'Gustavo Cairo'
        ],
        'Twitter': [
            '@JoseLuisRamonOk', '@EFugazzotto', '@LizanaGaby',
            '@RolandoScanio', '@germangomezmza', '@Enrique_thomas', '@GustavoCairoMza'
        ],
        'Bloque': [
            'Protectora', 'Partido Verde', 'Frente Renovador',
            'La Unión Mendocina', 'Partido Justicialista', 'PRO Libertad', 'La Libertad Avanza'
        ],
        'Posición San Jorge': [
            'En contra', 'En contra', 'En contra',
            'En contra', 'En contra', 'A favor', 'A favor'
        ],
        'URL': [
            'https://twitter.com/JoseLuisRamonOk', 'https://twitter.com/EFugazzotto', 'https://twitter.com/LizanaGaby',
            'https://twitter.com/RolandoScanio', 'https://twitter.com/germangomezmza', 'https://twitter.com/Enrique_thomas', 'https://twitter.com/GustavoCairoMza'
        ]
    }

    df_diputados_tw = pd.DataFrame(diputados_twitter)

    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cuentas monitoreadas", len(df_diputados_tw))
    with col2:
        en_contra = len(df_diputados_tw[df_diputados_tw['Posición San Jorge'] == 'En contra'])
        st.metric("Votaron EN CONTRA", en_contra)
    with col3:
        a_favor = len(df_diputados_tw[df_diputados_tw['Posición San Jorge'] == 'A favor'])
        st.metric("Votaron A FAVOR", a_favor)

    st.markdown("---")

    # Tabla de diputados
    st.subheader("Cuentas de Diputados")

    st.dataframe(
        df_diputados_tw,
        column_config={
            "Twitter": st.column_config.TextColumn("Twitter", width="medium"),
            "URL": st.column_config.LinkColumn("Ir al perfil", width="small"),
            "Posición San Jorge": st.column_config.TextColumn("Voto", width="small")
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")

    # Tweets que mencionan a los diputados
    st.subheader("Tweets sobre los Diputados")

    # Buscar tweets que mencionen a los diputados por nombre o username
    diputados_keywords = [
        ('José Luis Ramón', ['joseluisramonok', 'jose luis ramon', 'ramón']),
        ('Emanuel Fugazzotto', ['efugazzotto', 'fugazzotto']),
        ('Gabriela Lizana', ['lizanagaby', 'lizana']),
        ('Rolando Scanio', ['rolandoscanio', 'scanio']),
        ('Germán Gómez', ['germangomezmza', 'german gomez', 'germán gómez']),
        ('Enrique Thomas', ['enrique_thomas', 'enrique thomas']),
        ('Gustavo Cairo', ['gustavocairomza', 'gustavo cairo', 'cairo'])
    ]

    posts_twitter = db.get_posts(platform='twitter', days=90, limit=1000, only_relevant=False)

    if posts_twitter:
        df_tw = pd.DataFrame(posts_twitter)
        df_tw['content_lower'] = df_tw['content'].str.lower().fillna('')

        # Buscar tweets que mencionen a cada diputado
        tweets_encontrados = []
        for nombre, keywords in diputados_keywords:
            for kw in keywords:
                mask = df_tw['content_lower'].str.contains(kw, na=False)
                matches = df_tw[mask].head(3)
                for _, row in matches.iterrows():
                    if row['id'] not in [t['id'] for t in tweets_encontrados]:
                        tweets_encontrados.append({
                            'id': row['id'],
                            'diputado': nombre,
                            'content': row['content'],
                            'likes': row.get('likes', 0) or 0,
                            'shares': row.get('shares', 0) or 0,
                            'post_url': row.get('post_url', '')
                        })

        if tweets_encontrados:
            st.success(f"Se encontraron {len(tweets_encontrados)} tweets que mencionan a los diputados")

            # Ordenar por engagement
            tweets_ordenados = sorted(tweets_encontrados, key=lambda x: x['likes'] + x['shares'], reverse=True)

            for tweet in tweets_ordenados[:15]:
                with st.container():
                    st.markdown(f"**Menciona a: {tweet['diputado']}**")
                    st.write(tweet['content'][:350] + '...' if len(str(tweet['content'])) > 350 else tweet['content'])
                    col_stats, col_link = st.columns([3, 1])
                    with col_stats:
                        st.caption(f"❤️ {tweet['likes']:,} likes | 🔄 {tweet['shares']:,} retweets")
                    with col_link:
                        if tweet['post_url']:
                            st.markdown(f"[Ver tweet]({tweet['post_url']})")
                    st.markdown("---")
        else:
            st.info("No se encontraron tweets que mencionen a estos diputados en el período seleccionado.")
    else:
        st.info("No hay tweets en la base de datos.")

    st.markdown("---")

    # Links directos a los perfiles
    st.subheader("Acceso Directo a Perfiles")

    col_contra, col_favor = st.columns(2)

    with col_contra:
        st.markdown("### 🔴 Votaron EN CONTRA")
        st.markdown("""
        - [José Luis Ramón](https://twitter.com/JoseLuisRamonOk) - Protectora
        - [Emanuel Fugazzotto](https://twitter.com/EFugazzotto) - Partido Verde
        - [Gabriela Lizana](https://twitter.com/LizanaGaby) - Frente Renovador
        - [Rolando Scanio](https://twitter.com/RolandoScanio) - La Unión Mendocina
        - [Germán Gómez](https://twitter.com/germangomezmza) - PJ
        """)

    with col_favor:
        st.markdown("### 🟢 Votaron A FAVOR")
        st.markdown("""
        - [Enrique Thomas](https://twitter.com/Enrique_thomas) - PRO Libertad
        - [Gustavo Cairo](https://twitter.com/GustavoCairoMza) - La Libertad Avanza
        """)


# ========== PÁGINA: DATOS DE MEDIOS ==========
elif page == "Datos de Medios":
    st.header("Datos de Medios de Comunicación")

    st.markdown("""
    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #1f4e79;">
        <p style="margin: 0; color: #333;">
            Monitoreo de noticias sobre minería en medios de comunicación argentinos.
            Las noticias se obtienen de Google News y se actualizan periodicamente.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Botón para actualizar manualmente
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("Actualizar Noticias", type="primary", use_container_width=True):
            with st.spinner("Buscando nuevas noticias sobre minería..."):
                summary = news_scraper.run()
                if 'error' in summary:
                    st.warning(f"Scraping limitado: {summary['error']}")
                else:
                    st.success(f"Top Stories: {summary['new_top_stories']} nuevas | Noticias: {summary['new_news']} nuevas")
                st.rerun()

    with col_info:
        st.info("Las noticias se actualizan automáticamente. Puedes hacer clic en el botón para forzar una actualización manual.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Obtener datos - Top Stories (todas) y Noticias (últimas 48 horas reales)
    top_stories = news_scraper.get_top_stories(limit=500)
    all_news = news_scraper.get_all_news(limit=500, hours=48)  # Filtrar últimas 48 horas
    all_news_total = news_scraper.get_all_news(limit=500)  # Todas las noticias para estadísticas

    # ========== SECCIÓN 1: TOP STORIES ==========
    st.subheader("Noticias destacadas en Google Top Stories")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #654321;
                margin-bottom: 20px;">
        <p style="color: white;
                  font-size: 16px;
                  margin: 0;
                  font-weight: 500;">
            <strong>Top Stories</strong> es un espacio dedicado que Google muestra cuando identifica que ciertos contenidos
            están recibiendo alto tráfico actualmente. Se buscan noticias con las palabras clave: "minería", "mineros",
            "proyectos mineros" y "ley de glaciares".
        </p>
    </div>
    """, unsafe_allow_html=True)

    if top_stories:
        df_top = pd.DataFrame(top_stories)

        # Mostrar tabla
        df_top_display = df_top[['title', 'source', 'link']].copy()
        df_top_display.columns = ['Título', 'Medio', 'URL']

        st.dataframe(
            df_top_display,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "Título": st.column_config.TextColumn("Título", width="large"),
                "Medio": st.column_config.TextColumn("Medio", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )

        # Gráfico de distribución por medio
        st.subheader("Medios que más hablan de minería en Top Stories")

        media_stats = db.get_media_stats('top_stories')

        if media_stats:
            df_media = pd.DataFrame(media_stats)

            col_chart, col_stats = st.columns([2, 1])

            with col_chart:
                fig = px.pie(
                    df_media,
                    values='count',
                    names='source',
                    title='Distribución de Top Stories por Medio'
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with col_stats:
                st.metric("Total Top Stories", len(df_top))
                st.metric("Medios Únicos", df_top['source'].nunique())
        else:
            st.info("No hay suficientes datos para mostrar estadísticas de medios")
    else:
        st.info("No hay Top Stories almacenadas. Haz clic en 'Actualizar Noticias' para comenzar.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ========== SECCIÓN 2: TODAS LAS NOTICIAS (ÚLTIMAS 48 HORAS) ==========
    st.subheader("Noticias sobre minería (últimas 48 horas)")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #654321;
                margin-bottom: 20px;">
        <p style="color: white;
                  font-size: 16px;
                  margin: 0;
                  font-weight: 500;">
            Aquí se recopilan todas las noticias publicadas en las últimas 48 horas que hablan de minería
            en sus títulos, independientemente si Google las destaca o no.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if all_news:
        df_news = pd.DataFrame(all_news)

        st.success(f"Se encontraron **{len(all_news)} noticias** en las últimas 48 horas")

        # Filtro por medio
        all_sources = ["Todos"] + sorted(df_news['source'].dropna().unique().tolist())
        selected_source = st.selectbox("Filtrar por medio:", all_sources)

        if selected_source != "Todos":
            df_news_filtered = df_news[df_news['source'] == selected_source]
        else:
            df_news_filtered = df_news

        # Mostrar tabla
        df_news_display = df_news_filtered[['title', 'source', 'link']].copy()
        df_news_display.columns = ['Título', 'Medio', 'URL']

        st.dataframe(
            df_news_display,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "Título": st.column_config.TextColumn("Título", width="large"),
                "Medio": st.column_config.TextColumn("Medio", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )

        # Gráfico de distribución por medio
        st.subheader("Medios que más hablan de minería en general")

        media_stats_news = db.get_media_stats('news_results')

        if media_stats_news:
            df_media_news = pd.DataFrame(media_stats_news)

            col_chart2, col_stats2 = st.columns([2, 1])

            with col_chart2:
                fig2 = px.pie(
                    df_media_news,
                    values='count',
                    names='source',
                    title='Distribución de Noticias por Medio (Total histórico)'
                )
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)

            with col_stats2:
                st.metric("Noticias (48h)", len(df_news_filtered))
                st.metric("Total Histórico", len(all_news_total))
                st.metric("Medios Únicos", df_news_filtered['source'].nunique())
        else:
            st.info("No hay suficientes datos para mostrar estadísticas de medios")
    else:
        # No hay noticias en las últimas 48 horas
        st.warning("No hay noticias de las últimas 48 horas. La última actualización fue hace más de 48 horas.")
        if all_news_total:
            st.info(f"Hay **{len(all_news_total)} noticias** en el histórico. Haz clic en 'Actualizar Noticias' para obtener las más recientes.")


# ========== PÁGINA: ANÁLISIS POR PLATAFORMA ==========
elif page == "Análisis por Plataforma":
    st.header("Análisis por Plataforma")

    platform_selected = st.selectbox(
        "Seleccionar plataforma:",
        ["Todas", "Instagram", "Facebook", "TikTok", "Twitter"]
    )

    platform_filter = None if platform_selected == "Todas" else platform_selected.lower()

    posts = db.get_posts(platform=platform_filter, days=period_days, limit=200)

    if posts:
        df = pd.DataFrame(posts)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Posts", len(df))
        with col2:
            st.metric("Total Engagement", f"{df['engagement_total'].sum():,}")
        with col3:
            avg_engagement = df['engagement_total'].mean()
            st.metric("Engagement Promedio", f"{avg_engagement:,.0f}")

        st.markdown("---")

        # Gráfico temporal
        if 'post_date' in df.columns:
            df['post_date'] = pd.to_datetime(df['post_date'], errors='coerce')
            df_dated = df.dropna(subset=['post_date'])

            if not df_dated.empty:
                df_daily = df_dated.groupby(df_dated['post_date'].dt.date).agg({
                    'engagement_total': 'sum',
                    'id': 'count'
                }).reset_index()
                df_daily.columns = ['Fecha', 'Engagement', 'Posts']

                fig = px.line(
                    df_daily,
                    x='Fecha',
                    y='Engagement',
                    title='Evolución del Engagement',
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

        # Tabla de posts
        st.subheader("Listado de Publicaciones")

        display_df = df[['platform', 'author_username', 'engagement_total', 'likes', 'comments', 'shares', 'reach_level', 'post_url']].copy()
        display_df.columns = ['Plataforma', 'Usuario', 'Engagement', 'Likes', 'Comentarios', 'Compartidos', 'Alcance', 'URL']

        st.dataframe(
            display_df,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "Plataforma": st.column_config.TextColumn("Plataforma", width="small"),
                "Alcance": st.column_config.TextColumn("Alcance", width="small")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay datos disponibles para esta plataforma. Ejecuta el scraper primero.")


# ========== PÁGINA: PUBLICACIONES ==========
elif page == "Publicaciones":
    st.header("Explorador de Publicaciones")

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        platform_filter = st.selectbox(
            "Plataforma:",
            ["Todas", "Instagram", "Facebook", "TikTok", "Twitter"]
        )

    with col_f2:
        reach_filter = st.selectbox(
            "Nivel de alcance:",
            ["Todos", "ALTO", "MEDIO", "BAJO"]
        )

    with col_f3:
        sort_by = st.selectbox(
            "Ordenar por:",
            ["Engagement", "Likes", "Comentarios", "Compartidos"]
        )

    # Obtener posts
    platform = None if platform_filter == "Todas" else platform_filter.lower()
    posts = db.get_posts(platform=platform, days=period_days, limit=500)

    if posts:
        df = pd.DataFrame(posts)

        # Aplicar filtro de alcance
        if reach_filter != "Todos":
            df = df[df['reach_level'] == reach_filter]

        # Ordenar
        sort_map = {
            "Engagement": "engagement_total",
            "Likes": "likes",
            "Comentarios": "comments",
            "Compartidos": "shares"
        }
        df = df.sort_values(by=sort_map[sort_by], ascending=False)

        st.markdown(f"**{len(df)} publicaciones encontradas**")
        st.markdown("---")

        # Mostrar posts como cards
        for _, post in df.head(20).iterrows():
            reach_color = "#dc3545" if post['reach_level'] == 'ALTO' else "#ffc107" if post['reach_level'] == 'MEDIO' else "#28a745"

            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid {reach_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{post['platform'].upper()}</strong> | @{post['author_username']}
                        <span style="background-color: {reach_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 10px;">
                            {post['reach_level']}
                        </span>
                    </div>
                    <div style="text-align: right;">
                        ❤️ {post['likes']:,} | 💬 {post['comments']:,} | 🔄 {post['shares']:,}
                    </div>
                </div>
                <p style="margin: 10px 0; color: #555;">{(post['content'] or '')[:200]}{'...' if len(post['content'] or '') > 200 else ''}</p>
                <a href="{post['post_url']}" target="_blank" style="color: #1f4e79;">Ver publicación →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay publicaciones para mostrar")


# ========== PÁGINA: DETECTOR DE CONVOCATORIAS ==========
elif page == "Detector de Convocatorias":
    st.header("Detector de Convocatorias a Movilización")

    st.markdown("""
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <strong>⚠️ Detección automática</strong><br>
        Las convocatorias se detectan automáticamente mediante análisis de texto.
        Pueden existir falsos positivos o convocatorias no detectadas.
    </div>
    """, unsafe_allow_html=True)

    mobilizations = db.get_mobilization_calls(days=period_days)

    if mobilizations:
        st.metric("Convocatorias detectadas", len(mobilizations))
        st.markdown("---")

        for mob in mobilizations:
            event_date = mob.get('event_date', 'No especificada')

            st.markdown(f"""
            <div style="border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <h4 style="margin: 0;">📅 Fecha: {event_date}</h4>
                <p><strong>Plataforma:</strong> {mob.get('platform', 'N/A').upper()}</p>
                <p><strong>Usuario:</strong> @{mob.get('author_username', 'N/A')}</p>
                <p style="color: #666;">{mob.get('content', '')[:300]}...</p>
                <a href="{mob.get('post_url', '#')}" target="_blank">Ver publicación original →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No se han detectado convocatorias a movilización en el período seleccionado")


# ========== PÁGINA: CASOS DE ESTUDIO ==========
elif page == "Casos de Estudio":
    st.header("Casos de Estudio")

    st.markdown("""
    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #1f4e79;">
        <p style="margin: 0; color: #333;">
            Esta seccion documenta casos relevantes de contenido viral relacionado con la mineria en Mendoza.
            Estos casos sirven como referencia para entender patrones de comunicacion y potencial de viralización.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ===== CASO MANU CHAO =====
    st.subheader("Caso: Manu Chao - Apoyo a Uspallata")

    col_info, col_metrics = st.columns([2, 1])

    with col_info:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: linear-gradient(135deg, #000 0%, #333 100%); color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; margin-right: 10px;">
                    TikTok
                </div>
                <span style="font-weight: bold; font-size: 1.1em;">@manuchaoofficial</span>
                <span style="color: #1DA1F2; margin-left: 5px;">✓</span>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin-bottom: 15px;">
                <p style="font-size: 1.1em; margin: 0; font-style: italic;">
                    "Todos con Uspallata !!!<br>
                    Fuera minería de Mendoza !!!"
                </p>
                <p style="color: #666; margin: 10px 0 0 0; font-size: 0.9em;">
                    #manuchao #noalamina #notprogress #mendoza
                </p>
            </div>
            <p style="color: #666; font-size: 0.9em; margin: 0;">
                <strong>Fecha de publicacion:</strong> 2 de Agosto de 2025
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <a href="https://www.tiktok.com/@manuchaoofficial/video/7534059456691227926" target="_blank"
           style="display: inline-block; background: #000; color: white; padding: 10px 20px;
                  border-radius: 5px; text-decoration: none; font-weight: bold;">
            Ver publicacion en TikTok →
        </a>
        """, unsafe_allow_html=True)

    with col_metrics:
        st.markdown("### Metricas")
        st.metric("Likes", "11,700", help="Me gusta en la publicacion")
        st.metric("Comentarios", "278", help="Comentarios totales")
        st.metric("Compartidos", "669", help="Veces compartido")
        st.metric("Reproducciones", "147,900", help="Visualizaciones del video")

        total_engagement = 11700 + 278 + 669
        st.markdown("---")
        st.metric("Engagement Total", f"{total_engagement:,}")

    st.markdown("---")

    # Análisis del caso
    st.subheader("Analisis del Caso")

    col_analysis1, col_analysis2 = st.columns(2)

    with col_analysis1:
        st.markdown("""
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <h4 style="margin: 0 0 10px 0; color: #856404;">Por que es relevante</h4>
            <ul style="margin: 0; color: #856404;">
                <li><strong>Artista internacional</strong> con millones de seguidores</li>
                <li><strong>147,900 reproducciones</strong> en un solo video</li>
                <li>Menciona especificamente <strong>Uspallata y Mendoza</strong></li>
                <li>Utiliza hashtags de alta visibilidad</li>
                <li>Contenido que puede <strong>resurgir</strong> en momentos clave</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_analysis2:
        st.markdown("""
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <h4 style="margin: 0 0 10px 0; color: #721c24;">Factores de Riesgo</h4>
            <ul style="margin: 0; color: #721c24;">
                <li>Potencial de <strong>reactivacion viral</strong></li>
                <li>Credibilidad por ser figura publica reconocida</li>
                <li>Asociacion emocional con la marca "Manu Chao"</li>
                <li>Contenido facilmente compartible</li>
                <li>Puede inspirar acciones similares de otros artistas</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Alcance estimado
    st.subheader("Alcance Estimado")

    # Calcular alcance
    reach_likes = 11700 * 2
    reach_comments = 278 * 5
    reach_shares = 669 * 50
    reach_views = 147900 * 1
    total_reach = reach_likes + reach_comments + reach_shares + reach_views

    col_reach1, col_reach2, col_reach3, col_reach4 = st.columns(4)

    with col_reach1:
        st.metric("Por Likes", f"{reach_likes:,}", help="Likes x 2")
    with col_reach2:
        st.metric("Por Comentarios", f"{reach_comments:,}", help="Comentarios x 5")
    with col_reach3:
        st.metric("Por Shares", f"{reach_shares:,}", help="Compartidos x 50")
    with col_reach4:
        st.metric("Por Views", f"{reach_views:,}", help="Reproducciones x 1")

    st.markdown(f"""
    <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px;">
        <h2 style="margin: 0;">Alcance Total Estimado</h2>
        <h1 style="margin: 10px 0 0 0; font-size: 2.5em;">{total_reach:,} personas</h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Recomendaciones
    st.subheader("Recomendaciones")

    st.markdown("""
    <div style="background-color: #d4edda; padding: 20px; border-radius: 10px;">
        <h4 style="margin: 0 0 15px 0; color: #155724;">Acciones Sugeridas</h4>
        <ol style="margin: 0; color: #155724;">
            <li><strong>Monitoreo continuo:</strong> Seguir la cuenta @manuchaoofficial para detectar nuevas publicaciones</li>
            <li><strong>Preparar respuesta:</strong> Tener contenido positivo listo para contrarrestar si el video resurge</li>
            <li><strong>Identificar patrones:</strong> Analizar que eventos pueden reactivar este tipo de contenido</li>
            <li><strong>No confrontar directamente:</strong> Evitar engagement negativo que amplifique el alcance</li>
            <li><strong>Documentar:</strong> Registrar metricas periodicamente para detectar picos de actividad</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("""
    **Nota:** Este caso es de Agosto 2025 pero se incluye como documentacion porque:
    - Demuestra el potencial de viralización de figuras publicas
    - El contenido puede resurgir en momentos de debate sobre mineria
    - Sirve como benchmark para evaluar el impacto de futuras publicaciones
    """)


# ========== PÁGINA: ESTRATEGIA ==========
elif page == "Estrategia":
    st.header("Estrategia de Comunicación")

    st.markdown("""
    <div style="background-color: #e7f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #1f4e79;">
        <h3 style="margin: 0 0 10px 0; color: #1f4e79;">Enfoque Recomendado</h3>
        <p style="margin: 0; color: #333;">
            Utilizar <strong>influencers mendocinos</strong> con ecommerce o emprendimientos propios para establecer
            una estrategia de comunicación efectiva centrada en los <strong>beneficios económicos</strong> de la minería.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Mensajes clave
    st.subheader("Mensajes Clave Recomendados")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <h4 style="margin: 0 0 10px 0; color: #155724;">Empleo y Oportunidades</h4>
            <ul style="margin: 0; color: #155724;">
                <li>Generación de empleo local directo e indirecto</li>
                <li>Oportunidades para PyMEs y proveedores locales</li>
                <li>Capacitación y desarrollo profesional</li>
                <li>Salarios competitivos en la región</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background-color: #d4edda; padding: 15px; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0; color: #155724;">Progreso Regional</h4>
            <ul style="margin: 0; color: #155724;">
                <li>Inversión en infraestructura</li>
                <li>Desarrollo de comunidades locales</li>
                <li>Dinamización de la economía mendocina</li>
                <li>Modernización tecnológica</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <h4 style="margin: 0 0 10px 0; color: #856404;">Temas a Evitar</h4>
            <ul style="margin: 0; color: #856404;">
                <li>Debate sobre el agua (tema sensible)</li>
                <li>Confrontación directa con grupos ambientalistas</li>
                <li>Aspectos técnicos complejos</li>
                <li>Comparaciones con otros proyectos polémicos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background-color: #cce5ff; padding: 15px; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0; color: #004085;">Tono de Comunicación</h4>
            <ul style="margin: 0; color: #004085;">
                <li>Positivo y propositivo</li>
                <li>Enfocado en historias de éxito</li>
                <li>Testimonios de trabajadores locales</li>
                <li>Datos concretos de impacto económico</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Perfil de influencers
    st.subheader("Perfil de Influencers Objetivo")

    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 15px 0;">Características ideales:</h4>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                <strong>Perfil Comercial</strong>
                <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                    Emprendedores, dueños de ecommerce, negocios locales que puedan hablar desde
                    la perspectiva del crecimiento económico.
                </p>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                <strong>Audiencia Local</strong>
                <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                    Seguidores principalmente de Mendoza y alrededores, con interés en
                    desarrollo regional y oportunidades de negocio.
                </p>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                <strong>Engagement Orgánico</strong>
                <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                    Preferir micro-influencers (5K-50K seguidores) con comunidad activa
                    sobre grandes cuentas con engagement bajo.
                </p>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                <strong>Sin Historial Político</strong>
                <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                    Evitar perfiles con posiciones políticas marcadas o historial de
                    contenido controversial.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Formatos de contenido
    st.subheader("Formatos de Contenido Sugeridos")

    col_format1, col_format2, col_format3 = st.columns(3)

    with col_format1:
        st.markdown("""
        **Videos Cortos (TikTok/Reels)**
        - Testimonios de trabajadores
        - "Un día en mi trabajo"
        - Datos de impacto económico
        - Historias de emprendedores beneficiados
        """)

    with col_format2:
        st.markdown("""
        **Posts Informativos**
        - Infografías de empleo generado
        - Comparativas económicas regionales
        - Historias de éxito locales
        - Anuncios de inversiones
        """)

    with col_format3:
        st.markdown("""
        **Stories/Contenido Efímero**
        - Detrás de escenas
        - Q&A sobre oportunidades
        - Encuestas de opinión
        - Colaboraciones con negocios locales
        """)

    st.markdown("---")

    # Plan de acción
    st.subheader("Plan de Acción Sugerido")

    st.markdown("""
    | Fase | Acción | Objetivo |
    |------|--------|----------|
    | **1. Identificación** | Mapear influencers mendocinos con perfil comercial | Crear base de datos de potenciales colaboradores |
    | **2. Acercamiento** | Contacto inicial enfocado en colaboración comercial | Establecer relación sin mencionar minería inicialmente |
    | **3. Educación** | Compartir información sobre impacto económico | Generar conocimiento sobre beneficios |
    | **4. Activación** | Proponer colaboraciones de contenido | Crear contenido orgánico y auténtico |
    | **5. Amplificación** | Coordinar publicaciones y hashtags | Maximizar alcance de mensajes positivos |
    """)

    st.markdown("---")

    st.markdown("""
    <div style="background-color: #1f4e79; color: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
        <h4 style="margin: 0 0 10px 0; color: white;">¿Necesitás implementar esta estrategia?</h4>
        <p style="margin: 0 0 15px 0;">
            En <strong>Identidad Central</strong> somos especialistas en comunicación estratégica,
            marketing digital y gestión de reputación corporativa. Podemos ayudarte a:
        </p>
        <ul style="margin: 0 0 15px 0;">
            <li>Identificar y contactar influencers relevantes</li>
            <li>Diseñar contenido auténtico y efectivo</li>
            <li>Monitorear y medir el impacto de la campaña</li>
            <li>Gestionar la comunicación en redes sociales</li>
        </ul>
        <a href="https://www.identidadcentral.com/" target="_blank"
           style="display: inline-block; background: white; color: #1f4e79; padding: 10px 20px;
                  border-radius: 5px; text-decoration: none; font-weight: bold;">
            Contactanos →
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    **Nota:** Esta estrategia busca complementar la presencia digital actual con voces
    independientes y creíbles. El éxito depende de la autenticidad del contenido y de
    evitar que parezca comunicación corporativa o gubernamental.
    """)


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 10px;">
    <p style="margin: 0; font-size: 0.9em; color: #666;">
        Monitor Social - Minería en Mendoza
    </p>
    <p style="margin: 5px 0 0 0; font-size: 0.8em;">
        Desarrollado por <a href="https://www.identidadcentral.com/" target="_blank" style="color: #1f4e79; text-decoration: none; font-weight: bold;">Identidad Central</a>
    </p>
</div>
""", unsafe_allow_html=True)
