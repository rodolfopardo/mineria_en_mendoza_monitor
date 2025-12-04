#!/usr/bin/env python3
"""
Script para ejecutar el scraping de todas las redes sociales
Uso: python run_scraper.py [--platform PLATFORM] [--keywords-only] [--accounts-only]
"""

import argparse
from datetime import datetime

from scrapers import InstagramScraper, FacebookScraper, TikTokScraper, TwitterScraper
from analysis import ImpactAnalyzer


def run_all_scrapers(platforms=None, fetch_keywords=True, fetch_accounts=True,
                     max_per_keyword=30, max_per_account=15):
    """Ejecuta scrapers para todas las plataformas especificadas"""

    all_scrapers = {
        'instagram': InstagramScraper,
        'facebook': FacebookScraper,
        'tiktok': TikTokScraper,
        'twitter': TwitterScraper
    }

    if platforms is None:
        platforms = list(all_scrapers.keys())

    # Filtrar plataformas válidas
    valid_platforms = [p for p in platforms if p in all_scrapers]
    total_platforms = len(valid_platforms)

    print("\n" + "="*80)
    print("MONITOR SOCIAL - SCRAPING DE REDES SOCIALES")
    print("="*80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Plataformas: {', '.join(platforms)} ({total_platforms} total)")
    print("="*80)

    results = {}

    for i, platform in enumerate(platforms):
        platform_progress = ((i + 1) / total_platforms) * 100 if total_platforms > 0 else 0

        if platform not in all_scrapers:
            print(f"\n[{platform_progress:5.1f}%] Plataforma '{platform}' no reconocida, saltando...")
            continue

        print(f"\n[{platform_progress:5.1f}%] Iniciando scraping de {platform.upper()}...")

        try:
            scraper = all_scrapers[platform]()
            result = scraper.run(
                fetch_by_keywords=fetch_keywords,
                fetch_by_accounts=fetch_accounts,
                max_per_keyword=max_per_keyword,
                max_per_account=max_per_account
            )
            results[platform] = result
            print(f"[{platform_progress:5.1f}%] {platform.upper()} completado")
        except Exception as e:
            print(f"\n[{platform_progress:5.1f}%] Error en {platform}: {e}")
            results[platform] = {'error': str(e)}

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL DE SCRAPING")
    print("="*80)

    total_new = 0
    total_updated = 0

    for platform, result in results.items():
        if 'error' in result:
            print(f"  {platform.upper()}: Error - {result['error']}")
        else:
            new = result.get('totals', {}).get('new', 0)
            updated = result.get('totals', {}).get('updated', 0)
            total_new += new
            total_updated += updated
            print(f"  {platform.upper()}: {new} nuevos, {updated} actualizados")

    print(f"\n  TOTAL: {total_new} posts nuevos, {total_updated} actualizados")
    print("="*80)

    # Generar análisis de impacto
    print("\n📊 Generando análisis de impacto...")
    analyzer = ImpactAnalyzer()
    analyzer.print_report(days=14)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Scraper de redes sociales para Monitor de Minería'
    )

    parser.add_argument(
        '--platform', '-p',
        choices=['instagram', 'facebook', 'tiktok', 'twitter', 'all'],
        default='all',
        help='Plataforma a scrapear (default: all)'
    )

    parser.add_argument(
        '--keywords-only',
        action='store_true',
        help='Solo buscar por palabras clave'
    )

    parser.add_argument(
        '--accounts-only',
        action='store_true',
        help='Solo buscar en cuentas monitoreadas'
    )

    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=30,
        help='Máximo de resultados por búsqueda (default: 30)'
    )

    args = parser.parse_args()

    platforms = None if args.platform == 'all' else [args.platform]

    fetch_keywords = not args.accounts_only
    fetch_accounts = not args.keywords_only

    run_all_scrapers(
        platforms=platforms,
        fetch_keywords=fetch_keywords,
        fetch_accounts=fetch_accounts,
        max_per_keyword=args.max_results,
        max_per_account=args.max_results // 2
    )


if __name__ == "__main__":
    main()
