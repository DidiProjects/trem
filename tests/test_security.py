import io
import pytest
from app.utils.security import (
    validate_file_type,
    validate_file_size,
    sanitize_filename,
    get_file_hash
)


class TestValidateFileType:
    def test_valid_pdf(self):
        content = b"%PDF-1.4 fake pdf content"
        assert validate_file_type(content, "pdf") == True
    
    def test_invalid_pdf_wrong_magic(self):
        content = b"PK\x03\x04 this is a zip"
        assert validate_file_type(content, "pdf") == False
    
    def test_invalid_pdf_text_file(self):
        content = b"just some text content"
        assert validate_file_type(content, "pdf") == False
    
    def test_valid_zip(self):
        content = b"PK\x03\x04 zip content"
        assert validate_file_type(content, "zip") == True
    
    def test_unknown_type(self):
        content = b"any content"
        assert validate_file_type(content, "unknown") == False


class TestValidateFileSize:
    def test_within_limit(self):
        content = b"x" * 1000  # 1KB
        assert validate_file_size(content, "pdf") == True
    
    def test_exceeds_limit(self):
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        assert validate_file_size(content, "pdf") == False
    
    def test_unknown_type_default_limit(self):
        content = b"x" * (9 * 1024 * 1024)  # 9MB
        assert validate_file_size(content, "unknown") == True


class TestSanitizeFilename:
    def test_simple_filename(self):
        assert sanitize_filename("document.pdf") == "document.pdf"
    
    def test_path_traversal_attack(self):
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert result == "passwd"
    
    def test_windows_path_traversal(self):
        result = sanitize_filename("..\\..\\windows\\system32")
        assert ".." not in result
    
    def test_dangerous_characters(self):
        result = sanitize_filename('file<>:"|?*.pdf')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result
    
    def test_null_byte_injection(self):
        result = sanitize_filename("file.pdf\x00.exe")
        assert "\x00" not in result
    
    def test_empty_filename(self):
        result = sanitize_filename("")
        assert result == "documento"
    
    def test_none_filename(self):
        result = sanitize_filename(None)
        assert result == "documento"
    
    def test_max_length(self):
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50
        assert result.endswith(".pdf")


class TestGetFileHash:
    def test_generates_hash(self):
        content = b"test content"
        hash1 = get_file_hash(content)
        assert len(hash1) == 16
        assert hash1.isalnum()
    
    def test_same_content_same_hash(self):
        content = b"test content"
        assert get_file_hash(content) == get_file_hash(content)
    
    def test_different_content_different_hash(self):
        assert get_file_hash(b"content1") != get_file_hash(b"content2")


class TestMaliciousFileUpload:
    """Testes para prevenir uploads maliciosos"""
    
    def test_fake_pdf_extension_with_exe_content(self):
        # Arquivo .pdf mas com conteúdo de executável
        exe_magic = b"MZ"  # Magic bytes de .exe
        content = exe_magic + b"\x00" * 100
        assert validate_file_type(content, "pdf") == False
    
    def test_fake_pdf_extension_with_zip_content(self):
        # Arquivo .pdf mas com conteúdo de ZIP (possível zip bomb)
        zip_magic = b"PK\x03\x04"
        content = zip_magic + b"\x00" * 100
        assert validate_file_type(content, "pdf") == False
    
    def test_polyglot_file_detection(self):
        # Arquivo que poderia ser interpretado como múltiplos tipos
        content = b"%PDF-1.4 but also <script>alert('xss')</script>"
        # Deve passar como PDF válido (magic bytes corretos)
        assert validate_file_type(content, "pdf") == True
