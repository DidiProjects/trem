import whisper
import os
import tempfile
from moviepy.editor import VideoFileClip

_whisper_model = None

# Extensões suportadas
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma'}
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

# Idiomas suportados
SUPPORTED_LANGUAGES = {'pt', 'en', 'es', 'fr', 'de', 'it', 'ja', 'zh', 'ko', 'ru', 'ar', 'hi', 'nl', 'pl', 'tr'}


class AudioServiceError(Exception):
    """Exceção customizada para erros do serviço de áudio"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def get_whisper_model():
    """Carrega o modelo Whisper de forma lazy"""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def validate_transcription_input(filename: str, language: str = None) -> str:
    """
    Valida os parâmetros de entrada para transcrição.
    
    Args:
        filename: Nome do arquivo
        language: Código do idioma (opcional)
    
    Returns:
        Extensão do arquivo validada
    
    Raises:
        AudioServiceError: Se validação falhar
    """
    if not filename:
        raise AudioServiceError("Nome do arquivo é obrigatório")
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AudioServiceError(
            f"Formato não suportado. Use: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    
    if language and language not in SUPPORTED_LANGUAGES:
        raise AudioServiceError(
            f"Idioma não suportado. Use: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )
    
    return ext


def transcribe(input_path: str, language: str = None) -> dict:
    """
    Transcreve o áudio de um vídeo ou arquivo de áudio.
    Aceita tanto arquivos de vídeo quanto de áudio.
    
    Args:
        input_path: Caminho do arquivo de vídeo/áudio
        language: Código do idioma (pt, en, es, etc.) ou None para auto-detectar
    
    Returns:
        Dicionário com a transcrição completa, segmentos e metadados
    
    Raises:
        AudioServiceError: Se ocorrer erro no processamento
    """
    audio_path = None
    clip = None
    duration = None
    
    try:
        ext = os.path.splitext(input_path)[1].lower()
        
        # Se for vídeo, extrair áudio primeiro
        if ext in VIDEO_EXTENSIONS:
            clip = VideoFileClip(input_path)
            duration = clip.duration
            
            if clip.audio is None:
                raise AudioServiceError("O vídeo não possui trilha de áudio")
            
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            clip.audio.write_audiofile(audio_path, logger=None)
            file_to_transcribe = audio_path
        else:
            file_to_transcribe = input_path
            # Tentar obter duração do áudio
            try:
                import wave
                with wave.open(input_path, 'rb') as audio:
                    duration = audio.getnframes() / audio.getframerate()
            except:
                # Se não for WAV, tenta com moviepy
                try:
                    from moviepy.editor import AudioFileClip
                    audio_clip = AudioFileClip(input_path)
                    duration = audio_clip.duration
                    audio_clip.close()
                except:
                    duration = None
        
        # Carregar modelo e transcrever
        model = get_whisper_model()
        
        options = {}
        if language:
            options['language'] = language
        
        result = model.transcribe(file_to_transcribe, **options)
        
        # Formatar segmentos
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': round(segment['start'], 2),
                'end': round(segment['end'], 2),
                'text': segment['text'].strip()
            })
        
        return {
            'text': result['text'].strip(),
            'segments': segments,
            'language': result.get('language', language),
            'duration': round(duration, 2) if duration else None
        }
    
    except AudioServiceError:
        raise
    except Exception as e:
        raise AudioServiceError(f"Erro ao transcrever: {str(e)}", status_code=500)
    
    finally:
        # Limpar recursos
        if clip:
            clip.close()
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
