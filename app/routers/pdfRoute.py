import io
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import pikepdf
from app.auth import verify_api_key
from app.services import PdfService
from app.utils import safe_filename, get_output_filename

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
    
    try:
        output, _ = PdfService.split(content, pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(get_output_filename(file.filename, 'split'))}"}
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
        zip_buffer = PdfService.extract_pages(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    output_name = file.filename.rsplit(".", 1)[0] + "-extracted.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(output_name)}"}
    )


@router.post("/merge")
async def merge_pdfs(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Forneça pelo menos 2 arquivos PDF")
    
    contents = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Arquivo {file.filename} não é PDF")
        content = await file.read()
        contents.append((file.filename, content))
    
    try:
        output = PdfService.merge(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    first_name = files[0].filename.rsplit(".", 1)[0]
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(first_name + '-merged.pdf')}"}
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
        output = PdfService.add_password(content, user_password, owner_password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(get_output_filename(file.filename, 'protected'))}"}
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
        output = PdfService.remove_password(content, password)
    except pikepdf.PasswordError:
        raise HTTPException(status_code=400, detail="Senha incorreta")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(get_output_filename(file.filename, 'unlocked'))}"}
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
        return PdfService.get_info(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")


@router.post("/convert-to-image")
async def convert_to_image(
    file: UploadFile = File(...),
    format: Literal["png", "jpeg", "tiff"] = Form("png"),
    dpi: int = Form(150),
    pages: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    if dpi < 72 or dpi > 600:
        raise HTTPException(status_code=400, detail="DPI deve estar entre 72 e 600")
    
    content = await file.read()
    
    try:
        buffer, ext, is_single, page_num, mime_type = PdfService.convert_to_image(content, format, dpi, pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    if is_single:
        output_name = file.filename.rsplit(".", 1)[0] + f"_page_{page_num}.{ext}"
    else:
        output_name = file.filename.rsplit(".", 1)[0] + f"-images-{format}.zip"
    
    return StreamingResponse(
        buffer,
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={safe_filename(output_name)}"}
    )


@router.post("/convert-to-ofx")
async def convert_to_ofx(
    file: UploadFile = File(...),
    bank_id: str = Form("0000"),
    account_id: str = Form("0000000000"),
    account_type: Literal["CHECKING", "SAVINGS", "CREDITCARD"] = Form("CHECKING"),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    
    try:
        ofx_content = PdfService.convert_to_ofx(content, bank_id, account_id, account_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    if not ofx_content:
        raise HTTPException(
            status_code=400, 
            detail="Não foi possível extrair transações do PDF. Verifique se é um extrato bancário válido."
        )
    
    output_name = file.filename.rsplit(".", 1)[0] + ".ofx"
    return StreamingResponse(
        io.BytesIO(ofx_content.encode("utf-8")),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={safe_filename(output_name)}"}
    )


@router.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    content = await file.read()
    
    try:
        pages_text = PdfService.extract_text(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    
    return {
        "filename": file.filename,
        "total_pages": len(pages_text),
        "pages": pages_text
    }
