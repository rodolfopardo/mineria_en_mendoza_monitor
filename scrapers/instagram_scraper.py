"""
Instagram Scraper - Scraper para Instagram usando Apify
"""

from apify_client import ApifyClient
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class InstagramScraper(BaseScraper):
    """Scraper para Instagram usando Apify"""

    def __init__(self):
        super().__init__(platform="instagram")
        self.client = ApifyClient(self.apify_token)

        # Actor de Apify para Instagram
        # Usando shu8hern/instagram-scraper que es más confiable
        self.profile_actor = "shu8hern/instagram-scraper"
        self.hashtag_actor = "shu8hern/instagram-scraper"
        self.post_actor = "shu8hern/instagram-scraper"

    def fetch_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Busca publicaciones por hashtag/palabra clave en Instagram"""

        # Convertir keyword a hashtag format
        hashtag = keyword.replace(" ", "").replace("#", "").lower()

        run_input = {
            "hashtags": [hashtag],
            "resultsLimit": max_results,
            "searchType": "hashtag",
        }

        try:
            print(f"      Ejecutando Apify actor para hashtag: #{hashtag}")

            run = self.client.actor(self.hashtag_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} posts")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_by_account(self, username: str, max_results: int = 20) -> List[Dict]:
        """Obtiene publicaciones de una cuenta de Instagram"""

        # Limpiar username
        username = username.replace("@", "")

        run_input = {
            "username": [username],
            "resultsLimit": max_results,
        }

        try:
            print(f"      Ejecutando Apify actor para usuario: @{username}")

            run = self.client.actor(self.profile_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                # Filtrar errores
                if item.get('error'):
                    continue
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} posts")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_post_details(self, post_url: str) -> Dict:
        """Obtiene detalles de un post específico"""

        run_input = {
            "directUrls": [post_url],
            "resultsType": "details",
        }

        try:
            run = self.client.actor(self.post_actor).call(run_input=run_input)

            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                return item

            return {}

        except Exception as e:
            print(f"Error obteniendo detalles del post: {e}")
            return {}

    def parse_post(self, raw_data: Dict) -> Dict:
        """Parsea datos de Instagram a formato estándar"""

        # Instagram devuelve diferentes estructuras según el actor usado
        # Intentamos manejar las más comunes

        post_id = raw_data.get('id') or raw_data.get('shortCode') or raw_data.get('pk')

        # URL del post
        shortcode = raw_data.get('shortCode') or raw_data.get('code')
        if shortcode:
            post_url = f"https://www.instagram.com/p/{shortcode}/"
        else:
            post_url = raw_data.get('url') or raw_data.get('postUrl')

        # Información del autor
        owner = raw_data.get('ownerUsername') or raw_data.get('owner', {})
        if isinstance(owner, dict):
            author_username = owner.get('username', '')
            author_name = owner.get('full_name', '')
            author_followers = owner.get('follower_count', 0)
        else:
            author_username = owner
            author_name = raw_data.get('ownerFullName', '')
            author_followers = raw_data.get('ownerFollowers', 0)

        # Contenido
        caption = raw_data.get('caption') or raw_data.get('text') or ''
        if isinstance(caption, dict):
            caption = caption.get('text', '')

        # Métricas
        likes = (
            raw_data.get('likesCount') or
            raw_data.get('likes') or
            raw_data.get('edge_liked_by', {}).get('count', 0)
        )

        comments = (
            raw_data.get('commentsCount') or
            raw_data.get('comments') or
            raw_data.get('edge_media_to_comment', {}).get('count', 0)
        )

        # Instagram no muestra shares públicamente, usamos saves como proxy
        shares = raw_data.get('savesCount', 0)

        views = raw_data.get('videoViewCount') or raw_data.get('videoViews', 0)

        # Tipo de post
        post_type = raw_data.get('type', 'image')
        if raw_data.get('isVideo') or raw_data.get('videoUrl'):
            post_type = 'video'
        elif raw_data.get('childPosts') or raw_data.get('sidecarChildren'):
            post_type = 'carousel'

        # Fecha
        timestamp = raw_data.get('timestamp') or raw_data.get('taken_at_timestamp')
        if timestamp:
            if isinstance(timestamp, (int, float)):
                post_date = datetime.fromtimestamp(timestamp).isoformat()
            else:
                post_date = timestamp
        else:
            post_date = None

        return {
            'platform': 'instagram',
            'post_id': str(post_id) if post_id else None,
            'post_url': post_url,
            'author_username': author_username,
            'author_name': author_name,
            'author_followers': int(author_followers) if author_followers else 0,
            'content': caption,
            'post_type': post_type,
            'likes': int(likes) if likes else 0,
            'comments': int(comments) if comments else 0,
            'shares': int(shares) if shares else 0,
            'views': int(views) if views else 0,
            'post_date': post_date
        }


if __name__ == "__main__":
    scraper = InstagramScraper()
    results = scraper.run(
        fetch_by_keywords=True,
        fetch_by_accounts=True,
        max_per_keyword=20,
        max_per_account=10
    )
    print(f"\nResultados totales: {results['totals']}")
