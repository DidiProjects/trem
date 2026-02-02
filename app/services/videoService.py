from moviepy.editor import VideoFileClip

def cut_video(input_path: str, start: float, end: float, output_path: str) -> str:
    """
    Recorta um vídeo entre os tempos start e end (em segundos).
    
    Args:
        input_path: Caminho do arquivo de vídeo de entrada
        start: Tempo inicial em segundos
        end: Tempo final em segundos
        output_path: Caminho do arquivo de saída
    
    Returns:
        Caminho do arquivo de saída
    """
    clip = None
    subclip = None
    try:
        clip = VideoFileClip(input_path)
        
        # Validar que o tempo final não excede a duração do vídeo
        if end > clip.duration:
            end = clip.duration
        
        subclip = clip.subclip(start, end)
        subclip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None  # Suprime logs verbosos
        )
        return output_path
    finally:
        if subclip:
            subclip.close()
        if clip:
            clip.close()
