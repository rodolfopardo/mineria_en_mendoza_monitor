"""
Impact Analyzer - Análisis de impacto y evaluación de riesgo
Genera métricas consolidadas y evaluaciones de riesgo sociopolítico
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import Counter
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SocialDatabase


class ImpactAnalyzer:
    """Analizador de impacto y riesgo para publicaciones de redes sociales"""

    def __init__(self):
        self.db = SocialDatabase()

        # Factores de conversión para estimar alcance
        self.reach_multipliers = {
            'likes': 2,      # Cada like = 2 personas alcanzadas (promedio)
            'comments': 5,   # Cada comentario = 5 personas alcanzadas
            'shares': 50,    # Cada share = 50 personas alcanzadas
            'views': 1,      # Cada vista = 1 persona alcanzada
        }

        # Umbrales para clasificación de alcance
        self.reach_thresholds = {
            'alto': 5000,
            'medio': 1500,
            'bajo': 0
        }

        # Umbrales para evaluación de riesgo
        self.risk_thresholds = {
            'alto': {
                'engagement_total': 50000,
                'mobilization_posts': 5,
                'high_reach_posts': 3,
            },
            'medio': {
                'engagement_total': 20000,
                'mobilization_posts': 2,
                'high_reach_posts': 1,
            },
            'bajo': {
                'engagement_total': 0,
                'mobilization_posts': 0,
                'high_reach_posts': 0,
            }
        }

    def estimate_reach(self, post: Dict) -> int:
        """Estima el alcance de una publicación"""
        reach = 0
        reach += post.get('likes', 0) * self.reach_multipliers['likes']
        reach += post.get('comments', 0) * self.reach_multipliers['comments']
        reach += post.get('shares', 0) * self.reach_multipliers['shares']
        reach += post.get('views', 0) * self.reach_multipliers['views']
        return reach

    def calculate_total_reach(self, posts: List[Dict]) -> int:
        """Calcula el alcance total estimado de todas las publicaciones"""
        total = sum(self.estimate_reach(post) for post in posts)
        return total

    def get_consolidated_metrics(self, days: int = 14) -> Dict:
        """Obtiene métricas consolidadas del período"""
        metrics = self.db.get_consolidated_metrics(days=days)
        posts = self.db.get_posts(days=days, limit=500)

        # Calcular alcance estimado
        estimated_reach = self.calculate_total_reach(posts)

        # Contar posts por nivel de alcance
        reach_distribution = self.db.get_reach_distribution(days=days)

        # Posts con convocatoria a movilización
        mobilization_posts = sum(
            1 for p in posts if p.get('has_mobilization_call')
        )

        return {
            'period_days': days,
            'total_posts': metrics['total_posts'],
            'total_likes': metrics['total_likes'],
            'total_comments': metrics['total_comments'],
            'total_shares': metrics['total_shares'],
            'total_views': metrics['total_views'],
            'total_engagement': metrics['total_engagement'],
            'estimated_reach': estimated_reach,
            'reach_distribution': reach_distribution,
            'mobilization_posts': mobilization_posts,
            'by_platform': metrics['by_platform'],
            'posts_high_reach': reach_distribution.get('ALTO', 0),
            'posts_medium_reach': reach_distribution.get('MEDIO', 0),
            'posts_low_reach': reach_distribution.get('BAJO', 0),
        }

    def evaluate_risk(self, days: int = 14) -> Dict:
        """Evalúa el nivel de riesgo sociopolítico"""
        metrics = self.get_consolidated_metrics(days=days)

        # Obtener convocatorias detectadas
        mobilization_calls = self.db.get_mobilization_calls(days=days)

        # Evaluar factores de riesgo
        risk_factors = []
        risk_score = 0

        # Factor 1: Engagement total
        if metrics['total_engagement'] >= self.risk_thresholds['alto']['engagement_total']:
            risk_factors.append(("Engagement muy alto", 3))
            risk_score += 3
        elif metrics['total_engagement'] >= self.risk_thresholds['medio']['engagement_total']:
            risk_factors.append(("Engagement elevado", 2))
            risk_score += 2
        else:
            risk_factors.append(("Engagement moderado", 1))
            risk_score += 1

        # Factor 2: Posts de alto alcance
        high_reach = metrics.get('posts_high_reach', 0)
        if high_reach >= self.risk_thresholds['alto']['high_reach_posts']:
            risk_factors.append(("Múltiples publicaciones virales", 3))
            risk_score += 3
        elif high_reach >= self.risk_thresholds['medio']['high_reach_posts']:
            risk_factors.append(("Publicaciones con alto alcance", 2))
            risk_score += 2
        else:
            risk_factors.append(("Alcance limitado", 1))
            risk_score += 1

        # Factor 3: Convocatorias a movilización
        mobilization_count = len(mobilization_calls)
        if mobilization_count >= self.risk_thresholds['alto']['mobilization_posts']:
            risk_factors.append(("Múltiples convocatorias activas", 3))
            risk_score += 3
        elif mobilization_count >= self.risk_thresholds['medio']['mobilization_posts']:
            risk_factors.append(("Convocatorias detectadas", 2))
            risk_score += 2
        else:
            risk_factors.append(("Sin convocatorias significativas", 1))
            risk_score += 1

        # Factor 4: Tendencia temporal
        # Comparar última semana vs semana anterior
        recent_posts = self.db.get_posts(days=7, limit=500)
        older_posts = [p for p in self.db.get_posts(days=14, limit=500)
                       if p not in recent_posts]

        recent_engagement = sum(p.get('engagement_total', 0) for p in recent_posts)
        older_engagement = sum(p.get('engagement_total', 0) for p in older_posts)

        if older_engagement > 0:
            growth_rate = (recent_engagement - older_engagement) / older_engagement
            if growth_rate > 0.5:  # >50% de crecimiento
                risk_factors.append(("Tendencia en aumento significativo", 3))
                risk_score += 3
            elif growth_rate > 0.2:  # >20% de crecimiento
                risk_factors.append(("Tendencia en aumento", 2))
                risk_score += 2
            else:
                risk_factors.append(("Tendencia estable", 1))
                risk_score += 1
        else:
            risk_factors.append(("Sin datos históricos", 1))
            risk_score += 1

        # Determinar nivel de riesgo final
        max_score = 12  # 4 factores * 3 puntos máx
        risk_percentage = (risk_score / max_score) * 100

        if risk_percentage >= 70:
            risk_level = "ALTO"
            risk_description = "Alta actividad digital con potencial de escalamiento social significativo"
        elif risk_percentage >= 40:
            risk_level = "MEDIO"
            risk_description = "Actividad moderada dentro de patrones habituales del ecosistema ambientalista"
        else:
            risk_level = "BAJO"
            risk_description = "Actividad limitada sin indicios de escalamiento inusual"

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_percentage': round(risk_percentage, 1),
            'risk_description': risk_description,
            'risk_factors': risk_factors,
            'mobilization_calls': mobilization_calls,
            'metrics': metrics
        }

    def analyze_narratives(self, days: int = 14) -> Dict:
        """Analiza las narrativas predominantes"""
        posts = self.db.get_posts(days=days, limit=500)

        # Narrativas conocidas y su frecuencia
        known_narratives = {
            "El agua vale más que el oro": 0,
            "El agua de Mendoza no se negocia": 0,
            "No a San Jorge": 0,
            "La 7722 no se toca": 0,
            "El agua es vida": 0,
            "Mendoza es hija del agua": 0,
            "La megaminería es saqueo": 0,
            "No a la mina": 0,
            "La 7722 se defiende en la calle": 0,
        }

        # Categorías de narrativa
        categories = {
            "anti_minera_tradicional": [],
            "tecnico_ambiental": [],
            "movilizacion": [],
            "otros": []
        }

        # Palabras frecuentes (para nube de palabras)
        word_counter = Counter()

        stop_words = set([
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no',
            'por', 'con', 'para', 'una', 'los', 'las', 'del', 'al', 'su',
            'más', 'pero', 'como', 'ya', 'o', 'este', 'esta', 'sin', 'sobre',
            'ser', 'son', 'muy', 'hasta', 'hay', 'donde', 'vez', 'puede',
            'todos', 'así', 'nos', 'ni', 'si', 'porque', 'qué', 'cuando',
            'https', 'http', 'www', 'com', 'instagram', 'facebook', 'tiktok'
        ])

        for post in posts:
            content = (post.get('content') or '').lower()

            # Contar narrativas conocidas
            for narrative in known_narratives:
                if narrative.lower() in content:
                    known_narratives[narrative] += 1

            # Categorizar contenido
            if any(kw in content for kw in ['agua vale', 'no se negocia', 'no a la mina']):
                categories["anti_minera_tradicional"].append(post)
            elif any(kw in content for kw in ['dia', 'hidrogeol', 'principio precautorio', 'legal']):
                categories["tecnico_ambiental"].append(post)
            elif any(kw in content for kw in ['marcha', 'moviliza', 'convocatoria', 'calle']):
                categories["movilizacion"].append(post)
            else:
                categories["otros"].append(post)

            # Contar palabras
            words = content.split()
            for word in words:
                word = word.strip('.,!?¿¡"\'()[]{}')
                if len(word) > 3 and word not in stop_words:
                    word_counter[word] += 1

        # Ordenar narrativas por frecuencia
        sorted_narratives = sorted(
            known_narratives.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            'narratives': sorted_narratives,
            'top_narratives': [n for n, c in sorted_narratives if c > 0][:5],
            'categories': {
                k: len(v) for k, v in categories.items()
            },
            'word_frequency': word_counter.most_common(50),
            'total_posts_analyzed': len(posts)
        }

    def get_top_accounts(self, days: int = 14, limit: int = 10) -> List[Dict]:
        """Obtiene las cuentas con mayor impacto"""
        posts = self.db.get_posts(days=days, limit=500)

        # Agrupar por cuenta
        accounts = {}
        for post in posts:
            username = post.get('author_username')
            if not username:
                continue

            if username not in accounts:
                accounts[username] = {
                    'username': username,
                    'platform': post.get('platform'),
                    'posts': 0,
                    'total_engagement': 0,
                    'total_reach': 0,
                    'followers': post.get('author_followers', 0)
                }

            accounts[username]['posts'] += 1
            accounts[username]['total_engagement'] += post.get('engagement_total', 0)
            accounts[username]['total_reach'] += self.estimate_reach(post)

        # Ordenar por engagement
        sorted_accounts = sorted(
            accounts.values(),
            key=lambda x: x['total_engagement'],
            reverse=True
        )

        return sorted_accounts[:limit]

    def generate_full_report(self, days: int = 14) -> Dict:
        """Genera un reporte completo de análisis"""
        risk_analysis = self.evaluate_risk(days=days)
        narrative_analysis = self.analyze_narratives(days=days)
        top_accounts = self.get_top_accounts(days=days)
        top_posts = self.db.get_top_posts(limit=10, days=days)

        return {
            'report_date': datetime.now().isoformat(),
            'period': {
                'days': days,
                'start': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            },
            'risk_evaluation': risk_analysis,
            'narrative_analysis': narrative_analysis,
            'top_accounts': top_accounts,
            'top_posts': top_posts,
            'summary': {
                'total_posts': risk_analysis['metrics']['total_posts'],
                'total_engagement': risk_analysis['metrics']['total_engagement'],
                'estimated_reach': risk_analysis['metrics']['estimated_reach'],
                'risk_level': risk_analysis['risk_level'],
                'mobilization_detected': len(risk_analysis['mobilization_calls']) > 0
            }
        }

    def print_report(self, days: int = 14):
        """Imprime un reporte en consola"""
        report = self.generate_full_report(days=days)

        print("\n" + "="*80)
        print("INFORME DE ANÁLISIS DE REDES SOCIALES - MINERÍA MENDOZA")
        print("="*80)
        print(f"\nPeríodo: {report['period']['start']} a {report['period']['end']}")

        # Resumen ejecutivo
        print("\n" + "-"*80)
        print("RESUMEN EJECUTIVO")
        print("-"*80)
        print(f"Total publicaciones: {report['summary']['total_posts']}")
        print(f"Total interacciones: {report['summary']['total_engagement']:,}")
        print(f"Alcance estimado: {report['summary']['estimated_reach']:,} personas")
        print(f"Nivel de riesgo: {report['summary']['risk_level']}")

        # Evaluación de riesgo
        print("\n" + "-"*80)
        print("EVALUACIÓN DE RIESGO")
        print("-"*80)
        print(f"Nivel: {report['risk_evaluation']['risk_level']}")
        print(f"Score: {report['risk_evaluation']['risk_score']}/12 ({report['risk_evaluation']['risk_percentage']}%)")
        print(f"\n{report['risk_evaluation']['risk_description']}")
        print("\nFactores evaluados:")
        for factor, score in report['risk_evaluation']['risk_factors']:
            print(f"  - {factor}: {score}/3")

        # Narrativas
        print("\n" + "-"*80)
        print("PRINCIPALES NARRATIVAS")
        print("-"*80)
        for narrative, count in report['narrative_analysis']['narratives'][:5]:
            if count > 0:
                print(f"  - \"{narrative}\": {count} menciones")

        # Top cuentas
        print("\n" + "-"*80)
        print("CUENTAS CON MAYOR IMPACTO")
        print("-"*80)
        for i, account in enumerate(report['top_accounts'][:5], 1):
            print(f"  {i}. @{account['username']} ({account['platform']})")
            print(f"     Posts: {account['posts']} | Engagement: {account['total_engagement']:,}")

        # Convocatorias
        if report['risk_evaluation']['mobilization_calls']:
            print("\n" + "-"*80)
            print("CONVOCATORIAS DETECTADAS")
            print("-"*80)
            for call in report['risk_evaluation']['mobilization_calls'][:3]:
                print(f"  - Fecha: {call.get('event_date', 'No especificada')}")
                print(f"    Plataforma: {call.get('platform', 'N/A')}")

        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    analyzer = ImpactAnalyzer()
    analyzer.print_report(days=14)
