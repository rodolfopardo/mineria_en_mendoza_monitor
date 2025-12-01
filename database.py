"""
Base de datos para el Monitor Social de Minería en Mendoza
Almacena publicaciones de Instagram, Facebook, TikTok y Twitter
"""

import sqlite3
import shutil
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


def get_db_path():
    """Obtiene la ruta de la base de datos, copiando a tmp si es necesario para Streamlit Cloud"""
    original_db = os.path.join(os.path.dirname(__file__), "social_monitor.db")

    # En Streamlit Cloud, el filesystem es read-only, copiamos a /tmp
    if os.path.exists("/tmp"):
        tmp_db = "/tmp/social_monitor.db"
        # Copiar la base de datos si no existe en tmp o si el original es más nuevo
        if os.path.exists(original_db):
            try:
                if not os.path.exists(tmp_db) or os.path.getmtime(original_db) > os.path.getmtime(tmp_db):
                    shutil.copy2(original_db, tmp_db)
            except Exception:
                # Si falla la comparación, intentar copiar de todos modos
                try:
                    shutil.copy2(original_db, tmp_db)
                except Exception:
                    pass
        return tmp_db

    return original_db


class SocialDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        self.init_database()

    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla principal de publicaciones (todas las redes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                post_id TEXT NOT NULL,
                post_url TEXT UNIQUE NOT NULL,
                author_username TEXT,
                author_name TEXT,
                author_followers INTEGER DEFAULT 0,
                content TEXT,
                post_type TEXT,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                engagement_total INTEGER DEFAULT 0,
                reach_level TEXT,
                sentiment TEXT,
                has_mobilization_call BOOLEAN DEFAULT 0,
                keywords_matched TEXT,
                post_date TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de cuentas monitoreadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                followers INTEGER DEFAULT 0,
                account_type TEXT,
                is_key_account BOOLEAN DEFAULT 0,
                last_scraped TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, username)
            )
        ''')

        # Tabla de palabras clave de búsqueda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de convocatorias detectadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mobilization_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                event_date TEXT,
                event_location TEXT,
                event_type TEXT,
                description TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')

        # Tabla de narrativas/consignas detectadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS narratives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                narrative_text TEXT NOT NULL,
                category TEXT,
                occurrences INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de reportes generados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date_start DATE NOT NULL,
                report_date_end DATE NOT NULL,
                total_posts INTEGER DEFAULT 0,
                total_interactions INTEGER DEFAULT 0,
                estimated_reach INTEGER DEFAULT 0,
                risk_level TEXT,
                report_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de scraping logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                scrape_type TEXT,
                status TEXT,
                posts_found INTEGER DEFAULT 0,
                posts_new INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        # ========== TABLAS PARA MEDIOS DE COMUNICACIÓN ==========

        # Tabla para Top Stories de minería (Google News destacadas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS top_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                source_logo TEXT,
                date_published TEXT,
                thumbnail TEXT,
                is_live BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla para todas las noticias de minería
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                snippet TEXT,
                date_published TEXT,
                thumbnail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insertar palabras clave por defecto
        default_keywords = [
            ("minería Mendoza", "general"),
            ("minería", "general"),
            ("megaminería", "general"),
            ("7722", "legal"),
            ("ley 7722", "legal"),
            ("San Jorge", "proyecto"),
            ("PSJ", "proyecto"),
            ("Cobre Mendocino", "proyecto"),
            ("no a la mina", "consigna"),
            ("agua Mendoza", "ambiental"),
            ("el agua vale más", "consigna"),
            ("glaciares", "ambiental"),
            ("marcha minería", "movilizacion"),
            ("movilización agua", "movilizacion"),
        ]

        for keyword, category in default_keywords:
            cursor.execute('''
                INSERT OR IGNORE INTO search_keywords (keyword, category)
                VALUES (?, ?)
            ''', (keyword, category))

        # Insertar cuentas clave por defecto
        key_accounts = [
            ("instagram", "marcelo_romano0", "Marcelo Romano", "influencer"),
            ("instagram", "arte.porelagua", "Arte por el Agua", "organizacion"),
            ("instagram", "asamblea.uspallata", "Asamblea Uspallata", "asamblea"),
            ("instagram", "econewses", "Econews ES", "medio"),
            ("instagram", "cuyo.ambiental", "Cuyo Ambiental", "medio"),
            ("facebook", "pibessancarlos", "Pibes Autoconvocados San Carlos", "organizacion"),
            ("tiktok", "marcelo_romano0", "Marcelo Romano", "influencer"),
        ]

        for platform, username, display_name, account_type in key_accounts:
            cursor.execute('''
                INSERT OR IGNORE INTO monitored_accounts
                (platform, username, display_name, account_type, is_key_account)
                VALUES (?, ?, ?, ?, 1)
            ''', (platform, username, display_name, account_type))

        conn.commit()
        conn.close()

    # ========== MÉTODOS PARA POSTS ==========

    def post_exists(self, post_url: str) -> bool:
        """Verifica si un post ya existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM posts WHERE post_url = ?', (post_url,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def insert_post(self, post_data: Dict) -> bool:
        """Inserta un nuevo post"""
        if self.post_exists(post_data.get('post_url', '')):
            return self.update_post(post_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Calcular engagement total
            engagement = (
                post_data.get('likes', 0) +
                post_data.get('comments', 0) +
                post_data.get('shares', 0)
            )

            # Determinar nivel de alcance
            reach_level = self._calculate_reach_level(engagement)

            cursor.execute('''
                INSERT INTO posts (
                    platform, post_id, post_url, author_username, author_name,
                    author_followers, content, post_type, likes, comments, shares,
                    views, engagement_total, reach_level, sentiment,
                    has_mobilization_call, keywords_matched, post_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_data.get('platform'),
                post_data.get('post_id'),
                post_data.get('post_url'),
                post_data.get('author_username'),
                post_data.get('author_name'),
                post_data.get('author_followers', 0),
                post_data.get('content'),
                post_data.get('post_type'),
                post_data.get('likes', 0),
                post_data.get('comments', 0),
                post_data.get('shares', 0),
                post_data.get('views', 0),
                engagement,
                reach_level,
                post_data.get('sentiment'),
                post_data.get('has_mobilization_call', False),
                json.dumps(post_data.get('keywords_matched', [])),
                post_data.get('post_date')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error insertando post: {e}")
            conn.close()
            return False

    def update_post(self, post_data: Dict) -> bool:
        """Actualiza métricas de un post existente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            engagement = (
                post_data.get('likes', 0) +
                post_data.get('comments', 0) +
                post_data.get('shares', 0)
            )
            reach_level = self._calculate_reach_level(engagement)

            cursor.execute('''
                UPDATE posts SET
                    likes = ?, comments = ?, shares = ?, views = ?,
                    engagement_total = ?, reach_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE post_url = ?
            ''', (
                post_data.get('likes', 0),
                post_data.get('comments', 0),
                post_data.get('shares', 0),
                post_data.get('views', 0),
                engagement,
                reach_level,
                post_data.get('post_url')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error actualizando post: {e}")
            conn.close()
            return False

    def _calculate_reach_level(self, engagement: int) -> str:
        """Calcula el nivel de alcance basado en engagement"""
        if engagement >= 5000:
            return "ALTO"
        elif engagement >= 1500:
            return "MEDIO"
        else:
            return "BAJO"

    def get_posts(self, platform: str = None, days: int = 14, limit: int = 100, only_relevant: bool = True, filter_by_post_date: bool = True) -> List[Dict]:
        """Obtiene posts filtrados por plataforma y fecha de publicación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        # Filtro de relevancia (solo posts sobre Mendoza/minería local)
        # Twitter no tiene el campo marcado, así que lo excluimos del filtro
        if only_relevant and platform != 'twitter':
            relevance_filter = "AND (is_mendoza_relevant = 1 OR is_mendoza_relevant IS NULL)"
        else:
            relevance_filter = ""

        # Usar post_date (fecha real del post) en lugar de scraped_at
        date_column = "post_date" if filter_by_post_date else "scraped_at"

        if platform:
            cursor.execute(f'''
                SELECT * FROM posts
                WHERE platform = ? AND {date_column} >= ? {relevance_filter}
                ORDER BY engagement_total DESC
                LIMIT ?
            ''', (platform, date_filter.isoformat(), limit))
        else:
            cursor.execute(f'''
                SELECT * FROM posts
                WHERE {date_column} >= ? {relevance_filter}
                ORDER BY engagement_total DESC
                LIMIT ?
            ''', (date_filter.isoformat(), limit))

        columns = [desc[0] for desc in cursor.description]
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return posts

    def get_top_posts(self, limit: int = 10, only_relevant: bool = True, days: int = 14) -> List[Dict]:
        """Obtiene los posts con mayor engagement (filtrado por fecha de publicación)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        where_clauses = [f"post_date >= '{date_filter.isoformat()}'"]
        if only_relevant:
            # Twitter no tiene el campo marcado, así que lo incluimos siempre
            where_clauses.append("(is_mendoza_relevant = 1 OR is_mendoza_relevant IS NULL OR platform = 'twitter')")

        where_sql = "WHERE " + " AND ".join(where_clauses)

        cursor.execute(f'''
            SELECT * FROM posts
            {where_sql}
            ORDER BY engagement_total DESC
            LIMIT ?
        ''', (limit,))

        columns = [desc[0] for desc in cursor.description]
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return posts

    # ========== MÉTODOS PARA ESTADÍSTICAS ==========

    def get_consolidated_metrics(self, days: int = 14, only_relevant: bool = True) -> Dict:
        """Obtiene métricas consolidadas de todas las redes (filtrado por fecha de publicación)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        # Filtro de relevancia: Twitter no tiene el campo marcado, así que lo excluimos del filtro
        if only_relevant:
            relevance_filter = "AND (is_mendoza_relevant = 1 OR is_mendoza_relevant IS NULL OR platform = 'twitter')"
        else:
            relevance_filter = ""

        # Usar post_date para filtrar por fecha real de publicación
        cursor.execute(f'''
            SELECT
                COUNT(*) as total_posts,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                SUM(shares) as total_shares,
                SUM(views) as total_views,
                SUM(engagement_total) as total_engagement
            FROM posts
            WHERE post_date >= ? {relevance_filter}
        ''', (date_filter.isoformat(),))

        row = cursor.fetchone()

        # Métricas por plataforma
        cursor.execute(f'''
            SELECT
                platform,
                COUNT(*) as posts,
                SUM(likes) as likes,
                SUM(comments) as comments,
                SUM(shares) as shares,
                SUM(engagement_total) as engagement
            FROM posts
            WHERE post_date >= ? {relevance_filter}
            GROUP BY platform
        ''', (date_filter.isoformat(),))

        platforms = {}
        for prow in cursor.fetchall():
            platforms[prow[0]] = {
                'posts': prow[1],
                'likes': prow[2] or 0,
                'comments': prow[3] or 0,
                'shares': prow[4] or 0,
                'engagement': prow[5] or 0
            }

        conn.close()

        return {
            'total_posts': row[0] or 0,
            'total_likes': row[1] or 0,
            'total_comments': row[2] or 0,
            'total_shares': row[3] or 0,
            'total_views': row[4] or 0,
            'total_engagement': row[5] or 0,
            'by_platform': platforms
        }

    def get_reach_distribution(self, days: int = 14) -> Dict:
        """Obtiene distribución de publicaciones por nivel de alcance (por fecha de publicación)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT reach_level, COUNT(*) as count
            FROM posts
            WHERE post_date >= ?
            GROUP BY reach_level
        ''', (date_filter.isoformat(),))

        distribution = {}
        for row in cursor.fetchall():
            distribution[row[0]] = row[1]

        conn.close()
        return distribution

    def get_sentiment_distribution(self, days: int = 14) -> Dict:
        """Obtiene distribución de sentimiento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT sentiment, COUNT(*) as count
            FROM posts
            WHERE scraped_at >= ? AND sentiment IS NOT NULL
            GROUP BY sentiment
        ''', (date_filter.isoformat(),))

        distribution = {}
        for row in cursor.fetchall():
            distribution[row[0]] = row[1]

        conn.close()
        return distribution

    # ========== MÉTODOS PARA KEYWORDS ==========

    def get_active_keywords(self) -> List[Dict]:
        """Obtiene palabras clave activas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT keyword, category FROM search_keywords WHERE is_active = 1
        ''')

        keywords = [{'keyword': row[0], 'category': row[1]} for row in cursor.fetchall()]

        conn.close()
        return keywords

    def add_keyword(self, keyword: str, category: str = "custom") -> bool:
        """Agrega una nueva palabra clave"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO search_keywords (keyword, category)
                VALUES (?, ?)
            ''', (keyword, category))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    # ========== MÉTODOS PARA CUENTAS ==========

    def get_monitored_accounts(self, platform: str = None) -> List[Dict]:
        """Obtiene cuentas monitoreadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if platform:
            cursor.execute('''
                SELECT * FROM monitored_accounts WHERE platform = ?
                ORDER BY is_key_account DESC, followers DESC
            ''', (platform,))
        else:
            cursor.execute('''
                SELECT * FROM monitored_accounts
                ORDER BY is_key_account DESC, followers DESC
            ''')

        columns = [desc[0] for desc in cursor.description]
        accounts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return accounts

    def add_monitored_account(self, platform: str, username: str,
                              display_name: str = None, account_type: str = None,
                              is_key: bool = False) -> bool:
        """Agrega una cuenta para monitorear"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO monitored_accounts
                (platform, username, display_name, account_type, is_key_account)
                VALUES (?, ?, ?, ?, ?)
            ''', (platform, username, display_name, account_type, is_key))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    # ========== MÉTODOS PARA CONVOCATORIAS ==========

    def add_mobilization_call(self, post_id: int, event_date: str = None,
                               location: str = None, event_type: str = None,
                               description: str = None) -> bool:
        """Registra una convocatoria a movilización"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO mobilization_calls
                (post_id, event_date, event_location, event_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (post_id, event_date, location, event_type, description))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    def get_mobilization_calls(self, days: int = 14) -> List[Dict]:
        """Obtiene convocatorias detectadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_filter = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT mc.*, p.post_url, p.platform, p.author_username, p.content
            FROM mobilization_calls mc
            JOIN posts p ON mc.post_id = p.id
            WHERE mc.detected_at >= ?
            ORDER BY mc.event_date ASC
        ''', (date_filter.isoformat(),))

        columns = [desc[0] for desc in cursor.description]
        calls = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return calls

    # ========== MÉTODOS PARA LOGS ==========

    def log_scrape(self, platform: str, scrape_type: str, status: str,
                   posts_found: int = 0, posts_new: int = 0,
                   error_message: str = None) -> None:
        """Registra una operación de scraping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scraping_logs
            (platform, scrape_type, status, posts_found, posts_new, error_message,
             started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (platform, scrape_type, status, posts_found, posts_new, error_message))

        conn.commit()
        conn.close()

    # ========== MÉTODOS PARA MEDIOS DE COMUNICACIÓN ==========

    def article_exists(self, link: str, table: str = 'top_stories') -> bool:
        """Verifica si un artículo ya existe en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE link = ?', (link,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def insert_top_story(self, article: Dict) -> bool:
        """Inserta una Top Story si no existe"""
        if self.article_exists(article.get('link', ''), 'top_stories'):
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO top_stories
                (title, link, source, source_logo, date_published, thumbnail, is_live)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.get('title'),
                article.get('link'),
                article.get('source'),
                article.get('source_logo'),
                article.get('date'),
                article.get('thumbnail'),
                article.get('live', False)
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def insert_news_result(self, article: Dict) -> bool:
        """Inserta un News Result si no existe"""
        if not article.get('link'):
            return False

        if self.article_exists(article['link'], 'news_results'):
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            source_name = None
            if article.get('source'):
                if isinstance(article['source'], dict):
                    source_name = article['source'].get('name')
                else:
                    source_name = article['source']

            cursor.execute('''
                INSERT INTO news_results
                (title, link, source, snippet, date_published, thumbnail)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article.get('title'),
                article.get('link'),
                source_name,
                article.get('snippet'),
                article.get('date'),
                article.get('thumbnail')
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_top_stories_news(self, limit: int = 50) -> List[Dict]:
        """Obtiene las Top Stories más recientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, link, source, source_logo, date_published, thumbnail, is_live, created_at
            FROM top_stories
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        columns = ['title', 'link', 'source', 'source_logo', 'date_published', 'thumbnail', 'is_live', 'created_at']
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return articles

    def get_news_results(self, limit: int = 100) -> List[Dict]:
        """Obtiene los News Results más recientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, link, source, snippet, date_published, thumbnail, created_at
            FROM news_results
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        columns = ['title', 'link', 'source', 'snippet', 'date_published', 'thumbnail', 'created_at']
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return articles

    def get_media_stats(self, table: str = 'top_stories') -> List[Dict]:
        """Obtiene estadísticas de medios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT source, COUNT(*) as count
            FROM {table}
            WHERE source IS NOT NULL
            GROUP BY source
            ORDER BY count DESC
        ''')

        stats = [{'source': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()
        return stats

    def get_article_count(self, table: str = 'top_stories') -> int:
        """Obtiene el número total de artículos almacenados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        conn.close()
        return count


if __name__ == "__main__":
    # Test de la base de datos
    db = SocialDatabase()
    print("Base de datos inicializada correctamente")
    print(f"Keywords activas: {len(db.get_active_keywords())}")
    print(f"Cuentas monitoreadas: {len(db.get_monitored_accounts())}")
