"""
Scraper de noticias sobre minería en Mendoza usando SerpAPI
Obtiene Top Stories y News Results de Google News
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Importar serpapi solo si está disponible
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

from database import SocialDatabase


class MineriaNewsScraper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        self.db = SocialDatabase()

        # Palabras clave para búsqueda de minería
        self.keywords = [
            "minería Mendoza",
            "mineros Mendoza",
            "proyectos mineros Mendoza",
            "ley de glaciares minería"
        ]

    def fetch_top_stories(self, query: str = "minería Mendoza") -> Dict:
        """Consulta SerpApi para obtener Top Stories sobre minería"""
        if not SERPAPI_AVAILABLE or not self.api_key:
            return {}

        params = {
            "q": query,
            "hl": "es",
            "gl": "ar",
            "device": "desktop",
            "api_key": self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            print(f"Error al consultar Top Stories: {e}")
            return {}

    def fetch_recent_news(self, query: str = "minería Mendoza", hours: int = 48) -> Dict:
        """Consulta SerpApi para obtener noticias recientes (últimas 48 horas)"""
        if not SERPAPI_AVAILABLE or not self.api_key:
            return {}

        # Calcular fecha de inicio (48 horas atrás)
        date_from = datetime.now() - timedelta(hours=hours)
        date_str = date_from.strftime('%Y-%m-%d')

        params = {
            "engine": "google_news",
            "q": f"{query} after:{date_str}",
            "gl": "ar",
            "hl": "es",
            "api_key": self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            print(f"Error al consultar News Results: {e}")
            return {}

    def parse_and_store_top_stories(self, results: Dict) -> int:
        """Parsea y almacena Top Stories"""
        if not results or 'top_stories' not in results:
            print("No se encontraron Top Stories en los resultados")
            return 0

        top_stories = results.get('top_stories', [])
        new_articles_count = 0

        for story in top_stories:
            # Filtrar por palabras clave relacionadas con minería
            title = story.get('title', '').lower()
            if any(kw.split()[0] in title for kw in ['minería', 'mineros', 'minero', 'proyectos mineros', 'glaciares']):
                if self.db.insert_top_story(story):
                    new_articles_count += 1
                    print(f"Nueva Top Story almacenada: {story.get('title', 'Sin título')}")
                else:
                    print(f"Top Story ya existente: {story.get('title', 'Sin título')}")

        return new_articles_count

    def parse_and_store_news_results(self, results: Dict) -> int:
        """Parsea y almacena News Results"""
        if not results or 'news_results' not in results:
            print("No se encontraron News Results en los resultados")
            print(f"Keys disponibles en results: {list(results.keys()) if results else 'None'}")
            return 0

        news_results = results.get('news_results', [])
        print(f"Total de noticias encontradas en la API: {len(news_results)}")

        new_articles_count = 0

        for idx, article in enumerate(news_results):
            print(f"\n[{idx+1}] Procesando: {article.get('title', 'Sin título')[:50]}...")
            print(f"    Link: {article.get('link', 'No link')}")
            print(f"    Source: {article.get('source', 'No source')}")

            # Saltar noticias sin link
            if not article.get('link'):
                print(f"    Saltando: No tiene link")
                continue

            result = self.db.insert_news_result(article)
            if result:
                new_articles_count += 1
                print(f"    Nueva noticia almacenada")
            else:
                print(f"    Noticia ya existente (duplicada)")

        return new_articles_count

    def run(self) -> Dict:
        """Ejecuta el proceso completo de scraping y almacenamiento"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando búsqueda de noticias sobre minería...")

        if not SERPAPI_AVAILABLE:
            print("SerpAPI no está disponible. Instala google-search-results para habilitar scraping.")
            return {
                'timestamp': datetime.now().isoformat(),
                'new_top_stories': 0,
                'new_news': 0,
                'total_top_stories': self.db.get_article_count('top_stories'),
                'total_news': self.db.get_article_count('news_results'),
                'error': 'SerpAPI no disponible'
            }

        if not self.api_key:
            print("No hay API key configurada. Configura SERPAPI_KEY en .env")
            return {
                'timestamp': datetime.now().isoformat(),
                'new_top_stories': 0,
                'new_news': 0,
                'total_top_stories': self.db.get_article_count('top_stories'),
                'total_news': self.db.get_article_count('news_results'),
                'error': 'API key no configurada'
            }

        total_new_top_stories = 0
        total_new_news = 0

        # Buscar con cada palabra clave
        for keyword in self.keywords:
            print(f"\n{'='*60}")
            print(f"Buscando: {keyword}")
            print(f"{'='*60}")

            # Obtener Top Stories
            print(f"\nBuscando Top Stories para '{keyword}'...")
            top_stories_results = self.fetch_top_stories(keyword)
            new_top_stories = self.parse_and_store_top_stories(top_stories_results)
            total_new_top_stories += new_top_stories

            # Obtener noticias recientes (últimas 48 horas)
            print(f"\nBuscando noticias de últimas 48 horas para '{keyword}'...")
            recent_news_results = self.fetch_recent_news(keyword, hours=48)
            new_news = self.parse_and_store_news_results(recent_news_results)
            total_new_news += new_news

        summary = {
            'timestamp': datetime.now().isoformat(),
            'new_top_stories': total_new_top_stories,
            'new_news': total_new_news,
            'total_top_stories': self.db.get_article_count('top_stories'),
            'total_news': self.db.get_article_count('news_results')
        }

        print(f"\n{'='*60}")
        print(f"Resumen Final:")
        print(f"- Top Stories nuevas: {total_new_top_stories} (Total: {summary['total_top_stories']})")
        print(f"- Noticias nuevas: {total_new_news} (Total: {summary['total_news']})")
        print(f"{'='*60}\n")

        return summary

    def get_top_stories(self, limit: int = 50) -> List[Dict]:
        """Obtiene las últimas Top Stories almacenadas"""
        return self.db.get_top_stories_news(limit)

    def get_all_news(self, limit: int = 100) -> List[Dict]:
        """Obtiene todas las noticias almacenadas"""
        return self.db.get_news_results(limit)


if __name__ == "__main__":
    scraper = MineriaNewsScraper()
    scraper.run()
