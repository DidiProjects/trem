import io
import re
import uuid
import zipfile
from datetime import datetime
from typing import List, Literal, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import pikepdf
import fitz
from app.auth import verify_api_key

router = APIRouter()


def safe_filename(filename: str) -> str:
    return quote(filename, safe='')


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


@router.post("/convert-to-image")
async def convert_to_image(
    file: UploadFile = File(...),
    format: Literal["png", "jpeg", "tiff"] = Form("png"),
    dpi: int = Form(150),
    pages: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    """
    Converte PDF para imagens.
    
    - **format**: Formato de saída (png, jpeg, tiff)
    - **dpi**: Resolução da imagem (padrão: 150)
    - **pages**: Páginas a converter (ex: "1,3,5-7"). Se não informado, converte todas.
    
    Retorna um ZIP com as imagens de cada página.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")
    
    if dpi < 72 or dpi > 600:
        raise HTTPException(status_code=400, detail="DPI deve estar entre 72 e 600")
    
    content = await file.read()
    
    try:
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    total_pages = len(pdf)
    
    # Determina quais páginas converter
    if pages:
        page_numbers = parse_page_ranges(pages, total_pages)
    else:
        page_numbers = list(range(1, total_pages + 1))
    
    # Configuração do formato
    format_config = {
        "png": {"ext": "png", "mime": "image/png"},
        "jpeg": {"ext": "jpg", "mime": "image/jpeg"},
        "tiff": {"ext": "tiff", "mime": "image/tiff"}
    }
    
    config = format_config[format]
    zoom = dpi / 72  # 72 é o DPI padrão do PDF
    matrix = fitz.Matrix(zoom, zoom)
    
    # Se for apenas uma página, retorna a imagem diretamente
    if len(page_numbers) == 1:
        page = pdf[page_numbers[0] - 1]
        pix = page.get_pixmap(matrix=matrix)
        
        if format == "jpeg":
            img_bytes = pix.tobytes("jpeg")
        elif format == "tiff":
            img_bytes = pix.tobytes("tiff")
        else:
            img_bytes = pix.tobytes("png")
        
        pdf.close()
        
        output_name = file.filename.rsplit(".", 1)[0] + f"_page_{page_numbers[0]}.{config['ext']}"
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type=config["mime"],
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename(output_name)}"
            }
        )
    
    # Múltiplas páginas: retorna ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for page_num in page_numbers:
            page = pdf[page_num - 1]
            pix = page.get_pixmap(matrix=matrix)
            
            if format == "jpeg":
                img_bytes = pix.tobytes("jpeg")
            elif format == "tiff":
                img_bytes = pix.tobytes("tiff")
            else:
                img_bytes = pix.tobytes("png")
            
            zip_file.writestr(f"page_{page_num}.{config['ext']}", img_bytes)
    
    zip_buffer.seek(0)
    pdf.close()
    
    output_name = file.filename.rsplit(".", 1)[0] + f"-images-{format}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename(output_name)}"
        }
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
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    full_text = ""
    for page in pdf:
        full_text += page.get_text()
    pdf.close()
    
    transactions = extract_transactions_from_text(full_text)
    
    if not transactions:
        raise HTTPException(
            status_code=400, 
            detail="Não foi possível extrair transações do PDF. Verifique se é um extrato bancário válido."
        )
    
    ofx_content = generate_ofx(transactions, bank_id, account_id, account_type)
    
    output_name = file.filename.rsplit(".", 1)[0] + ".ofx"
    return StreamingResponse(
        io.BytesIO(ofx_content.encode("utf-8")),
        media_type="application/x-ofx",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename(output_name)}"
        }
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
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao abrir PDF: {str(e)}")
    
    pages_text = []
    for i, page in enumerate(pdf):
        pages_text.append({
            "page": i + 1,
            "text": page.get_text()
        })
    
    pdf.close()
    
    return {
        "filename": file.filename,
        "total_pages": len(pages_text),
        "pages": pages_text
    }


def extract_transactions_from_text(text: str) -> List[dict]:
    lines = text.split('\n')
    current_year = datetime.now().year
    
    skip_keywords = ['saldo do dia', 'saldo disponível', 'total', 'anterior', 'limite', 
                    'extrato', 'agência', 'conta', 'período', 'cliente', 'cpf', 'cnpj',
                    'solicitado em', 'ifood.com', 'atendimento', 'data movimentação']
    
    transactions = []
    for line in lines:
        line = line.strip()
        if not line or any(kw in line.lower() for kw in skip_keywords):
            continue
        transaction = try_parse_transaction(line, current_year)
        if transaction:
            transactions.append(transaction)
    
    if not transactions:
        transactions = parse_zoop_format(lines, current_year)
    
    return transactions


def parse_zoop_format(lines: List[str], current_year: int) -> List[dict]:
    transactions = []
    clean_lines = [l.strip() for l in lines if l.strip()]
    i = 0
    
    while i < len(clean_lines):
        line = clean_lines[i]
        date_match = re.match(r'^(\d{2}/\d{2}/\d{4})$', line)
        
        if date_match and i + 3 < len(clean_lines):
            date_str = date_match.group(1)
            tipo = clean_lines[i + 1]
            descricao = clean_lines[i + 2]
            valor_line = clean_lines[i + 3]
            
            valor_match = re.match(r'^(-?)R\$\s*([\d.]+,\d{2})$', valor_line)
            
            if valor_match:
                try:
                    date = datetime.strptime(date_str, "%d/%m/%Y")
                    amount_str = valor_match.group(2).replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    if valor_match.group(1) == '-':
                        amount = -amount
                    
                    transactions.append({
                        "date": date,
                        "description": f"{tipo} - {descricao}",
                        "amount": amount
                    })
                    i += 4
                    continue
                except (ValueError, IndexError):
                    pass
        i += 1
    
    return transactions


def try_parse_transaction(line: str, current_year: int) -> Optional[dict]:
    patterns = [
        (r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?)R\$\s*([\d.]+,\d{2})\s*$', '%d/%m/%Y', True),
        (r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+R\$\s*(-?[\d.]+,\d{2})\s*$', '%d/%m/%Y', False),
        (r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d.]+,\d{2})\s*$', '%d/%m/%Y', False),
        (r'^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(-?[\d.]+,\d{2})\s*$', '%d/%m/%y', False),
        (r'^(\d{2}/\d{2})\s+(.+?)\s+(-?[\d.]+,\d{2})\s*$', '%d/%m', False),
        (r'^(\d{4}-\d{2}-\d{2})\s+(.+?)\s+(-?[\d.]+,\d{2})\s*$', '%Y-%m-%d', False),
    ]
    
    for pattern, date_fmt, has_sign in patterns:
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                if date_fmt == '%d/%m':
                    date = datetime.strptime(f"{date_str}/{current_year}", "%d/%m/%Y")
                else:
                    date = datetime.strptime(date_str, date_fmt)
                
                description = match.group(2).strip()
                
                if has_sign:
                    sign = match.group(3)
                    amount_str = match.group(4)
                    amount_str = f"{sign}{amount_str}"
                else:
                    amount_str = match.group(3)
                
                amount_str = amount_str.replace('.', '').replace(',', '.')
                amount = float(amount_str)
                
                if amount == 0:
                    continue
                
                return {"date": date, "description": description, "amount": amount}
            except ValueError:
                continue
    
    return None


def generate_ofx(transactions: List[dict], bank_id: str, account_id: str, account_type: str) -> str:
    now = datetime.now()
    start_date = min(t["date"] for t in transactions) if transactions else now
    end_date = max(t["date"] for t in transactions) if transactions else now
    
    ofx = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>{dtserver}
<LANGUAGE>POR
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>{trnuid}
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<CURDEF>BRL
<BANKACCTFROM>
<BANKID>{bankid}
<ACCTID>{acctid}
<ACCTTYPE>{accttype}
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>{dtstart}
<DTEND>{dtend}
""".format(
        dtserver=now.strftime("%Y%m%d%H%M%S"),
        trnuid=str(uuid.uuid4()).replace("-", "")[:32],
        bankid=bank_id,
        acctid=account_id,
        accttype=account_type,
        dtstart=start_date.strftime("%Y%m%d"),
        dtend=end_date.strftime("%Y%m%d")
    )
    
    for i, trans in enumerate(transactions):
        trntype = "CREDIT" if trans["amount"] >= 0 else "DEBIT"
        ofx += """<STMTTRN>
<TRNTYPE>{trntype}
<DTPOSTED>{dtposted}
<TRNAMT>{amount:.2f}
<FITID>{fitid}
<MEMO>{memo}
</STMTTRN>
""".format(
            trntype=trntype,
            dtposted=trans["date"].strftime("%Y%m%d"),
            amount=trans["amount"],
            fitid=f"{trans['date'].strftime('%Y%m%d')}{i:06d}",
            memo=trans["description"][:255]
        )
    
    balance = sum(t["amount"] for t in transactions)
    
    ofx += """</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>{balance:.2f}
<DTASOF>{dtasof}
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>""".format(balance=balance, dtasof=end_date.strftime("%Y%m%d"))
    
    return ofx


def parse_page_ranges(pages: str, total_pages: int) -> List[int]:
    result = []
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(lambda x: int(x.strip()), part.split("-"))
            if start < 1 or end > total_pages or start > end:
                raise HTTPException(status_code=400, detail=f"Intervalo inválido: {part}")
            result.extend(range(start, end + 1))
        else:
            page = int(part)
            if page < 1 or page > total_pages:
                raise HTTPException(status_code=400, detail=f"Página inválida: {page}")
            result.append(page)
    return sorted(set(result))
