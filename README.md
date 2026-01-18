# PDF API

REST API for PDF file manipulation with API Key authentication.

## Features

### PDF Manipulation
- **Split PDF**: Extract specific pages from a PDF
- **Extract Pages**: Separate all pages into individual files
- **Merge PDFs**: Combine multiple PDFs into a single file
- **Add Password**: Add password protection to PDF
- **Remove Password**: Remove password from a protected PDF
- **PDF Info**: Get PDF information and metadata

### Conversion
- **Convert to Image**: Convert PDF to PNG, JPEG, or TIFF
- **Convert to OFX**: Extract transactions from bank statements to OFX
- **Extract Text**: Extract text from all PDF pages

## Architecture

```
app/
├── main.py              # FastAPI application
├── auth_secure.py       # Authentication with rate limiting
├── config.py            # Configuration
├── routers/
│   └── pdfRoute.py      # Controller - HTTP endpoints
├── services/
│   └── pdfService.py    # PDF processing logic
└── utils/
    ├── filename.py      # Filename utilities
    ├── pagination.py    # Page range parser
    └── security.py      # Security validations
```

## Security

### File Protection
- ✅ Magic bytes validation (verifies actual PDF content)
- ✅ Size limit (50MB per file)
- ✅ Filename sanitization
- ✅ Path traversal protection
- ✅ Limit of 20 files per merge

### Authentication
- ✅ API Key with timing-safe comparison
- ✅ Rate limiting (100 req/min per IP)
- ✅ Blocking after 10 failed attempts (5 min)
- ✅ Authentication attempt logging

## Requirements

- Docker
- Docker Compose

## Configuration

1. Copy the environment variables example file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and set your API Key:
```
API_KEY=your-secret-key-here
```

## Running

### With Docker Compose

```bash
docker-compose up -d --build
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
# Run all tests
docker exec pdf-api pytest -v

# Run specific tests
docker exec pdf-api pytest tests/test_security.py -v
docker exec pdf-api pytest tests/test_services.py -v
docker exec pdf-api pytest tests/test_routes.py -v
```

## Endpoints

All endpoints require the `X-API-Key` header with your access key.

### Health Check
```
GET /health
```

### Split PDF
```
POST /pdf/split
Content-Type: multipart/form-data

file: document.pdf
pages: "1-3,5,7-10"
```

### Extract Pages
```
POST /pdf/extract-pages
Content-Type: multipart/form-data

file: document.pdf
```
Returns a ZIP with each page in a separate file.

### Merge PDFs
```
POST /pdf/merge
Content-Type: multipart/form-data

files: document1.pdf
files: document2.pdf
```
Maximum of 20 files per request.

### Add Password
```
POST /pdf/add-password
Content-Type: multipart/form-data

file: document.pdf
user_password: password123
owner_password: admin_password (optional)
```

### Remove Password
```
POST /pdf/remove-password
Content-Type: multipart/form-data

file: document.pdf
password: password123
```

### PDF Info
```
POST /pdf/info
Content-Type: multipart/form-data

file: document.pdf
```

### Convert to Image
```
POST /pdf/convert-to-image
Content-Type: multipart/form-data

file: document.pdf
format: png | jpeg | tiff (default: png)
dpi: 72-600 (default: 150)
pages: "1-3,5" (optional, default: all)
```
Returns a single image or ZIP with multiple pages.

### Convert to OFX
```
POST /pdf/convert-to-ofx
Content-Type: multipart/form-data

file: statement.pdf
bank_id: 001 (bank code)
account_id: 12345678 (account number)
account_type: CHECKING | SAVINGS | CREDITCARD
```
Extracts transactions from bank statements to OFX format.

### Extract Text
```
POST /pdf/extract-text
Content-Type: multipart/form-data

file: document.pdf
```
Returns JSON with text from each page.

## Usage Example with cURL

```bash
# Split PDF
curl -X POST "http://localhost:3002/pdf/split" \
  -H "X-API-Key: your-secret-key-here" \
  -F "file=@document.pdf" \
  -F "pages=1-3" \
  --output result.pdf

# Convert to Image
curl -X POST "http://localhost:3002/pdf/convert-to-image" \
  -H "X-API-Key: your-secret-key-here" \
  -F "file=@document.pdf" \
  -F "format=png" \
  -F "dpi=300" \
  --output images.zip

# Extract Text
curl -X POST "http://localhost:3002/pdf/extract-text" \
  -H "X-API-Key: your-secret-key-here" \
  -F "file=@document.pdf"
```

## CI/CD

Deployment is automated via GitHub Actions:

1. **Tests**: Runs all unit tests
2. **Deploy**: Only runs if all tests pass

```yaml
# .github/workflows/deploy.yml
jobs:
  test:    # Runs pytest
  deploy:  # Only runs if test passes (needs: test)
```

## Interactive Documentation

Access Swagger documentation at: `http://localhost:3002/docs`

## License

MIT
