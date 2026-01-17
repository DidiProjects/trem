import io
import os
import uuid
import zipfile
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from app.auth import verify_api_key
from app.config import get_settings

router = APIRouter()


@router.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    pages: str = Form(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    total_pages = len(reader.pages)
    
    page_numbers = parse_page_ranges(pages, total_pages)
    
    writer = PdfWriter()
    for page_num in page_numbers:
        writer.add_page(reader.pages[page_num - 1])
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=split_{file.filename}"}
    )


@router.post("/extract-pages")
async def extract_pages(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            page_buffer = io.BytesIO()
            writer.write(page_buffer)
            page_buffer.seek(0)
            zip_file.writestr(f"page_{i + 1}.pdf", page_buffer.read())
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={file.filename.replace('.pdf', '_pages.zip')}"}
    )


@router.post("/merge")
async def merge_pdfs(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Forneça pelo menos 2 arquivos PDF")
    
    writer = PdfWriter()
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Arquivo {file.filename} não é PDF")
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=merged.pdf"}
    )


@router.post("/add-password")
async def add_password(
    file: UploadFile = File(...),
    user_password: str = Form(...),
    owner_password: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password or user_password,
        algorithm="AES-256"
    )
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=protected_{file.filename}"}
    )


@router.post("/remove-password")
async def remove_password(
    file: UploadFile = File(...),
    password: str = Form(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    
    if reader.is_encrypted:
        try:
            reader.decrypt(password)
        except Exception:
            raise HTTPException(status_code=400, detail="Senha incorreta")
    
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=unlocked_{file.filename}"}
    )


@router.post("/info")
async def pdf_info(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    
    metadata = reader.metadata
    
    return {
        "filename": file.filename,
        "pages": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "metadata": {
            "title": metadata.title if metadata else None,
            "author": metadata.author if metadata else None,
            "subject": metadata.subject if metadata else None,
            "creator": metadata.creator if metadata else None,
            "producer": metadata.producer if metadata else None,
        }
    }


def parse_page_ranges(pages: str, total_pages: int) -> List[int]:
    result = []
    parts = pages.split(",")
    
    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start = int(start.strip())
            end = int(end.strip())
            if start < 1 or end > total_pages or start > end:
                raise HTTPException(status_code=400, detail=f"Intervalo inválido: {part}")
            result.extend(range(start, end + 1))
        else:
            page = int(part)
            if page < 1 or page > total_pages:
                raise HTTPException(status_code=400, detail=f"Página inválida: {page}")
            result.append(page)
    
    return sorted(set(result))
