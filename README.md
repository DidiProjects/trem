# PDF API

API REST para manipulação de arquivos PDF com autenticação por API Key.

## Funcionalidades

- **Split PDF**: Extrair páginas específicas de um PDF
- **Extract Pages**: Separar todas as páginas em arquivos individuais
- **Merge PDFs**: Juntar múltiplos PDFs em um único arquivo
- **Add Password**: Adicionar senha de proteção ao PDF
- **Remove Password**: Remover senha de um PDF protegido
- **PDF Info**: Obter informações e metadados do PDF

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

## Exemplo de Uso com cURL

```bash
curl -X POST "http://localhost:8000/pdf/split" \
  -H "X-API-Key: sua-chave-secreta-aqui" \
  -F "file=@documento.pdf" \
  -F "pages=1-3" \
  --output resultado.pdf
```

## Documentação Interativa

Acesse a documentação Swagger em: `http://localhost:8000/docs`
