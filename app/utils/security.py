import io
import hashlib
from typing import Optional
from fastapi import UploadFile, HTTPException

# Magic bytes para identificar tipos de arquivo
MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06"],
}

# Tamanhos máximos por tipo (em bytes)
MAX_SIZES = {
    "pdf": 50 * 1024 * 1024,  # 50MB
    "zip": 100 * 1024 * 1024,  # 100MB
}


def validate_file_type(content: bytes, expected_type: str) -> bool:
    """Valida o tipo real do arquivo pelos magic bytes"""
    if expected_type not in MAGIC_BYTES:
        return False
    
    for magic in MAGIC_BYTES[expected_type]:
        if content.startswith(magic):
            return True
    return False


def validate_file_size(content: bytes, file_type: str) -> bool:
    """Valida se o arquivo não excede o tamanho máximo"""
    max_size = MAX_SIZES.get(file_type, 10 * 1024 * 1024)
    return len(content) <= max_size


def get_file_hash(content: bytes) -> str:
    """Gera hash SHA-256 do arquivo para logging/auditoria"""
    return hashlib.sha256(content).hexdigest()[:16]


async def validate_pdf_upload(file: UploadFile, max_size_mb: int = 50) -> bytes:
    """
    Validação completa de upload de PDF:
    1. Verifica extensão
    2. Verifica tamanho
    3. Verifica magic bytes (conteúdo real)
    """
    # 1. Validar extensão
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="Arquivo deve ter extensão .pdf"
        )
    
    # 2. Ler conteúdo
    content = await file.read()
    
    # 3. Validar tamanho
    max_size = max_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o tamanho máximo de {max_size_mb}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Arquivo está vazio"
        )
    
    # 4. Validar magic bytes (conteúdo real é PDF)
    if not validate_file_type(content, "pdf"):
        raise HTTPException(
            status_code=400,
            detail="Arquivo não é um PDF válido"
        )
    
    return content


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Remove caracteres perigosos do nome do arquivo"""
    if not filename:
        return "documento"
    
    # Remove path traversal
    filename = filename.replace("\\", "/").split("/")[-1]
    
    # Remove caracteres perigosos
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limita tamanho
    if len(filename) > max_length:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:max_length - len(ext) - 1] + "." + ext
    
    return filename
