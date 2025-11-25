"""
TikTok Scraper - Scraper para TikTok usando Apify
"""

from apify_client import ApifyClient
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class TikTokScraper(BaseScraper):
    """Scraper para TikTok usando Apify"""

    def __init__(self):
        super().__init__(platform="tiktok")
        self.client = ApifyClient(self.apify_token)

        # Actors de Apify para TikTok (probados)
        self.scraper_actor = "clockworks/tiktok-scraper"
        self.comments_actor = "clockworks/tiktok-comments-scraper"
        self.search_actor = "clockworks/tiktok-search-scraper"

    def fetch_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Busca videos por palabra clave en TikTok"""

        # Usar el scraper principal con searchQueries
        run_input = {
            "searchQueries": [keyword],
            "resultsPerPage": max_results,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        }

        try:
            print(f"      Ejecutando Apify actor para búsqueda: '{keyword}'")

            # Usar el scraper principal que soporta búsquedas
            run = self.client.actor(self.scraper_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} videos")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_by_account(self, username: str, max_results: int = 20) -> List[Dict]:
        """Obtiene videos de un usuario de TikTok"""

        # Construir URL del perfil
        if not username.startswith('@'):
            username = f"@{username}"

        profile_url = f"https://www.tiktok.com/{username}"

        run_input = {
            "profiles": [profile_url],
            "resultsPerPage": max_results,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        }

        try:
            print(f"      Ejecutando Apify actor para usuario: {username}")

            run = self.client.actor(self.scraper_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} videos")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_video_details(self, video_url: str) -> Dict:
        """Obtiene detalles de un video específico"""

        run_input = {
            "postURLs": [video_url],
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        }

        try:
            run = self.client.actor(self.scraper_actor).call(run_input=run_input)

            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                return item

            return {}

        except Exception as e:
            print(f"Error obteniendo detalles del video: {e}")
            return {}

    def fetch_video_comments(self, video_url: str, max_comments: int = 100) -> List[Dict]:
        """Obtiene comentarios de un video"""

        run_input = {
            "postURLs": [video_url],
            "maxComments": max_comments,
        }

        try:
            run = self.client.actor(self.comments_actor).call(run_input=run_input)

            comments = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                comments.append(item)

            return comments

        except Exception as e:
            print(f"Error obteniendo comentarios: {e}")
            return []

    def parse_post(self, raw_data: Dict) -> Dict:
        """Parsea datos de TikTok a formato estándar"""

        # ID y URL del video
        video_id = raw_data.get('id') or raw_data.get('videoId')
        author_id = raw_data.get('authorMeta', {}).get('id', '')
        author_unique_id = raw_data.get('authorMeta', {}).get('name', '')

        # URL del video
        post_url = raw_data.get('webVideoUrl') or raw_data.get('videoUrl')
        if not post_url and video_id:
            if author_unique_id:
                post_url = f"https://www.tiktok.com/@{author_unique_id}/video/{video_id}"
            else:
                post_url = f"https://www.tiktok.com/video/{video_id}"

        # Información del autor
        author_meta = raw_data.get('authorMeta', {})
        author_username = (
            author_meta.get('name') or
            author_meta.get('uniqueId') or
            raw_data.get('author', {}).get('uniqueId', '')
        )
        author_name = (
            author_meta.get('nickName') or
            author_meta.get('nickname') or
            raw_data.get('author', {}).get('nickname', '')
        )
        author_followers = (
            author_meta.get('fans') or
            author_meta.get('followers') or
            raw_data.get('authorStats', {}).get('followerCount', 0)
        )

        # Contenido
        content = raw_data.get('text') or raw_data.get('desc') or ''

        # Métricas
        stats = raw_data.get('stats', {})

        likes = (
            raw_data.get('diggCount') or
            stats.get('diggCount') or
            raw_data.get('likes', 0)
        )

        comments = (
            raw_data.get('commentCount') or
            stats.get('commentCount') or
            raw_data.get('comments', 0)
        )

        shares = (
            raw_data.get('shareCount') or
            stats.get('shareCount') or
            raw_data.get('shares', 0)
        )

        views = (
            raw_data.get('playCount') or
            stats.get('playCount') or
            raw_data.get('views', 0)
        )

        # Fecha
        timestamp = raw_data.get('createTime') or raw_data.get('createTimeISO')
        if timestamp:
            if isinstance(timestamp, (int, float)):
                post_date = datetime.fromtimestamp(timestamp).isoformat()
            else:
                post_date = timestamp
        else:
            post_date = None

        return {
            'platform': 'tiktok',
            'post_id': str(video_id) if video_id else None,
            'post_url': post_url,
            'author_username': author_username,
            'author_name': author_name,
            'author_followers': int(author_followers) if author_followers else 0,
            'content': content,
            'post_type': 'video',
            'likes': int(likes) if likes else 0,
            'comments': int(comments) if comments else 0,
            'shares': int(shares) if shares else 0,
            'views': int(views) if views else 0,
            'post_date': post_date
        }


if __name__ == "__main__":
    scraper = TikTokScraper()
    results = scraper.run(
        fetch_by_keywords=True,
        fetch_by_accounts=True,
        max_per_keyword=20,
        max_per_account=10
    )
    print(f"\nResultados totales: {results['totals']}")
