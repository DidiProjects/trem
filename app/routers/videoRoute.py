from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import tempfile
import os
from app.services.videoService import cut_video

router = APIRouter()

def cleanup_files(*paths):
    """Remove arquivos temporários após envio da resposta"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass

@router.post("/cut")
async def movie_cut(
    file: UploadFile = File(...),
    start: float = Form(...),
    end: float = Form(...)
):
    # Validações
    if start < 0:
        raise HTTPException(status_code=400, detail="Tempo inicial deve ser >= 0")
    if end <= start:
        raise HTTPException(status_code=400, detail="Tempo final deve ser maior que o inicial")
    
    # Extensões de vídeo aceitas
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}")
    
    temp_in_path = None
    temp_out_path = None
    
    try:
        # Salvar arquivo de entrada
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_in:
            temp_in.write(await file.read())
            temp_in_path = temp_in.name
        
        # Criar arquivo de saída
        temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_out_path = temp_out.name
        temp_out.close()
        
        # Processar vídeo
        cut_video(temp_in_path, start, end, temp_out_path)
        
        # Gerar nome do arquivo de saída
        original_name = os.path.splitext(file.filename or 'video')[0]
        output_filename = f"{original_name}_recorte.mp4"
        
        return FileResponse(
            temp_out_path,
            filename=output_filename,
            media_type="video/mp4",
            background=BackgroundTask(cleanup_files, temp_in_path, temp_out_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        cleanup_files(temp_in_path, temp_out_path)
        raise HTTPException(status_code=500, detail=f"Erro ao processar vídeo: {str(e)}")
