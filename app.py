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
import subprocess
import json

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
                        "rodolfo": "oh8we61g",
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
            "Datos de Medios"
        ],
        index=0
    )

    st.markdown("---")

    # Filtro de período
    st.subheader("Período de análisis")
    period_days = st.selectbox(
        "Seleccionar período:",
        [7, 14, 30, 60, 90, 365],
        index=0,  # Por defecto últimos 7 días
        format_func=lambda x: f"Últimos {x} días" if x < 365 else "Todo el histórico"
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



# ========== PÁGINA: ANÁLISIS 48 HORAS ==========
if page == "Análisis 48 Horas":
    st.header("Indice de Riesgo de Movilizacion - Ultimas 48 Horas")

    # ===== INDICE DE RIESGO PRINCIPAL =====
    # Nivel actual: MEDIO - Post aprobacion, sin convocatorias masivas nuevas
    riesgo_nivel = "MEDIO"  # ALTO, MEDIO, BAJO
    riesgo_color = "#f59e0b"  # amarillo para MEDIO
    riesgo_icon = "⚠️"

    if riesgo_nivel == "ALTO":
        riesgo_color = "#dc2626"
        riesgo_icon = "🔴"
        riesgo_bg = "linear-gradient(135deg, #dc2626 0%, #991b1b 100%)"
    elif riesgo_nivel == "MEDIO":
        riesgo_color = "#f59e0b"
        riesgo_icon = "🟡"
        riesgo_bg = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
    else:
        riesgo_color = "#22c55e"
        riesgo_icon = "🟢"
        riesgo_bg = "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)"

    st.markdown(f"""
    <div style="background: {riesgo_bg};
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 25px;
                border: 3px solid {riesgo_color};
                box-shadow: 0 0 30px rgba(245, 158, 11, 0.3);">
        <div style="text-align: center;">
            <p style="color: white; margin: 0; font-size: 16px; opacity: 0.9;">INDICE DE RIESGO DE MOVILIZACION</p>
            <h1 style="color: white; margin: 10px 0; font-size: 48px;">{riesgo_icon} {riesgo_nivel}</h1>
            <p style="color: white; margin: 0; font-size: 14px; opacity: 0.8;">Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== EXPLICACION DEL NIVEL =====
    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:
        st.markdown("""
        <div style="background: #fef2f2; padding: 15px; border-radius: 10px; border-left: 4px solid #dc2626;">
            <strong style="color: #dc2626;">🔴 ALTO</strong><br>
            <span style="font-size: 12px; color: #666;">Movilizacion masiva en curso o convocada. Miles de personas. Cobertura nacional.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_exp2:
        st.markdown("""
        <div style="background: #fefce8; padding: 15px; border-radius: 10px; border-left: 4px solid #f59e0b;">
            <strong style="color: #f59e0b;">🟡 MEDIO</strong><br>
            <span style="font-size: 12px; color: #666;">Movilizaciones sin escala social. Actividad en redes pero sin convocatorias masivas.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_exp3:
        st.markdown("""
        <div style="background: #f0fdf4; padding: 15px; border-radius: 10px; border-left: 4px solid #22c55e;">
            <strong style="color: #22c55e;">🟢 BAJO</strong><br>
            <span style="font-size: 12px; color: #666;">Movilizaciones muriendo. Sin convocatorias activas. Tema perdiendo traccion.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ===== SITUACION ACTUAL =====
    st.subheader("Situacion Actual (11 de Diciembre)")

    st.warning("""
    **POST-APROBACION - DIA 2**

    Segunda marcha masiva el 10/12. Asambleas mantienen "alerta y movilizacion permanente".
    Movimiento sigue activo en las calles. Gobierno avanza con promocion internacional en Londres.
    """)

    # ===== CONVOCATORIAS DETECTADAS =====
    st.markdown("---")
    st.subheader("Convocatorias Detectadas")

    col_conv1, col_conv2 = st.columns(2)

    with col_conv1:
        st.markdown("**Ultimas 48 horas:**")
        st.markdown("""
        | Fecha | Evento | Convocantes |
        |-------|--------|-------------|
        | 10/12 | Segunda marcha masiva | Asambleas |
        | 9/12 | Concentracion Legislatura | Asambleas |
        | 9/12 | Marcha KM 0 (19hs) | Multisectorial |
        | 8-9/12 | Gesta del Agua (caminata) | Asamblea Uspallata |
        """)

    with col_conv2:
        st.markdown("**Proximas convocatorias:**")
        st.markdown("""
        | Fecha | Evento | Estado |
        |-------|--------|--------|
        | - | Sin convocatorias masivas detectadas | - |

        **Nota:** Asambleas declararon "alerta y movilizacion permanente".
        Proximo foco: presentacion de recursos judiciales (amparos).
        """)

    # ===== INDICADORES DE ACTIVIDAD =====
    st.markdown("---")
    st.subheader("Indicadores de Actividad")

    col_ind1, col_ind2, col_ind3, col_ind4 = st.columns(4)

    with col_ind1:
        st.metric("Convocatorias activas", "0", delta="Sin cambios", delta_color="off")

    with col_ind2:
        st.metric("Menciones en redes (24h)", "Estable", delta="Post-pico", delta_color="off")

    with col_ind3:
        st.metric("Cobertura mediatica", "Alta", delta="Sigue en agenda")

    with col_ind4:
        st.metric("Recursos judiciales", "En preparacion", delta="Proximo frente")

    # ===== ANALISIS DE TENDENCIA =====
    st.markdown("---")
    st.subheader("Analisis de Tendencia")

    st.markdown("""
    **Factores que bajan el riesgo:**
    - La batalla legislativa termino. El objetivo principal (frenar la aprobacion) no se logro.
    - No hay fechas de votacion proximas que funcionen como catalizador.
    - Gobierno avanza con promocion internacional (Latorre en Londres).

    **Factores que mantienen riesgo MEDIO (no BAJO):**
    - Segunda marcha masiva el 10/12: el movimiento no se desmovilizo.
    - Cobertura mediatica sigue alta: Pagina12, Clarin, medios internacionales.
    - Asambleas declararon "alerta y movilizacion permanente".
    - Posibles amparos judiciales pueden reactivar atencion.
    - Debate nacional por Ley de Glaciares puede escalar el conflicto.
    """)

    # ===== ESCENARIOS PROXIMAS 48-72 HORAS =====
    st.markdown("---")
    st.subheader("Escenarios Proximas 48-72 Horas")

    with st.expander("Escenario 1: Calma relativa (mas probable)", expanded=True):
        st.markdown("""
        - Sin movilizaciones masivas.
        - Actividad concentrada en redes y declaraciones mediaticas.
        - Asambleas preparando estrategia judicial.
        - **Riesgo se mantiene en MEDIO o baja a BAJO.**
        """)

    with st.expander("Escenario 2: Reactivacion por anuncio judicial", expanded=False):
        st.markdown("""
        - Presentacion de amparo genera cobertura mediatica.
        - Posible convocatoria a concentracion en tribunales.
        - Movilizacion acotada (cientos, no miles).
        - **Riesgo se mantiene en MEDIO.**
        """)

    with st.expander("Escenario 3: Escalada (menos probable)", expanded=False):
        st.markdown("""
        - Algun evento catalizador (incidente, declaracion polemica).
        - Nueva convocatoria masiva emergente.
        - Cortes de ruta o acciones directas.
        - **Riesgo sube a ALTO.**
        """)

    # ===== ACTORES A MONITOREAR =====
    st.markdown("---")
    st.subheader("Actores a Monitorear")

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("**Organizaciones clave:**")
        st.markdown("""
        - Asamblea por el Agua de Uspallata
        - Asambleas del Valle de Uco
        - Multisectorial por el Agua
        - Organizaciones de izquierda (PTS, MST)
        """)

    with col_act2:
        st.markdown("**Cuentas en redes:**")
        st.markdown("""
        - @asamblea.uspallata (Instagram)
        - @marcelo_romano0 (influencer antiminero)
        - @cuyo.ambiental
        - Grupos de Facebook de San Carlos y Uspallata
        """)

    # ===== RECOMENDACIONES =====
    st.markdown("---")
    st.subheader("Recomendaciones")

    st.info("""
    **Para las proximas 48 horas:**

    1. **Monitorear redes** de asambleas para detectar nuevas convocatorias.
    2. **Seguir medios judiciales** para anticipar presentacion de amparos.
    3. **Observar declaraciones** de referentes antimineros sobre proximos pasos.
    4. **Estar atentos** a posibles fechas simbolicas (aniversarios, efemerides ambientales).
    """)

    # Timestamp con más detalle
    st.markdown("---")
    st.caption(f"Análisis generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Fuentes: {db.get_post_count():,} posts de redes + {db.get_article_count('news_results')} noticias de medios")

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

    # Obtener datos - Top Stories (todas) y Noticias (últimas 7 días)
    top_stories = news_scraper.get_top_stories(limit=500)
    all_news = news_scraper.get_all_news(limit=500, hours=168)  # Últimos 7 días (168 horas)
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

    # ========== SECCIÓN 2: TODAS LAS NOTICIAS (ÚLTIMOS 7 DÍAS) ==========
    st.subheader("Noticias sobre minería (últimos 7 días)")

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
            Aquí se recopilan todas las noticias de los últimos 7 días que hablan de minería
            en sus títulos, independientemente si Google las destaca o no.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if all_news:
        df_news = pd.DataFrame(all_news)

        st.success(f"Se encontraron **{len(all_news)} noticias** en los últimos 7 días")

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
                st.metric("Noticias (7 días)", len(df_news_filtered))
                st.metric("Total Histórico", len(all_news_total))
                st.metric("Medios Únicos", df_news_filtered['source'].nunique())
        else:
            st.info("No hay suficientes datos para mostrar estadísticas de medios")
    else:
        # No hay noticias en los últimos 7 días
        st.warning("No hay noticias de los últimos 7 días. La última actualización fue hace más de 7 días.")
        if all_news_total:
            st.info(f"Hay **{len(all_news_total)} noticias** en el histórico. Haz clic en 'Actualizar Noticias' para obtener las más recientes.")



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
