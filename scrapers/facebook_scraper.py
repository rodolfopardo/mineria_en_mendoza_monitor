"""
Facebook Scraper - Scraper para Facebook usando Apify
"""

from apify_client import ApifyClient
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class FacebookScraper(BaseScraper):
    """Scraper para Facebook usando Apify"""

    def __init__(self):
        super().__init__(platform="facebook")
        self.client = ApifyClient(self.apify_token)

        # Actor de Apify para Facebook (probado y funciona)
        self.posts_actor = "apify/facebook-posts-scraper"

    def fetch_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Facebook no soporta búsqueda por keyword, retorna lista vacía"""
        # Facebook search requiere autenticación, usamos solo scraping de páginas
        print(f"      -> Facebook no soporta búsqueda pública por keyword")
        return []

    def fetch_by_account(self, username: str, max_results: int = 20) -> List[Dict]:
        """Obtiene publicaciones de una página de Facebook"""

        # Para Facebook, el username puede ser una URL o el nombre de la página
        if not username.startswith('http'):
            page_url = f"https://www.facebook.com/{username}"
        else:
            page_url = username

        run_input = {
            "startUrls": [{"url": page_url}],
            "resultsLimit": max_results,
        }

        try:
            print(f"      Ejecutando Apify actor para página: {username}")

            run = self.client.actor(self.posts_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} posts")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_post_details(self, post_url: str) -> Dict:
        """Obtiene detalles de un post específico de Facebook"""

        run_input = {
            "startUrls": [{"url": post_url}],
            "resultsLimit": 1,
        }

        try:
            run = self.client.actor(self.posts_actor).call(run_input=run_input)

            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                return item

            return {}

        except Exception as e:
            print(f"Error obteniendo detalles del post: {e}")
            return {}

    def parse_post(self, raw_data: Dict) -> Dict:
        """Parsea datos de Facebook a formato estándar"""

        # ID y URL del post
        post_id = raw_data.get('postId') or raw_data.get('id')
        post_url = raw_data.get('postUrl') or raw_data.get('url')

        if not post_url and post_id:
            post_url = f"https://www.facebook.com/{post_id}"

        # Información del autor
        author_data = raw_data.get('user') or raw_data.get('author') or {}
        if isinstance(author_data, dict):
            author_username = author_data.get('id') or author_data.get('username', '')
            author_name = author_data.get('name', '')
        else:
            author_username = raw_data.get('pageName', '')
            author_name = raw_data.get('pageName', '')

        # Contenido
        content = (
            raw_data.get('text') or
            raw_data.get('message') or
            raw_data.get('postText') or
            ''
        )

        # Métricas - Facebook tiene diferentes formatos
        # Reactions (likes, love, haha, etc.)
        reactions = raw_data.get('reactions') or {}
        if isinstance(reactions, dict):
            likes = reactions.get('total', 0) or reactions.get('count', 0)
        else:
            likes = (
                raw_data.get('likes') or
                raw_data.get('likesCount') or
                raw_data.get('reactionCount', 0)
            )

        comments = (
            raw_data.get('comments') or
            raw_data.get('commentsCount') or
            raw_data.get('commentCount', 0)
        )
        if isinstance(comments, list):
            comments = len(comments)

        shares = (
            raw_data.get('shares') or
            raw_data.get('sharesCount') or
            raw_data.get('shareCount', 0)
        )

        views = raw_data.get('videoViews') or raw_data.get('viewCount', 0)

        # Tipo de post
        post_type = raw_data.get('type', 'post')
        if raw_data.get('isVideo') or raw_data.get('videoUrl'):
            post_type = 'video'
        elif raw_data.get('images') or raw_data.get('photoUrl'):
            post_type = 'image'

        # Fecha
        timestamp = raw_data.get('time') or raw_data.get('timestamp') or raw_data.get('date')
        if timestamp:
            if isinstance(timestamp, (int, float)):
                post_date = datetime.fromtimestamp(timestamp).isoformat()
            elif isinstance(timestamp, str):
                post_date = timestamp
            else:
                post_date = None
        else:
            post_date = None

        return {
            'platform': 'facebook',
            'post_id': str(post_id) if post_id else None,
            'post_url': post_url,
            'author_username': str(author_username) if author_username else None,
            'author_name': author_name,
            'author_followers': 0,  # Facebook no expone esto fácilmente
            'content': content,
            'post_type': post_type,
            'likes': int(likes) if likes else 0,
            'comments': int(comments) if comments else 0,
            'shares': int(shares) if shares else 0,
            'views': int(views) if views else 0,
            'post_date': post_date
        }


if __name__ == "__main__":
    scraper = FacebookScraper()
    results = scraper.run(
        fetch_by_keywords=True,
        fetch_by_accounts=True,
        max_per_keyword=20,
        max_per_account=10
    )
    print(f"\nResultados totales: {results['totals']}")
