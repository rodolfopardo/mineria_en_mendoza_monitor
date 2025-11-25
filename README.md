# Monitor Social - Mineria en Mendoza

Dashboard de monitoreo de redes sociales para analisis de impacto y riesgo sociopolitico relacionado con la mineria en Mendoza, Argentina.

## Caracteristicas

- **Monitoreo multi-plataforma**: TikTok, Instagram, Facebook, Twitter
- **Analisis de impacto**: Metricas consolidadas de engagement y alcance estimado
- **Evaluacion de riesgo**: Sistema de puntuacion automatico (BAJO/MEDIO/ALTO)
- **Deteccion de narrativas**: Identificacion de consignas y temas recurrentes
- **Convocatorias**: Deteccion automatica de llamados a movilizacion
- **Estrategia de comunicacion**: Recomendaciones para campanas de influencers

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/rodolfopardo/mineria_en_mendoza_monitor.git
cd mineria_en_mendoza_monitor

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu token de Apify
```

## Uso

```bash
# Ejecutar el dashboard
streamlit run app.py

# Ejecutar scraping manual
python run_scraper.py
```

## Estructura del Proyecto

```
social_monitor/
├── app.py                 # Dashboard principal (Streamlit)
├── database.py            # Gestion de base de datos SQLite
├── run_scraper.py         # Script de scraping manual
├── requirements.txt       # Dependencias
├── social_monitor.db      # Base de datos con datos precargados
├── analysis/
│   └── impact_analyzer.py # Analisis de impacto y riesgo
└── scrapers/
    ├── base_scraper.py    # Clase base para scrapers
    ├── tiktok_scraper.py  # Scraper de TikTok
    ├── instagram_scraper.py
    ├── facebook_scraper.py
    └── twitter_scraper.py
```

## Datos Incluidos

El repositorio incluye una base de datos con datos reales scrapeados que incluyen:

- **99 publicaciones** de TikTok y Facebook
- **49 posts relevantes** para Mendoza
- Metricas de engagement, alcance y sentimiento
- Datos de cuentas como @marceloromano97 y otros actores clave

## Tecnologias

- **Streamlit** - Framework para el dashboard
- **Apify** - Scraping de redes sociales
- **SQLite** - Base de datos local
- **Plotly** - Graficos interactivos
- **TextBlob** - Analisis de sentimiento

## Desarrollado por

**[Identidad Central](https://www.identidadcentral.com/)**

Especialistas en comunicacion estrategica, marketing digital y gestion de reputacion corporativa.

## Licencia

Este proyecto es privado y confidencial.
