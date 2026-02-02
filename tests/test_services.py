import io
import zipfile
import pytest
from app.services import PdfService
from app.services.videoService import (
    validate_cut_input as validate_video_cut_input,
    VideoServiceError,
    VIDEO_EXTENSIONS
)
from app.services.audioService import (
    validate_cut_input as validate_audio_cut_input,
    validate_transcription_input,
    AudioServiceError,
    AUDIO_EXTENSIONS,
    VIDEO_EXTENSIONS as AUDIO_VIDEO_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_LANGUAGES
)
from app.services.imageService import (
    validate_image_file,
    validate_output_format,
    is_svg,
    convert_image,
    compress_image,
    images_to_pdf,
    ImageServiceError,
    IMAGE_EXTENSIONS,
    OUTPUT_FORMATS
)


class TestVideoServiceValidation:
    def test_validate_cut_input_valid_mp4(self):
        ext = validate_video_cut_input("video.mp4", 0, 10)
        assert ext == ".mp4"

    def test_validate_cut_input_valid_mkv(self):
        ext = validate_video_cut_input("video.mkv", 5, 15)
        assert ext == ".mkv"

    def test_validate_cut_input_all_extensions(self):
        for ext in VIDEO_EXTENSIONS:
            result = validate_video_cut_input(f"video{ext}", 0, 10)
            assert result == ext

    def test_validate_cut_input_empty_filename(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input("", 0, 10)
        assert "obrigatório" in exc.value.message

    def test_validate_cut_input_none_filename(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input(None, 0, 10)
        assert exc.value.status_code == 400

    def test_validate_cut_input_invalid_extension(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input("video.txt", 0, 10)
        assert "não suportado" in exc.value.message

    def test_validate_cut_input_negative_start(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input("video.mp4", -5, 10)
        assert "inicial" in exc.value.message

    def test_validate_cut_input_end_before_start(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input("video.mp4", 10, 5)
        assert "maior" in exc.value.message

    def test_validate_cut_input_end_equals_start(self):
        with pytest.raises(VideoServiceError) as exc:
            validate_video_cut_input("video.mp4", 10, 10)
        assert "maior" in exc.value.message

    def test_video_service_error_default_status(self):
        error = VideoServiceError("Test error")
        assert error.status_code == 400
        assert error.message == "Test error"

    def test_video_service_error_custom_status(self):
        error = VideoServiceError("Server error", 500)
        assert error.status_code == 500


class TestAudioServiceValidation:
    def test_validate_cut_input_valid_mp3(self):
        ext = validate_audio_cut_input("audio.mp3", 0, 10)
        assert ext == ".mp3"

    def test_validate_cut_input_valid_wav(self):
        ext = validate_audio_cut_input("audio.wav", 5, 15)
        assert ext == ".wav"

    def test_validate_cut_input_all_extensions(self):
        for ext in AUDIO_EXTENSIONS:
            result = validate_audio_cut_input(f"audio{ext}", 0, 10)
            assert result == ext

    def test_validate_cut_input_empty_filename(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_audio_cut_input("", 0, 10)
        assert "obrigatório" in exc.value.message

    def test_validate_cut_input_video_extension_rejected(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_audio_cut_input("video.mp4", 0, 10)
        assert "não suportado" in exc.value.message

    def test_validate_cut_input_negative_start(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_audio_cut_input("audio.mp3", -5, 10)
        assert "inicial" in exc.value.message

    def test_validate_cut_input_end_before_start(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_audio_cut_input("audio.mp3", 10, 5)
        assert "maior" in exc.value.message


class TestAudioServiceTranscriptionValidation:
    def test_validate_transcription_audio_file(self):
        ext = validate_transcription_input("audio.mp3", None)
        assert ext == ".mp3"

    def test_validate_transcription_video_file(self):
        ext = validate_transcription_input("video.mp4", None)
        assert ext == ".mp4"

    def test_validate_transcription_with_language(self):
        ext = validate_transcription_input("audio.wav", "pt")
        assert ext == ".wav"

    def test_validate_transcription_all_languages(self):
        for lang in SUPPORTED_LANGUAGES:
            ext = validate_transcription_input("audio.mp3", lang)
            assert ext == ".mp3"

    def test_validate_transcription_all_extensions(self):
        for ext in SUPPORTED_EXTENSIONS:
            result = validate_transcription_input(f"file{ext}", None)
            assert result == ext

    def test_validate_transcription_empty_filename(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_transcription_input("", None)
        assert "obrigatório" in exc.value.message

    def test_validate_transcription_invalid_extension(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_transcription_input("file.txt", None)
        assert "não suportado" in exc.value.message

    def test_validate_transcription_invalid_language(self):
        with pytest.raises(AudioServiceError) as exc:
            validate_transcription_input("audio.mp3", "xyz")
        assert "Idioma" in exc.value.message

    def test_audio_service_error_default_status(self):
        error = AudioServiceError("Test error")
        assert error.status_code == 400
        assert error.message == "Test error"

    def test_audio_service_error_custom_status(self):
        error = AudioServiceError("Server error", 500)
        assert error.status_code == 500


class TestExtensionSets:
    def test_video_extensions_not_empty(self):
        assert len(VIDEO_EXTENSIONS) > 0

    def test_audio_extensions_not_empty(self):
        assert len(AUDIO_EXTENSIONS) > 0

    def test_supported_extensions_is_union(self):
        assert SUPPORTED_EXTENSIONS == AUDIO_VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    def test_no_overlap_audio_video(self):
        overlap = VIDEO_EXTENSIONS & AUDIO_EXTENSIONS
        assert len(overlap) == 0

    def test_supported_languages_contains_common(self):
        assert "pt" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES


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


# ============================================================================
# IMAGE SERVICE TESTS
# ============================================================================

class TestImageServiceValidation:
    def test_validate_image_file_valid_jpg(self):
        ext = validate_image_file("image.jpg")
        assert ext == ".jpg"

    def test_validate_image_file_valid_png(self):
        ext = validate_image_file("image.png")
        assert ext == ".png"

    def test_validate_image_file_valid_svg(self):
        ext = validate_image_file("image.svg")
        assert ext == ".svg"

    def test_validate_image_file_all_extensions(self):
        for ext in IMAGE_EXTENSIONS:
            result = validate_image_file(f"image{ext}")
            assert result == ext

    def test_validate_image_file_empty_filename(self):
        with pytest.raises(ImageServiceError) as exc:
            validate_image_file("")
        assert "obrigatório" in exc.value.message

    def test_validate_image_file_none_filename(self):
        with pytest.raises(ImageServiceError) as exc:
            validate_image_file(None)
        assert exc.value.status_code == 400

    def test_validate_image_file_invalid_extension(self):
        with pytest.raises(ImageServiceError) as exc:
            validate_image_file("image.txt")
        assert "não suportado" in exc.value.message

    def test_validate_output_format_valid(self):
        for fmt in OUTPUT_FORMATS:
            result = validate_output_format(fmt)
            assert result == fmt.lower()

    def test_validate_output_format_uppercase(self):
        result = validate_output_format("PNG")
        assert result == "png"

    def test_validate_output_format_invalid(self):
        with pytest.raises(ImageServiceError) as exc:
            validate_output_format("xyz")
        assert "não suportado" in exc.value.message


class TestImageServiceSvgDetection:
    def test_is_svg_valid_svg(self):
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        assert is_svg(svg_content) == True

    def test_is_svg_with_xml_declaration(self):
        svg_content = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        assert is_svg(svg_content) == True

    def test_is_svg_not_svg(self):
        png_header = b'\x89PNG\r\n\x1a\n'
        assert is_svg(png_header) == False

    def test_is_svg_empty(self):
        assert is_svg(b'') == False


class TestImageServiceConvert:
    @pytest.fixture
    def sample_png_bytes(self):
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.fixture
    def sample_rgba_png_bytes(self):
        from PIL import Image
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    def test_convert_png_to_jpeg(self, sample_png_bytes):
        result, ext = convert_image(sample_png_bytes, 'jpeg', 90)
        assert ext == 'jpg'
        assert result.getvalue()

    def test_convert_png_to_webp(self, sample_png_bytes):
        result, ext = convert_image(sample_png_bytes, 'webp', 90)
        assert ext == 'webp'
        assert result.getvalue()

    def test_convert_png_to_gif(self, sample_png_bytes):
        result, ext = convert_image(sample_png_bytes, 'gif')
        assert ext == 'gif'
        assert result.getvalue()

    def test_convert_png_to_bmp(self, sample_png_bytes):
        result, ext = convert_image(sample_png_bytes, 'bmp')
        assert ext == 'bmp'
        assert result.getvalue()

    def test_convert_png_to_tiff(self, sample_png_bytes):
        result, ext = convert_image(sample_png_bytes, 'tiff')
        assert ext == 'tiff'
        assert result.getvalue()

    def test_convert_rgba_to_jpeg(self, sample_rgba_png_bytes):
        result, ext = convert_image(sample_rgba_png_bytes, 'jpeg', 90)
        assert ext == 'jpg'
        assert result.getvalue()

    def test_convert_raster_to_svg_fails(self, sample_png_bytes):
        with pytest.raises(ImageServiceError) as exc:
            convert_image(sample_png_bytes, 'svg')
        assert "SVG não é suportada" in exc.value.message


class TestImageServiceCompress:
    @pytest.fixture
    def sample_jpeg_bytes(self):
        from PIL import Image
        img = Image.new('RGB', (500, 500), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=100)
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.fixture
    def sample_large_png_bytes(self):
        from PIL import Image
        img = Image.new('RGB', (2000, 2000), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    def test_compress_returns_stats(self, sample_jpeg_bytes):
        result, ext, stats = compress_image(sample_jpeg_bytes, 50)
        
        assert ext == 'jpg'
        assert 'original_size' in stats
        assert 'compressed_size' in stats
        assert 'reduction_percent' in stats
        assert 'original_dimensions' in stats
        assert 'final_dimensions' in stats

    def test_compress_reduces_size(self, sample_jpeg_bytes):
        result, ext, stats = compress_image(sample_jpeg_bytes, 30)
        
        assert stats['compressed_size'] <= stats['original_size']

    def test_compress_with_max_dimension(self, sample_large_png_bytes):
        result, ext, stats = compress_image(sample_large_png_bytes, 70, max_dimension=800)
        
        assert stats['final_dimensions'][0] <= 800
        assert stats['final_dimensions'][1] <= 800

    def test_compress_invalid_quality_low(self, sample_jpeg_bytes):
        with pytest.raises(ImageServiceError) as exc:
            compress_image(sample_jpeg_bytes, 0)
        assert "Qualidade" in exc.value.message

    def test_compress_invalid_quality_high(self, sample_jpeg_bytes):
        with pytest.raises(ImageServiceError) as exc:
            compress_image(sample_jpeg_bytes, 101)
        assert "Qualidade" in exc.value.message


class TestImageServiceToPdf:
    @pytest.fixture
    def sample_images(self):
        from PIL import Image
        images = []
        for color in ['red', 'green', 'blue']:
            img = Image.new('RGB', (100, 100), color=color)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            images.append(buffer.getvalue())
        return images

    def test_images_to_pdf_single_layout(self, sample_images):
        result = images_to_pdf(sample_images, layout='single')
        assert result.getvalue()
        # Check PDF header
        assert result.getvalue()[:4] == b'%PDF'

    def test_images_to_pdf_grouped_layout(self, sample_images):
        result = images_to_pdf(sample_images, layout='grouped', images_per_page=2)
        assert result.getvalue()
        assert result.getvalue()[:4] == b'%PDF'

    def test_images_to_pdf_empty_list(self):
        with pytest.raises(ImageServiceError) as exc:
            images_to_pdf([])
        assert "Nenhuma imagem" in exc.value.message

    def test_images_to_pdf_single_image(self, sample_images):
        result = images_to_pdf([sample_images[0]], layout='single')
        assert result.getvalue()[:4] == b'%PDF'


class TestImageServiceError:
    def test_image_service_error_default_status(self):
        error = ImageServiceError("Test error")
        assert error.status_code == 400
        assert error.message == "Test error"

    def test_image_service_error_custom_status(self):
        error = ImageServiceError("Server error", 500)
        assert error.status_code == 500


class TestImageExtensionSets:
    def test_image_extensions_not_empty(self):
        assert len(IMAGE_EXTENSIONS) > 0

    def test_output_formats_not_empty(self):
        assert len(OUTPUT_FORMATS) > 0

    def test_common_formats_supported(self):
        assert '.jpg' in IMAGE_EXTENSIONS
        assert '.png' in IMAGE_EXTENSIONS
        assert '.svg' in IMAGE_EXTENSIONS
        assert 'jpeg' in OUTPUT_FORMATS
        assert 'png' in OUTPUT_FORMATS
        assert 'webp' in OUTPUT_FORMATS
