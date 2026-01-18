import io
import hashlib
from typing import Optional
from fastapi import UploadFile, HTTPException

# Magic bytes to identify file types
MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06"],
}

# Maximum sizes by type (in bytes)
MAX_SIZES = {
    "pdf": 50 * 1024 * 1024,  # 50MB
    "zip": 100 * 1024 * 1024,  # 100MB
}


def validate_file_type(content: bytes, expected_type: str) -> bool:
    """Validate the actual file type by magic bytes"""
    if expected_type not in MAGIC_BYTES:
        return False
    
    for magic in MAGIC_BYTES[expected_type]:
        if content.startswith(magic):
            return True
    return False


def validate_file_size(content: bytes, file_type: str) -> bool:
    """Validate if file does not exceed maximum size"""
    max_size = MAX_SIZES.get(file_type, 10 * 1024 * 1024)
    return len(content) <= max_size


def get_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file for logging/auditing"""
    return hashlib.sha256(content).hexdigest()[:16]


async def validate_pdf_upload(file: UploadFile, max_size_mb: int = 50) -> bytes:
    """
    Complete PDF upload validation:
    1. Verify extension
    2. Verify size
    3. Verify magic bytes (actual content)
    """
    # 1. Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="File must have .pdf extension"
        )
    
    # 2. Read content
    content = await file.read()
    
    # 3. Validate size
    max_size = max_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {max_size_mb}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    # 4. Validate magic bytes (actual content is PDF)
    if not validate_file_type(content, "pdf"):
        raise HTTPException(
            status_code=400,
            detail="File is not a valid PDF"
        )
    
    return content


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Remove dangerous characters from filename"""
    if not filename:
        return "document"
    
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
