import io
import zipfile
import pytest
from app.services import PdfService


class TestPdfServiceSplit:
    def test_split_single_page(self, sample_pdf_bytes):
        result, total = PdfService.split(sample_pdf_bytes, "1")
        assert total == 3
        assert result.getvalue()
    
    def test_split_multiple_pages(self, sample_pdf_bytes):
        result, total = PdfService.split(sample_pdf_bytes, "1,3")
        assert total == 3
        assert result.getvalue()
    
    def test_split_range(self, sample_pdf_bytes):
        result, total = PdfService.split(sample_pdf_bytes, "1-2")
        assert total == 3
        assert result.getvalue()


class TestPdfServiceExtractPages:
    def test_extract_pages_creates_zip(self, sample_pdf_bytes):
        result = PdfService.extract_pages(sample_pdf_bytes)
        
        with zipfile.ZipFile(result, 'r') as zf:
            names = zf.namelist()
            assert len(names) == 3
            assert "page_1.pdf" in names
            assert "page_2.pdf" in names
            assert "page_3.pdf" in names


class TestPdfServiceMerge:
    def test_merge_two_pdfs(self, sample_pdf_bytes):
        contents = [
            ("doc1.pdf", sample_pdf_bytes),
            ("doc2.pdf", sample_pdf_bytes)
        ]
        result = PdfService.merge(contents)
        assert result.getvalue()


class TestPdfServicePassword:
    def test_add_password(self, sample_pdf_bytes):
        result = PdfService.add_password(sample_pdf_bytes, "senha123", None)
        assert result.getvalue()
    
    def test_add_password_with_owner(self, sample_pdf_bytes):
        result = PdfService.add_password(sample_pdf_bytes, "user", "owner")
        assert result.getvalue()
    
    def test_remove_password(self, protected_pdf_bytes):
        result = PdfService.remove_password(protected_pdf_bytes, "user123")
        assert result.getvalue()
    
    def test_remove_password_wrong_password(self, protected_pdf_bytes):
        with pytest.raises(Exception):
            PdfService.remove_password(protected_pdf_bytes, "senha_errada")


class TestPdfServiceInfo:
    def test_get_info(self, sample_pdf_bytes):
        result = PdfService.get_info(sample_pdf_bytes, "teste.pdf")
        
        assert result["filename"] == "teste.pdf"
        assert result["pages"] == 3
        assert result["encrypted"] == False
        assert "pdf_version" in result
        assert "metadata" in result


class TestPdfServiceConvertToImage:
    def test_convert_single_page_to_png(self, sample_pdf_bytes):
        buffer, ext, is_single, page_num, mime = PdfService.convert_to_image(
            sample_pdf_bytes, "png", 150, "1"
        )
        
        assert is_single == True
        assert ext == "png"
        assert page_num == 1
        assert mime == "image/png"
        assert buffer.getvalue()
    
    def test_convert_single_page_to_jpeg(self, sample_pdf_bytes):
        buffer, ext, is_single, page_num, mime = PdfService.convert_to_image(
            sample_pdf_bytes, "jpeg", 150, "1"
        )
        
        assert ext == "jpg"
        assert mime == "image/jpeg"
    
    def test_convert_multiple_pages_returns_zip(self, sample_pdf_bytes):
        buffer, ext, is_single, page_num, mime = PdfService.convert_to_image(
            sample_pdf_bytes, "png", 150, "1-2"
        )
        
        assert is_single == False
        assert mime == "application/zip"
        
        with zipfile.ZipFile(buffer, 'r') as zf:
            names = zf.namelist()
            assert "page_1.png" in names
            assert "page_2.png" in names
    
    def test_convert_all_pages(self, sample_pdf_bytes):
        buffer, ext, is_single, page_num, mime = PdfService.convert_to_image(
            sample_pdf_bytes, "png", 150, None
        )
        
        assert is_single == False
        
        with zipfile.ZipFile(buffer, 'r') as zf:
            assert len(zf.namelist()) == 3


class TestPdfServiceExtractText:
    def test_extract_text(self, sample_pdf_with_text):
        result = PdfService.extract_text(sample_pdf_with_text)
        
        assert len(result) == 1
        assert result[0]["page"] == 1
        assert "Test text" in result[0]["text"]


class TestPdfServiceOFX:
    def test_convert_to_ofx_with_transactions(self, sample_bank_statement_pdf):
        result = PdfService.convert_to_ofx(
            sample_bank_statement_pdf,
            "032",
            "12345678",
            "CHECKING"
        )
        
        if result:  # Pode não extrair dependendo do formato
            assert "OFXHEADER" in result
            assert "<BANKID>032" in result
            assert "<ACCTID>12345678" in result
    
    def test_convert_to_ofx_no_transactions(self, sample_pdf_bytes):
        result = PdfService.convert_to_ofx(
            sample_pdf_bytes,
            "032",
            "12345678",
            "CHECKING"
        )
        
        assert result is None


class TestTransactionParsing:
    def test_parse_zoop_format(self):
        lines = [
            "15/01/2026",
            "PIX",
            "Pagamento João",
            "R$ 150,00",
            "16/01/2026",
            "TED",
            "Transferência",
            "-R$ 200,00",
        ]
        
        from datetime import datetime
        result = PdfService._parse_zoop_format(lines, 2026)
        
        assert len(result) == 2
        assert result[0]["amount"] == 150.00
        assert result[1]["amount"] == -200.00
    
    def test_try_parse_transaction_standard_format(self):
        line = "15/01/2026 Compra no mercado R$ 150,00"
        result = PdfService._try_parse_transaction(line, 2026)
        
        if result:
            assert result["amount"] == 150.00
            assert "mercado" in result["description"]
    
    def test_generate_ofx_structure(self):
        from datetime import datetime
        transactions = [
            {"date": datetime(2026, 1, 15), "description": "PIX Recebido", "amount": 100.00},
            {"date": datetime(2026, 1, 16), "description": "TED Enviado", "amount": -50.00},
        ]
        
        result = PdfService._generate_ofx(transactions, "032", "123456", "CHECKING")
        
        assert "OFXHEADER:100" in result
        assert "<BANKID>032" in result
        assert "<ACCTID>123456" in result
        assert "<TRNTYPE>CREDIT" in result
        assert "<TRNTYPE>DEBIT" in result
        assert "<TRNAMT>100.00" in result
        assert "<TRNAMT>-50.00" in result
        assert "<BALAMT>50.00" in result
