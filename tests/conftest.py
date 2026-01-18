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
    """Creates a simple PDF in memory for tests"""
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
    """Creates a PDF with text for extraction tests"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Test text for extraction")
    page.insert_text((100, 120), "Second line of text")
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    doc.close()
    
    return buffer.getvalue()


@pytest.fixture
def sample_bank_statement_pdf():
    """Creates a PDF simulating bank statement in Zoop format"""
    doc = fitz.open()
    page = doc.new_page()
    
    # Simulates Zoop format (4 lines per transaction)
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
    """Creates a password-protected PDF"""
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
