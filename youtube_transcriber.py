"""
Transcriptor de videos de YouTube
Descarga subtítulos automáticos o transcribe audio con Whisper
"""

import os
import subprocess
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Intentar importar dependencias opcionales
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class YouTubeTranscriber:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(__file__), "transcripts")
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_video_id(self, url: str) -> str:
        """Extrae el ID del video de una URL de YouTube"""
        if "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "/live/" in url:
                return url.split("/live/")[1].split("?")[0]
        return url

    def get_youtube_transcript(self, video_url: str, language: str = 'es') -> Optional[Dict]:
        """Obtiene subtítulos automáticos de YouTube"""
        if not TRANSCRIPT_API_AVAILABLE:
            print("youtube-transcript-api no está instalado")
            print("Instalar con: pip install youtube-transcript-api")
            return None

        video_id = self.extract_video_id(video_url)
        print(f"Obteniendo transcripción para video: {video_id}")

        try:
            # Intentar obtener subtítulos en español
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Buscar subtítulos manuales o automáticos en español
            transcript = None
            try:
                transcript = transcript_list.find_transcript([language])
            except:
                # Si no hay en español, buscar automáticos y traducir
                try:
                    transcript = transcript_list.find_generated_transcript(['es', 'en'])
                except:
                    # Usar el primero disponible
                    for t in transcript_list:
                        transcript = t
                        break

            if transcript:
                transcript_data = transcript.fetch()

                # Formatear transcripción
                full_text = ""
                segments = []

                for entry in transcript_data:
                    start_time = entry['start']
                    duration = entry.get('duration', 0)
                    text = entry['text']

                    # Formato timestamp
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    timestamp = f"{minutes:02d}:{seconds:02d}"

                    segments.append({
                        'timestamp': timestamp,
                        'start': start_time,
                        'duration': duration,
                        'text': text
                    })

                    full_text += f"[{timestamp}] {text}\n"

                return {
                    'video_id': video_id,
                    'video_url': video_url,
                    'language': transcript.language,
                    'is_generated': transcript.is_generated,
                    'segments': segments,
                    'full_text': full_text,
                    'fetched_at': datetime.now().isoformat()
                }

        except Exception as e:
            print(f"Error obteniendo transcripción: {e}")
            return None

    def transcribe_with_whisper(self, video_url: str, model_size: str = "base") -> Optional[Dict]:
        """Descarga audio y transcribe con Whisper"""
        if not WHISPER_AVAILABLE:
            print("Whisper no está instalado")
            print("Instalar con: pip install openai-whisper")
            return None

        video_id = self.extract_video_id(video_url)
        audio_path = os.path.join(self.output_dir, f"{video_id}.mp3")

        # Descargar audio con yt-dlp
        print(f"Descargando audio del video {video_id}...")
        try:
            subprocess.run([
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "-o", audio_path,
                video_url
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Error descargando audio: {e}")
            return None
        except FileNotFoundError:
            print("yt-dlp no está instalado. Instalar con: pip install yt-dlp")
            return None

        # Transcribir con Whisper
        print(f"Transcribiendo con Whisper (modelo: {model_size})...")
        try:
            model = whisper.load_model(model_size)
            result = model.transcribe(audio_path, language="es")

            # Formatear resultado
            segments = []
            full_text = ""

            for segment in result['segments']:
                start_time = segment['start']
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"

                segments.append({
                    'timestamp': timestamp,
                    'start': start_time,
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })

                full_text += f"[{timestamp}] {segment['text'].strip()}\n"

            # Limpiar archivo de audio
            if os.path.exists(audio_path):
                os.remove(audio_path)

            return {
                'video_id': video_id,
                'video_url': video_url,
                'language': result.get('language', 'es'),
                'model': model_size,
                'segments': segments,
                'full_text': full_text,
                'transcribed_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error transcribiendo con Whisper: {e}")
            return None

    def save_transcript(self, transcript: Dict, filename: str = None) -> str:
        """Guarda la transcripción en un archivo"""
        if not filename:
            video_id = transcript.get('video_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"transcript_{video_id}_{timestamp}.txt"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Transcripción de Video de YouTube\n")
            f.write(f"# Video ID: {transcript.get('video_id')}\n")
            f.write(f"# URL: {transcript.get('video_url')}\n")
            f.write(f"# Idioma: {transcript.get('language')}\n")
            f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# {'='*60}\n\n")
            f.write(transcript.get('full_text', ''))

        print(f"Transcripción guardada en: {filepath}")
        return filepath

    def transcribe(self, video_url: str, method: str = "auto") -> Optional[Dict]:
        """
        Transcribe un video de YouTube

        Args:
            video_url: URL del video
            method: "youtube" (subtítulos), "whisper" (IA), "auto" (intenta ambos)

        Returns:
            Dict con la transcripción o None si falla
        """
        print(f"\n{'='*60}")
        print(f"Transcribiendo: {video_url}")
        print(f"Método: {method}")
        print(f"{'='*60}\n")

        transcript = None

        if method in ["youtube", "auto"]:
            print("Intentando obtener subtítulos de YouTube...")
            transcript = self.get_youtube_transcript(video_url)
            if transcript:
                print(f"✓ Subtítulos obtenidos ({len(transcript['segments'])} segmentos)")

        if not transcript and method in ["whisper", "auto"]:
            print("Intentando transcribir con Whisper...")
            transcript = self.transcribe_with_whisper(video_url)
            if transcript:
                print(f"✓ Transcripción con Whisper completada")

        if transcript:
            filepath = self.save_transcript(transcript)
            transcript['saved_to'] = filepath
            return transcript
        else:
            print("✗ No se pudo obtener la transcripción")
            return None


if __name__ == "__main__":
    # URL del live de la Legislatura
    VIDEO_URL = "https://www.youtube.com/live/OvG4zIP7Abc"

    transcriber = YouTubeTranscriber()

    # Verificar dependencias
    print("Dependencias disponibles:")
    print(f"  - youtube-transcript-api: {'✓' if TRANSCRIPT_API_AVAILABLE else '✗'}")
    print(f"  - whisper: {'✓' if WHISPER_AVAILABLE else '✗'}")
    print()

    # Transcribir
    result = transcriber.transcribe(VIDEO_URL, method="auto")

    if result:
        print(f"\n{'='*60}")
        print("TRANSCRIPCIÓN EXITOSA")
        print(f"{'='*60}")
        print(f"Archivo: {result.get('saved_to')}")
        print(f"Segmentos: {len(result.get('segments', []))}")
        print(f"\nPrimeros 500 caracteres:")
        print(result.get('full_text', '')[:500])
