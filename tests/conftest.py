import io
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pikepdf
import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.v1.dependencies import get_current_user
from app.domain.entities.user import User
from app.infrastructure.database.connection import get_db


# ---------------------------------------------------------------------------
# DB mock — evita conexão real com PostgreSQL nos testes
# ---------------------------------------------------------------------------

async def mock_get_db():
    yield MagicMock(spec=AsyncSession)


# ---------------------------------------------------------------------------
# Usuários mock
# ---------------------------------------------------------------------------

def make_mock_user(
    profile_name: str = "file_editor",
    must_change_password: bool = False,
    status: str = "active",
) -> User:
    return User(
        id="00000000-0000-0000-0000-000000000001",
        username="testuser",
        email="test@example.com",
        password_hash="$argon2id$placeholder",
        profile_id="00000000-0000-0000-0000-000000000010",
        profile_name=profile_name,
        status=status,
        must_change_password=must_change_password,
        provisional_password_sent_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )


async def _user_file_editor():
    return make_mock_user("file_editor")


async def _user_must_change():
    return make_mock_user("file_editor", must_change_password=True)


async def _user_airline():
    return make_mock_user("airline_company")


# ---------------------------------------------------------------------------
# Fixtures de client HTTP
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Client autenticado como file_editor (para testes de routers de arquivo)."""
    app.dependency_overrides[get_current_user] = _user_file_editor
    app.dependency_overrides[get_db] = mock_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_must_change():
    """Client autenticado, mas com must_change_password=True."""
    app.dependency_overrides[get_current_user] = _user_must_change
    app.dependency_overrides[get_db] = mock_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """Client sem autenticação (DB mockado para evitar erro de conexão)."""
    app.dependency_overrides[get_db] = mock_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures de arquivos PDF
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_pdf_bytes():
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.add_blank_page(page_size=(612, 792))
    pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    buf.seek(0)
    pdf.close()
    return buf.getvalue()


@pytest.fixture
def sample_pdf_with_text():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Test text for extraction")
    page.insert_text((100, 120), "Second line of text")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def sample_bank_statement_pdf():
    doc = fitz.open()
    page = doc.new_page()
    y = 100
    for date, tipo, desc, valor in [
        ("15/01/2026", "PIX", "Pagamento João", "R$ 150,00"),
        ("16/01/2026", "TED", "Transferência Maria", "-R$ 200,00"),
        ("17/01/2026", "Depósito", "Salário", "R$ 5.000,00"),
    ]:
        page.insert_text((100, y), date)
        page.insert_text((100, y + 15), tipo)
        page.insert_text((100, y + 30), desc)
        page.insert_text((100, y + 45), valor)
        y += 70
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def protected_pdf_bytes():
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(
        buf,
        encryption=pikepdf.Encryption(user="user123", owner="owner123", aes=True, R=6),
    )
    buf.seek(0)
    pdf.close()
    return buf.getvalue()
