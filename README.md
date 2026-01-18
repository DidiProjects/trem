# PDF API

API REST para manipulação de arquivos PDF com autenticação por API Key.

## Funcionalidades

### Manipulação de PDF
- **Split PDF**: Extrair páginas específicas de um PDF
- **Extract Pages**: Separar todas as páginas em arquivos individuais
- **Merge PDFs**: Juntar múltiplos PDFs em um único arquivo
- **Add Password**: Adicionar senha de proteção ao PDF
- **Remove Password**: Remover senha de um PDF protegido
- **PDF Info**: Obter informações e metadados do PDF

### Conversão
- **Convert to Image**: Converter PDF para PNG, JPEG ou TIFF
- **Convert to OFX**: Extrair transações de extratos bancários para OFX
- **Extract Text**: Extrair texto de todas as páginas do PDF

## Arquitetura

```
app/
├── main.py              # Aplicação FastAPI
├── auth_secure.py       # Autenticação com rate limiting
├── config.py            # Configurações
├── routers/
│   └── pdfRoute.py      # Controller - endpoints HTTP
├── services/
│   └── pdfService.py    # Lógica de processamento PDF
└── utils/
    ├── filename.py      # Utilitários de nome de arquivo
    ├── pagination.py    # Parser de intervalos de página
    └── security.py      # Validações de segurança
```

## Segurança

### Proteção de Arquivos
- ✅ Validação de magic bytes (verifica conteúdo real do PDF)
- ✅ Limite de tamanho (50MB por arquivo)
- ✅ Sanitização de nomes de arquivo
- ✅ Proteção contra path traversal
- ✅ Limite de 20 arquivos por merge

### Autenticação
- ✅ API Key com comparação timing-safe
- ✅ Rate limiting (100 req/min por IP)
- ✅ Bloqueio após 10 tentativas falhas (5 min)
- ✅ Logging de tentativas de autenticação

## Requisitos

- Docker
- Docker Compose

## Configuração

1. Copie o arquivo de exemplo de variáveis de ambiente:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` e defina sua API Key:
```
API_KEY=sua-chave-secreta-aqui
```

## Execução

### Com Docker Compose

```bash
docker-compose up -d --build
```

### Desenvolvimento Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testes

```bash
# Executar todos os testes
docker exec pdf-api pytest -v

# Executar testes específicos
docker exec pdf-api pytest tests/test_security.py -v
docker exec pdf-api pytest tests/test_services.py -v
docker exec pdf-api pytest tests/test_routes.py -v
```

## Endpoints

Todos os endpoints requerem o header `X-API-Key` com sua chave de acesso.

### Health Check
```
GET /health
```

### Split PDF
```
POST /pdf/split
Content-Type: multipart/form-data

file: arquivo.pdf
pages: "1-3,5,7-10"
```

### Extract Pages
```
POST /pdf/extract-pages
Content-Type: multipart/form-data

file: arquivo.pdf
```
Retorna um ZIP com cada página em um arquivo separado.

### Merge PDFs
```
POST /pdf/merge
Content-Type: multipart/form-data

files: arquivo1.pdf
files: arquivo2.pdf
```
Máximo de 20 arquivos por requisição.

### Add Password
```
POST /pdf/add-password
Content-Type: multipart/form-data

file: arquivo.pdf
user_password: senha123
owner_password: senha_admin (opcional)
```

### Remove Password
```
POST /pdf/remove-password
Content-Type: multipart/form-data

file: arquivo.pdf
password: senha123
```

### PDF Info
```
POST /pdf/info
Content-Type: multipart/form-data

file: arquivo.pdf
```

### Convert to Image
```
POST /pdf/convert-to-image
Content-Type: multipart/form-data

file: arquivo.pdf
format: png | jpeg | tiff (padrão: png)
dpi: 72-600 (padrão: 150)
pages: "1-3,5" (opcional, padrão: todas)
```
Retorna imagem única ou ZIP com múltiplas páginas.

### Convert to OFX
```
POST /pdf/convert-to-ofx
Content-Type: multipart/form-data

file: extrato.pdf
bank_id: 001 (código do banco)
account_id: 12345678 (número da conta)
account_type: CHECKING | SAVINGS | CREDITCARD
```
Extrai transações de extratos bancários para formato OFX.

### Extract Text
```
POST /pdf/extract-text
Content-Type: multipart/form-data

file: arquivo.pdf
```
Retorna JSON com texto de cada página.

## Exemplo de Uso com cURL

```bash
# Split PDF
curl -X POST "http://localhost:3002/pdf/split" \
  -H "X-API-Key: sua-chave-secreta-aqui" \
  -F "file=@documento.pdf" \
  -F "pages=1-3" \
  --output resultado.pdf

# Convert to Image
curl -X POST "http://localhost:3002/pdf/convert-to-image" \
  -H "X-API-Key: sua-chave-secreta-aqui" \
  -F "file=@documento.pdf" \
  -F "format=png" \
  -F "dpi=300" \
  --output imagens.zip

# Extract Text
curl -X POST "http://localhost:3002/pdf/extract-text" \
  -H "X-API-Key: sua-chave-secreta-aqui" \
  -F "file=@documento.pdf"
```

## CI/CD

O deploy é automatizado via GitHub Actions:

1. **Testes**: Executa todos os testes unitários
2. **Deploy**: Só ocorre se todos os testes passarem

```yaml
# .github/workflows/deploy.yml
jobs:
  test:    # Executa pytest
  deploy:  # Só roda se test passar (needs: test)
```

## Documentação Interativa

Acesse a documentação Swagger em: `http://localhost:3002/docs`

## Licença

MIT
