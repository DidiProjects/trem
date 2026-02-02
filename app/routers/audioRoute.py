from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from app.services.audioService import (
    transcribe,
    validate_transcription_input,
    AudioServiceError
)

router = APIRouter()


def cleanup_files(*paths):
    """Remove arquivos temporários"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


@router.post("/transcribe")
async def audio_transcribe(
    file: UploadFile = File(...),
    language: str = Form(None)
):
    """
    Transcreve o áudio de um arquivo de vídeo ou áudio.
    Retorna um JSON com a transcrição completa e segmentos com timestamps.
    """
    temp_path = None
    
    try:
        # Validações no service
        ext = validate_transcription_input(file.filename, language)
        
        # Salvar arquivo de entrada
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        # Transcrever
        result = transcribe(temp_path, language)
        
        return JSONResponse(content=result)
    
    except AudioServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    finally:
        cleanup_files(temp_path)
