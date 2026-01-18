import io
import pytest
from fastapi.testclient import TestClient
import pikepdf
import fitz

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def sample_pdf_bytes():
    """Cria um PDF simples em memória para testes"""
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.add_blank_page(page_size=(612, 792))
    pdf.add_blank_page(page_size=(612, 792))
    
    buffer = io.BytesIO()
    pdf.save(buffer)
    buffer.seek(0)
    pdf.close()
    
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_with_text():
    """Cria um PDF com texto para testes de extração"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Texto de teste para extração")
    page.insert_text((100, 120), "Segunda linha de texto")
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    doc.close()
    
    return buffer.getvalue()


@pytest.fixture
def sample_bank_statement_pdf():
    """Cria um PDF simulando extrato bancário formato Zoop"""
    doc = fitz.open()
    page = doc.new_page()
    
    # Simula formato Zoop (4 linhas por transação)
    y = 100
    transactions = [
        ("15/01/2026", "PIX", "Pagamento João", "R$ 150,00"),
        ("16/01/2026", "TED", "Transferência Maria", "-R$ 200,00"),
        ("17/01/2026", "Depósito", "Salário", "R$ 5.000,00"),
    ]
    
    for date, tipo, desc, valor in transactions:
        page.insert_text((100, y), date)
        page.insert_text((100, y + 15), tipo)
        page.insert_text((100, y + 30), desc)
        page.insert_text((100, y + 45), valor)
        y += 70
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    doc.close()
    
    return buffer.getvalue()


@pytest.fixture
def protected_pdf_bytes():
    """Cria um PDF protegido com senha"""
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    
    buffer = io.BytesIO()
    pdf.save(
        buffer,
        encryption=pikepdf.Encryption(
            user="user123",
            owner="owner123",
            aes=True,
            R=6
        )
    )
    buffer.seek(0)
    pdf.close()
    
    return buffer.getvalue()
