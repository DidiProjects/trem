import io
import pytest

from app.main import app
from app.auth import verify_api_key
from fastapi.testclient import TestClient


async def mock_verify_api_key():
    return "test-api-key"


@pytest.fixture
def client():
    app.dependency_overrides[verify_api_key] = mock_verify_api_key
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    app.dependency_overrides.clear()
    return TestClient(app)


class TestPdfRoutesSplit:
    def test_split_pdf_success(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/split",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"pages": "1"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_split_pdf_invalid_file(self, client):
        response = client.post(
            "/pdf/split",
            files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
            data={"pages": "1"}
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]


class TestPdfRoutesExtractPages:
    def test_extract_pages_success(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/extract-pages",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"


class TestPdfRoutesMerge:
    def test_merge_pdfs_success(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/merge",
            files=[
                ("files", ("doc1.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")),
                ("files", ("doc2.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")),
            ]
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_merge_single_file_fails(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/merge",
            files=[("files", ("doc1.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))]
        )
        
        assert response.status_code == 400
        assert "pelo menos 2" in response.json()["detail"]


class TestPdfRoutesPassword:
    def test_add_password_success(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/add-password",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"user_password": "senha123"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_remove_password_success(self, client, protected_pdf_bytes):
        response = client.post(
            "/pdf/remove-password",
            files={"file": ("protected.pdf", io.BytesIO(protected_pdf_bytes), "application/pdf")},
            data={"password": "user123"}
        )
        
        assert response.status_code == 200
    
    def test_remove_password_wrong_password(self, client, protected_pdf_bytes):
        response = client.post(
            "/pdf/remove-password",
            files={"file": ("protected.pdf", io.BytesIO(protected_pdf_bytes), "application/pdf")},
            data={"password": "wrong"}
        )
        
        assert response.status_code == 400


class TestPdfRoutesInfo:
    def test_info_success(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/info",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["pages"] == 3
        assert "metadata" in data


class TestPdfRoutesConvertToImage:
    def test_convert_to_png(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/convert-to-image",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"format": "png", "dpi": "150", "pages": "1"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    
    def test_convert_to_jpeg(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/convert-to-image",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"format": "jpeg", "dpi": "150", "pages": "1"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
    
    def test_convert_multiple_pages_returns_zip(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/convert-to-image",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"format": "png", "dpi": "150"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
    
    def test_convert_invalid_dpi(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/convert-to-image",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"format": "png", "dpi": "1000"}
        )
        
        assert response.status_code == 400
        assert "DPI" in response.json()["detail"]


class TestPdfRoutesConvertToOfx:
    def test_convert_to_ofx_no_transactions(self, client, sample_pdf_bytes):
        response = client.post(
            "/pdf/convert-to-ofx",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            data={"bank_id": "032", "account_id": "123456", "account_type": "CHECKING"}
        )
        
        assert response.status_code == 400
        assert "extrair transações" in response.json()["detail"]


class TestPdfRoutesExtractText:
    def test_extract_text_success(self, client, sample_pdf_with_text):
        response = client.post(
            "/pdf/extract-text",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_with_text), "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["total_pages"] == 1
        assert "pages" in data


class TestPdfRoutesAuth:
    def test_missing_api_key(self, client_no_auth, sample_pdf_bytes):
        response = client_no_auth.post(
            "/pdf/info",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        
        assert response.status_code == 401
    
    def test_invalid_api_key(self, client_no_auth, sample_pdf_bytes):
        response = client_no_auth.post(
            "/pdf/info",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
            headers={"X-API-Key": "wrong-key"}
        )
        
        assert response.status_code == 403
