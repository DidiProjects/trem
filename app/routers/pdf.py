import io
import os
import uuid
import zipfile
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import pikepdf
from app.auth import verify_api_key
from app.config import get_settings

router = APIRouter()


def get_output_filename(original: str, operation: str) -> str:
    name = original.rsplit(".", 1)[0]
    return f"{name}-{operation}.pdf"


@router.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    pages: str = Form(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    
    try:
        pdf = pikepdf.open(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    total_pages = len(pdf.pages)
    page_numbers = parse_page_ranges(pages, total_pages)
    
    output_pdf = pikepdf.new()
    for page_num in page_numbers:
        output_pdf.pages.append(pdf.pages[page_num - 1])
    
    output = io.BytesIO()
    output_pdf.save(output)
    output.seek(0)
    
    pdf.close()
    output_pdf.close()
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={get_output_filename(file.filename, 'split')}"}
    )


@router.post("/extract-pages")
async def extract_pages(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    
    try:
        pdf = pikepdf.open(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, page in enumerate(pdf.pages):
            page_pdf = pikepdf.new()
            page_pdf.pages.append(page)
            page_buffer = io.BytesIO()
            page_pdf.save(page_buffer)
            page_buffer.seek(0)
            zip_file.writestr(f"page_{i + 1}.pdf", page_buffer.read())
            page_pdf.close()
    
    zip_buffer.seek(0)
    pdf.close()
    
    output_name = file.filename.rsplit(".", 1)[0] + "-extracted.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={output_name}"}
    )


@router.post("/merge")
async def merge_pdfs(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Forneça pelo menos 2 arquivos PDF")
    
    output_pdf = pikepdf.new()
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Arquivo {file.filename} não é PDF")
        content = await file.read()
        try:
            pdf = pikepdf.open(io.BytesIO(content))
            for page in pdf.pages:
                output_pdf.pages.append(page)
            pdf.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao abrir {file.filename}: {str(e)}")
    
    output = io.BytesIO()
    output_pdf.save(output)
    output.seek(0)
    output_pdf.close()
    
    first_name = files[0].filename.rsplit(".", 1)[0]
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={first_name}-merged.pdf"}
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
    
    try:
        pdf = pikepdf.open(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    output = io.BytesIO()
    pdf.save(
        output,
        encryption=pikepdf.Encryption(
            user=user_password,
            owner=owner_password or user_password,
            aes=True,
            R=6
        )
    )
    output.seek(0)
    pdf.close()
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={get_output_filename(file.filename, 'protected')}"}
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
    
    try:
        pdf = pikepdf.open(io.BytesIO(content), password=password)
    except pikepdf.PasswordError:
        raise HTTPException(status_code=400, detail="Senha incorreta")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    output = io.BytesIO()
    pdf.save(output)
    output.seek(0)
    pdf.close()
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={get_output_filename(file.filename, 'unlocked')}"}
    )


@router.post("/info")
async def pdf_info(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    
    try:
        pdf = pikepdf.open(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    metadata = pdf.docinfo
    
    result = {
        "filename": file.filename,
        "pages": len(pdf.pages),
        "encrypted": pdf.is_encrypted,
        "pdf_version": str(pdf.pdf_version),
        "metadata": {
            "title": str(metadata.get("/Title", "")) if metadata else None,
            "author": str(metadata.get("/Author", "")) if metadata else None,
            "subject": str(metadata.get("/Subject", "")) if metadata else None,
            "creator": str(metadata.get("/Creator", "")) if metadata else None,
            "producer": str(metadata.get("/Producer", "")) if metadata else None,
        }
    }
    
    pdf.close()
    return result


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
