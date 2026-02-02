import pytest
from fastapi import HTTPException
from app.utils.filename import safe_filename, get_output_filename
from app.utils.pagination import parse_page_ranges
from app.utils.security import (
    validate_file_type,
    validate_file_size,
    get_file_hash,
    MAGIC_BYTES,
    MAX_SIZES
)


class TestSafeFilename:
    def test_simple_filename(self):
        result = safe_filename("documento.pdf")
        assert result == "documento.pdf"

    def test_filename_with_spaces(self):
        result = safe_filename("meu documento.pdf")
        assert result == "meu%20documento.pdf"

    def test_filename_with_special_chars(self):
        result = safe_filename("arquivo (1).pdf")
        assert result == "arquivo%20%281%29.pdf"

    def test_filename_with_accents(self):
        result = safe_filename("relatório_março.pdf")
        assert "relat" in result
        assert ".pdf" in result
        assert "%C3%" in result

    def test_empty_filename(self):
        result = safe_filename("")
        assert result == ""

    def test_filename_with_path_traversal(self):
        result = safe_filename("../../../etc/passwd")
        assert ".." not in result or "%2E%2E" in result

    def test_filename_unicode(self):
        result = safe_filename("文档.pdf")
        assert ".pdf" in result


class TestGetOutputFilename:
    def test_split_operation(self):
        result = get_output_filename("documento.pdf", "split")
        assert result == "documento-split.pdf"

    def test_protected_operation(self):
        result = get_output_filename("arquivo.pdf", "protected")
        assert result == "arquivo-protected.pdf"

    def test_merged_operation(self):
        result = get_output_filename("relatorio.pdf", "merged")
        assert result == "relatorio-merged.pdf"

    def test_filename_with_multiple_dots(self):
        result = get_output_filename("arquivo.v2.pdf", "split")
        assert result == "arquivo.v2-split.pdf"

    def test_recorte_operation(self):
        result = get_output_filename("video.mp4", "recorte", preserve_extension=True)
        assert result == "video-recorte.mp4"


class TestParsePageRanges:
    def test_single_page(self):
        result = parse_page_ranges("1", 10)
        assert result == [1]

    def test_multiple_pages(self):
        result = parse_page_ranges("1,3,5", 10)
        assert result == [1, 3, 5]

    def test_page_range(self):
        result = parse_page_ranges("1-5", 10)
        assert result == [1, 2, 3, 4, 5]

    def test_mixed_pages_and_ranges(self):
        result = parse_page_ranges("1,3-5,8", 10)
        assert result == [1, 3, 4, 5, 8]

    def test_removes_duplicates(self):
        result = parse_page_ranges("1,1,2,2-3", 10)
        assert result == [1, 2, 3]

    def test_sorts_result(self):
        result = parse_page_ranges("5,1,3", 10)
        assert result == [1, 3, 5]

    def test_handles_spaces(self):
        result = parse_page_ranges("1, 3, 5 - 7", 10)
        assert result == [1, 3, 5, 6, 7]

    def test_invalid_page_zero(self):
        with pytest.raises(HTTPException) as exc:
            parse_page_ranges("0", 10)
        assert exc.value.status_code == 400

    def test_invalid_page_exceeds_total(self):
        with pytest.raises(HTTPException) as exc:
            parse_page_ranges("15", 10)
        assert exc.value.status_code == 400

    def test_invalid_range_exceeds_total(self):
        with pytest.raises(HTTPException) as exc:
            parse_page_ranges("5-15", 10)
        assert exc.value.status_code == 400

    def test_invalid_range_start_greater_than_end(self):
        with pytest.raises(HTTPException) as exc:
            parse_page_ranges("5-3", 10)
        assert exc.value.status_code == 400

    def test_all_pages(self):
        result = parse_page_ranges("1-10", 10)
        assert result == list(range(1, 11))


class TestValidateFileType:
    def test_valid_pdf(self):
        content = b"%PDF-1.4 test content"
        assert validate_file_type(content, "pdf") is True

    def test_invalid_pdf(self):
        content = b"not a pdf file"
        assert validate_file_type(content, "pdf") is False

    def test_valid_zip(self):
        content = b"PK\x03\x04 zip content"
        assert validate_file_type(content, "zip") is True

    def test_valid_zip_empty(self):
        content = b"PK\x05\x06 empty zip"
        assert validate_file_type(content, "zip") is True

    def test_invalid_zip(self):
        content = b"not a zip file"
        assert validate_file_type(content, "zip") is False

    def test_unknown_type(self):
        content = b"any content"
        assert validate_file_type(content, "unknown") is False

    def test_empty_content(self):
        assert validate_file_type(b"", "pdf") is False


class TestValidateFileSize:
    def test_valid_pdf_size(self):
        content = b"x" * (1024 * 1024)
        assert validate_file_size(content, "pdf") is True

    def test_pdf_exceeds_limit(self):
        content = b"x" * (51 * 1024 * 1024)
        assert validate_file_size(content, "pdf") is False

    def test_valid_zip_size(self):
        content = b"x" * (50 * 1024 * 1024)
        assert validate_file_size(content, "zip") is True

    def test_zip_exceeds_limit(self):
        content = b"x" * (101 * 1024 * 1024)
        assert validate_file_size(content, "zip") is False

    def test_unknown_type_default_limit(self):
        content = b"x" * (9 * 1024 * 1024)
        assert validate_file_size(content, "unknown") is True

    def test_unknown_type_exceeds_default(self):
        content = b"x" * (11 * 1024 * 1024)
        assert validate_file_size(content, "unknown") is False


class TestGetFileHash:
    def test_returns_string(self):
        result = get_file_hash(b"test content")
        assert isinstance(result, str)

    def test_returns_16_chars(self):
        result = get_file_hash(b"test content")
        assert len(result) == 16

    def test_same_content_same_hash(self):
        content = b"same content"
        assert get_file_hash(content) == get_file_hash(content)

    def test_different_content_different_hash(self):
        assert get_file_hash(b"content1") != get_file_hash(b"content2")

    def test_empty_content(self):
        result = get_file_hash(b"")
        assert len(result) == 16


class TestSecurityConstants:
    def test_magic_bytes_pdf_exists(self):
        assert "pdf" in MAGIC_BYTES
        assert len(MAGIC_BYTES["pdf"]) > 0

    def test_magic_bytes_zip_exists(self):
        assert "zip" in MAGIC_BYTES
        assert len(MAGIC_BYTES["zip"]) >= 2

    def test_max_sizes_pdf(self):
        assert MAX_SIZES["pdf"] == 50 * 1024 * 1024

    def test_max_sizes_zip(self):
        assert MAX_SIZES["zip"] == 100 * 1024 * 1024
