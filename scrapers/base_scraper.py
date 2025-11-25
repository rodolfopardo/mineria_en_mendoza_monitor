"""
Base Scraper - Clase base para todos los scrapers de redes sociales
"""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
from textblob import TextBlob
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SocialDatabase

load_dotenv()


class BaseScraper(ABC):
    """Clase base abstracta para scrapers de redes sociales"""

    def __init__(self, platform: str):
        self.platform = platform
        self.db = SocialDatabase()
        self.apify_token = os.getenv('APIFY_TOKEN')

        # Palabras clave para búsqueda
        self.keywords = [kw['keyword'] for kw in self.db.get_active_keywords()]

        # Patrones para detectar convocatorias a movilización
        self.mobilization_patterns = [
            r'convocatoria',
            r'nos vemos en',
            r'salir a la calle',
            r'marcha',
            r'manifestación',
            r'movilización',
            r'vigilia',
            r'estado de alerta',
            r'todos a la',
            r'\d{1,2}[/\-]\d{1,2}.*legislatura',
            r'\d{1,2}[/\-]\d{1,2}.*plaza',
            r'\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        ]

        # Consignas conocidas
        self.known_narratives = [
            "el agua vale más que el oro",
            "el agua de mendoza no se negocia",
            "no a san jorge",
            "la 7722 no se toca",
            "el agua es vida",
            "mendoza es hija del agua",
            "la megaminería es saqueo",
            "no a la mina",
            "la 7722 se defiende en la calle",
        ]

    @abstractmethod
    def fetch_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Busca publicaciones por palabra clave"""
        pass

    @abstractmethod
    def fetch_by_account(self, username: str, max_results: int = 20) -> List[Dict]:
        """Obtiene publicaciones de una cuenta específica"""
        pass

    @abstractmethod
    def parse_post(self, raw_data: Dict) -> Dict:
        """Parsea datos crudos de la API a formato estándar"""
        pass

    def analyze_sentiment(self, text: str) -> str:
        """Analiza el sentimiento de un texto"""
        if not text:
            return "neutral"

        try:
            # TextBlob funciona mejor en inglés, pero da una aproximación
            analysis = TextBlob(text)
            polarity = analysis.sentiment.polarity

            if polarity > 0.1:
                return "positivo"
            elif polarity < -0.1:
                return "negativo"
            else:
                return "neutral"
        except:
            return "neutral"

    def detect_mobilization_call(self, text: str) -> bool:
        """Detecta si el texto contiene una convocatoria a movilización"""
        if not text:
            return False

        text_lower = text.lower()

        for pattern in self.mobilization_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def extract_narratives(self, text: str) -> List[str]:
        """Extrae narrativas/consignas conocidas del texto"""
        if not text:
            return []

        text_lower = text.lower()
        found_narratives = []

        for narrative in self.known_narratives:
            if narrative in text_lower:
                found_narratives.append(narrative)

        return found_narratives

    def match_keywords(self, text: str) -> List[str]:
        """Identifica qué palabras clave aparecen en el texto"""
        if not text:
            return []

        text_lower = text.lower()
        matched = []

        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)

        return matched

    def process_and_store(self, posts: List[Dict]) -> Dict:
        """Procesa y almacena una lista de posts"""
        new_count = 0
        updated_count = 0

        for raw_post in posts:
            try:
                # Parsear a formato estándar
                post = self.parse_post(raw_post)

                if not post or not post.get('post_url'):
                    continue

                # Enriquecer con análisis
                content = post.get('content', '')
                post['sentiment'] = self.analyze_sentiment(content)
                post['has_mobilization_call'] = self.detect_mobilization_call(content)
                post['keywords_matched'] = self.match_keywords(content)
                post['narratives'] = self.extract_narratives(content)

                # Guardar en BD
                if self.db.post_exists(post['post_url']):
                    if self.db.update_post(post):
                        updated_count += 1
                else:
                    if self.db.insert_post(post):
                        new_count += 1

                        # Si tiene convocatoria, registrarla
                        if post['has_mobilization_call']:
                            self._register_mobilization(post)

            except Exception as e:
                print(f"Error procesando post: {e}")
                continue

        return {
            'new': new_count,
            'updated': updated_count,
            'total_processed': len(posts)
        }

    def _register_mobilization(self, post: Dict) -> None:
        """Registra una convocatoria detectada"""
        # Intentar extraer fecha del contenido
        content = post.get('content', '')
        event_date = self._extract_date_from_text(content)

        # Obtener el ID del post de la BD
        posts = self.db.get_posts(platform=self.platform, limit=1)
        if posts:
            # Buscar el post recién insertado
            for p in self.db.get_posts(platform=self.platform, limit=50):
                if p.get('post_url') == post.get('post_url'):
                    self.db.add_mobilization_call(
                        post_id=p.get('id'),
                        event_date=event_date,
                        description=content[:200] if content else None
                    )
                    break

    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Intenta extraer una fecha del texto"""
        if not text:
            return None

        # Patrones de fecha comunes
        patterns = [
            r'(\d{1,2})[/\-](\d{1,2})',  # 26/11 o 26-11
            r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        ]

        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        text_lower = text.lower()

        # Buscar patrón día/mes
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})', text_lower)
        if match:
            day, month = match.groups()
            year = datetime.now().year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Buscar patrón "día de mes"
        match = re.search(r'(\d{1,2})\s+de\s+(\w+)', text_lower)
        if match:
            day, month_name = match.groups()
            if month_name in months:
                year = datetime.now().year
                return f"{year}-{months[month_name]}-{day.zfill(2)}"

        return None

    def run(self, fetch_by_keywords: bool = True, fetch_by_accounts: bool = True,
            max_per_keyword: int = 50, max_per_account: int = 20) -> Dict:
        """Ejecuta el proceso completo de scraping"""
        print(f"\n{'='*60}")
        print(f"SCRAPING DE {self.platform.upper()}")
        print(f"{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

        results = {
            'platform': self.platform,
            'timestamp': datetime.now().isoformat(),
            'by_keyword': {},
            'by_account': {},
            'totals': {'new': 0, 'updated': 0}
        }

        # Búsqueda por palabras clave
        if fetch_by_keywords:
            print(f"\n1. Buscando por palabras clave...")
            for keyword in self.keywords[:5]:  # Limitar a 5 keywords principales
                print(f"   Buscando: '{keyword}'...")
                try:
                    posts = self.fetch_by_keyword(keyword, max_per_keyword)
                    if posts:
                        result = self.process_and_store(posts)
                        results['by_keyword'][keyword] = result
                        results['totals']['new'] += result['new']
                        results['totals']['updated'] += result['updated']
                        print(f"   -> {result['new']} nuevos, {result['updated']} actualizados")
                except Exception as e:
                    print(f"   -> Error: {e}")
                    results['by_keyword'][keyword] = {'error': str(e)}

        # Búsqueda por cuentas monitoreadas
        if fetch_by_accounts:
            print(f"\n2. Obteniendo posts de cuentas monitoreadas...")
            accounts = self.db.get_monitored_accounts(platform=self.platform)

            for account in accounts:
                username = account['username']
                print(f"   Cuenta: @{username}...")
                try:
                    posts = self.fetch_by_account(username, max_per_account)
                    if posts:
                        result = self.process_and_store(posts)
                        results['by_account'][username] = result
                        results['totals']['new'] += result['new']
                        results['totals']['updated'] += result['updated']
                        print(f"   -> {result['new']} nuevos, {result['updated']} actualizados")
                except Exception as e:
                    print(f"   -> Error: {e}")
                    results['by_account'][username] = {'error': str(e)}

        # Log del scraping
        self.db.log_scrape(
            platform=self.platform,
            scrape_type='full',
            status='success',
            posts_found=results['totals']['new'] + results['totals']['updated'],
            posts_new=results['totals']['new']
        )

        print(f"\n{'='*60}")
        print(f"RESUMEN {self.platform.upper()}:")
        print(f"  Posts nuevos: {results['totals']['new']}")
        print(f"  Posts actualizados: {results['totals']['updated']}")
        print(f"{'='*60}\n")

        return results
