"""
Twitter/X Scraper - Scraper para Twitter usando Apify
"""

from apify_client import ApifyClient
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class TwitterScraper(BaseScraper):
    """Scraper para Twitter/X usando Apify"""

    def __init__(self):
        super().__init__(platform="twitter")
        self.client = ApifyClient(self.apify_token)

        # Actors de Apify para Twitter
        # Hay varios disponibles, estos son algunos populares
        self.search_actor = "apidojo/tweet-scraper"
        self.profile_actor = "apidojo/twitter-user-scraper"

        # Alternativas si los anteriores no funcionan
        self.alt_search_actor = "quacker/twitter-scraper"
        self.alt_profile_actor = "microworlds/twitter-scraper"

    def fetch_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Busca tweets por palabra clave"""

        # Agregar filtro de ubicación si es sobre Mendoza
        search_query = keyword
        if "mendoza" not in keyword.lower():
            search_query = f"{keyword} Mendoza"

        run_input = {
            "searchTerms": [search_query],
            "maxTweets": max_results,
            "sort": "Latest",  # Tweets más recientes
            "tweetLanguage": "es",
        }

        try:
            print(f"      Ejecutando Apify actor para búsqueda: '{search_query}'")

            run = self.client.actor(self.search_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} tweets")
            return posts

        except Exception as e:
            print(f"      -> Error en actor principal, intentando alternativo...")
            return self._fetch_by_keyword_alt(search_query, max_results)

    def _fetch_by_keyword_alt(self, keyword: str, max_results: int) -> List[Dict]:
        """Búsqueda alternativa si el actor principal falla"""

        run_input = {
            "searchTerms": [keyword],
            "maxItems": max_results,
            "sort": "Latest",
        }

        try:
            run = self.client.actor(self.alt_search_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} tweets (actor alternativo)")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def fetch_by_account(self, username: str, max_results: int = 20) -> List[Dict]:
        """Obtiene tweets de un usuario específico"""

        # Limpiar username
        username = username.replace("@", "")

        run_input = {
            "handle": [username],
            "maxTweets": max_results,
            "mode": "user",
        }

        try:
            print(f"      Ejecutando Apify actor para usuario: @{username}")

            run = self.client.actor(self.profile_actor).call(run_input=run_input)

            posts = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                posts.append(item)

            print(f"      -> Obtenidos {len(posts)} tweets")
            return posts

        except Exception as e:
            print(f"      -> Error en Apify: {e}")
            return []

    def parse_post(self, raw_data: Dict) -> Dict:
        """Parsea datos de Twitter a formato estándar"""

        # ID y URL del tweet
        tweet_id = raw_data.get('id') or raw_data.get('id_str') or raw_data.get('tweetId')

        # URL del tweet
        post_url = raw_data.get('url') or raw_data.get('tweetUrl')
        if not post_url and tweet_id:
            author = raw_data.get('user', {}).get('screen_name', '')
            if author:
                post_url = f"https://twitter.com/{author}/status/{tweet_id}"
            else:
                post_url = f"https://twitter.com/i/status/{tweet_id}"

        # Información del autor
        user = raw_data.get('user', {})
        if isinstance(user, dict):
            author_username = user.get('screen_name') or user.get('username', '')
            author_name = user.get('name', '')
            author_followers = user.get('followers_count') or user.get('followersCount', 0)
        else:
            author_username = raw_data.get('author', {}).get('userName', '')
            author_name = raw_data.get('author', {}).get('displayName', '')
            author_followers = raw_data.get('author', {}).get('followers', 0)

        # Contenido
        content = (
            raw_data.get('full_text') or
            raw_data.get('text') or
            raw_data.get('tweetText') or
            ''
        )

        # Métricas
        likes = (
            raw_data.get('favorite_count') or
            raw_data.get('likeCount') or
            raw_data.get('likes', 0)
        )

        comments = (
            raw_data.get('reply_count') or
            raw_data.get('replyCount') or
            raw_data.get('replies', 0)
        )

        shares = (
            raw_data.get('retweet_count') or
            raw_data.get('retweetCount') or
            raw_data.get('retweets', 0)
        )

        views = (
            raw_data.get('views') or
            raw_data.get('viewCount') or
            raw_data.get('impressions', 0)
        )

        # Tipo de contenido
        post_type = 'tweet'
        if raw_data.get('entities', {}).get('media'):
            media = raw_data['entities']['media']
            if isinstance(media, list) and len(media) > 0:
                media_type = media[0].get('type', '')
                if media_type == 'video':
                    post_type = 'video'
                elif media_type == 'photo':
                    post_type = 'image'

        # Fecha
        timestamp = raw_data.get('created_at') or raw_data.get('createdAt') or raw_data.get('timestamp')
        if timestamp:
            if isinstance(timestamp, (int, float)):
                post_date = datetime.fromtimestamp(timestamp).isoformat()
            elif isinstance(timestamp, str):
                # Twitter usa formato específico
                try:
                    # Formato: "Wed Oct 10 20:19:24 +0000 2018"
                    post_date = datetime.strptime(
                        timestamp, "%a %b %d %H:%M:%S +0000 %Y"
                    ).isoformat()
                except:
                    post_date = timestamp
            else:
                post_date = None
        else:
            post_date = None

        return {
            'platform': 'twitter',
            'post_id': str(tweet_id) if tweet_id else None,
            'post_url': post_url,
            'author_username': author_username,
            'author_name': author_name,
            'author_followers': int(author_followers) if author_followers else 0,
            'content': content,
            'post_type': post_type,
            'likes': int(likes) if likes else 0,
            'comments': int(comments) if comments else 0,
            'shares': int(shares) if shares else 0,
            'views': int(views) if views else 0,
            'post_date': post_date
        }


if __name__ == "__main__":
    scraper = TwitterScraper()
    results = scraper.run(
        fetch_by_keywords=True,
        fetch_by_accounts=True,
        max_per_keyword=20,
        max_per_account=10
    )
    print(f"\nResultados totales: {results['totals']}")
