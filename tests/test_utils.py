import pytest
from fastapi import HTTPException
from app.utils.filename import safe_filename, get_output_filename
from app.utils.pagination import parse_page_ranges


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
        # ó e ç são encoded
        assert "relat" in result
        assert ".pdf" in result
        assert "%C3%" in result  # caractere acentuado encoded
    
    def test_empty_filename(self):
        result = safe_filename("")
        assert result == ""


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
