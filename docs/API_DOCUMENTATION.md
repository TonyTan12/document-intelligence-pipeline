# API Documentation

Complete reference for the Document Intelligence Pipeline REST API.

## Base URL

```
Local Development: http://localhost:8000
Production: https://your-domain.com
```

## OpenAPI/Swagger

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication

Currently, the API does not require authentication. For production use, add API key middleware:

```python
# Add to api.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/documents/upload")
async def upload_document(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    ...
):
    # Validate token
    pass
```

## Endpoints

### 1. Health Check

Check API status and component availability.

**Endpoint:** `GET /` or `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "document_processor": "ready",
    "ocr_engine": "ready",
    "data_extractor": "ready"
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

### 2. Upload Document

Upload and process a single document.

**Endpoint:** `POST /documents/upload`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Document file (PDF, PNG, JPG, TIFF, BMP) |
| `extract_data` | Boolean | No | Enable AI extraction (default: true) |
| `language` | String | No | OCR language code (default: "eng") |

**Request Example (cURL):**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf" \
  -F "extract_data=true" \
  -F "language=eng"
```

**Request Example (Python):**
```python
import requests

url = "http://localhost:8000/documents/upload"
files = {"file": open("invoice.pdf", "rb")}
data = {"extract_data": "true", "language": "eng"}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result["document_id"])
```

**Response (202 Accepted):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "invoice.pdf",
  "status": "processing",
  "message": "Document uploaded successfully, processing started"
}
```

**Status Codes:**
- `202 Accepted`: Document accepted for processing
- `400 Bad Request`: Invalid file type or size
- `413 Payload Too Large`: File exceeds size limit (50MB)

---

### 3. Get Document Result

Retrieve processing results for a document.

**Endpoint:** `GET /documents/{document_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | String | Document identifier from upload |

**Request Example:**
```bash
curl "http://localhost:8000/documents/doc_a1b2c3d4e5f6"
```

**Response (Processing):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "invoice.pdf",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response (Completed):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "invoice.pdf",
  "status": "completed",
  "document_type": "invoice",
  "ocr_result": {
    "text": "Invoice #12345...",
    "confidence": 0.94,
    "engine": "tesseract",
    "page_count": 1,
    "language": "eng"
  },
  "extracted_data": {
    "document_type": "invoice",
    "fields": {
      "vendor_name": {
        "value": "Acme Corp",
        "confidence": 0.95,
        "source_text": "Acme Corp"
      },
      "invoice_number": {
        "value": "INV-12345",
        "confidence": 0.98,
        "source_text": "Invoice #: INV-12345"
      },
      "invoice_date": {
        "value": "2024-01-15",
        "confidence": 0.92,
        "source_text": "Date: January 15, 2024"
      },
      "total_amount": {
        "value": 1500.00,
        "confidence": 0.94,
        "source_text": "Total: $1,500.00"
      }
    },
    "confidence": 0.94,
    "model_used": "gpt-4o-mini",
    "processing_time_ms": 1234
  },
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:30:02Z"
}
```

**Response (Failed):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "corrupted.pdf",
  "status": "failed",
  "error_message": "Unable to parse PDF file",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:30:01Z"
}
```

**Status Codes:**
- `200 OK`: Result retrieved successfully
- `404 Not Found`: Document ID not found

---

### 4. Batch Upload

Upload and process multiple documents simultaneously.

**Endpoint:** `POST /documents/batch`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | Yes | Multiple document files (max 10) |
| `extract_data` | Boolean | No | Enable AI extraction (default: true) |
| `language` | String | No | OCR language code (default: "eng") |

**Request Example:**
```bash
curl -X POST "http://localhost:8000/documents/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@invoice1.pdf" \
  -F "files=@receipt1.png" \
  -F "files=@contract.pdf" \
  -F "extract_data=true"
```

**Response:**
```json
{
  "batch_id": "batch_x1y2z3a4b5c6",
  "document_count": 3,
  "documents": [
    {
      "document_id": "doc_doc1abc123",
      "filename": "invoice1.pdf",
      "status": "processing",
      "message": "Processing started"
    },
    {
      "document_id": "doc_doc2def456",
      "filename": "receipt1.png",
      "status": "processing",
      "message": "Processing started"
    },
    {
      "document_id": "doc_doc3ghi789",
      "filename": "contract.pdf",
      "status": "processing",
      "message": "Processing started"
    }
  ]
}
```

**Status Codes:**
- `202 Accepted`: Batch accepted for processing
- `400 Bad Request`: Invalid request (too many files)

---

### 5. Get Batch Result

Retrieve results for all documents in a batch.

**Endpoint:** `GET /batch/{batch_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_id` | String | Batch identifier from upload |

**Request Example:**
```bash
curl "http://localhost:8000/batch/batch_x1y2z3a4b5c6"
```

**Response:**
```json
{
  "batch_id": "batch_x1y2z3a4b5c6",
  "status": "completed",
  "total_documents": 3,
  "completed": 3,
  "failed": 0,
  "results": [
    {
      "document_id": "doc_doc1abc123",
      "filename": "invoice1.pdf",
      "status": "completed",
      "document_type": "invoice",
      "ocr_result": { ... },
      "extracted_data": { ... }
    },
    {
      "document_id": "doc_doc2def456",
      "filename": "receipt1.png",
      "status": "completed",
      "document_type": "receipt",
      "ocr_result": { ... },
      "extracted_data": { ... }
    },
    {
      "document_id": "doc_doc3ghi789",
      "filename": "contract.pdf",
      "status": "completed",
      "document_type": "contract",
      "ocr_result": { ... },
      "extracted_data": { ... }
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Results retrieved successfully
- `404 Not Found`: Batch ID not found

---

### 6. Delete Document

Remove a document and its results from the system.

**Endpoint:** `DELETE /documents/{document_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | String | Document identifier |

**Request Example:**
```bash
curl -X DELETE "http://localhost:8000/documents/doc_a1b2c3d4e5f6"
```

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Document deleted
- `404 Not Found`: Document ID not found

---

## Data Models

### ProcessingStatus

Enum representing document processing state:
- `pending`: Waiting to be processed
- `processing`: Currently being processed
- `completed`: Processing finished successfully
- `failed`: Processing failed

### OCRResult

| Field | Type | Description |
|-------|------|-------------|
| `text` | String | Extracted text content |
| `confidence` | Float | OCR confidence score (0-1) |
| `engine` | String | OCR engine used (tesseract/easyocr) |
| `page_count` | Integer | Number of pages processed |
| `language` | String | Language code used |

### ExtractedField

| Field | Type | Description |
|-------|------|-------------|
| `value` | Any | The extracted value |
| `confidence` | Float | Extraction confidence (0-1) |
| `source_text` | String | Original text snippet |

### ExtractedData

| Field | Type | Description |
|-------|------|-------------|
| `document_type` | String | Detected document category |
| `fields` | Object | Dictionary of ExtractedField |
| `confidence` | Float | Overall extraction confidence |
| `model_used` | String | AI model used |
| `processing_time_ms` | Integer | Processing time in milliseconds |

---

## Error Handling

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error description",
  "details": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Invalid input |
| `404` | Not Found - Resource doesn't exist |
| `413` | Payload Too Large - File too big |
| `422` | Validation Error - Invalid parameters |
| `500` | Internal Server Error |

---

## Rate Limiting

Default rate limits (configurable):
- 100 requests per minute per IP
- 10 concurrent uploads per IP

---

## Webhooks (Future)

Planned webhook support for async notifications:

```json
{
  "event": "document.completed",
  "document_id": "doc_abc123",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": { ... }
}
```

---

## SDK Examples

### Python

```python
import requests
import time

class DocumentIntelligenceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_and_wait(self, file_path, extract_data=True, timeout=60):
        """Upload document and wait for processing."""
        # Upload
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/documents/upload",
                files={"file": f},
                data={"extract_data": extract_data}
            )
        
        doc_id = response.json()["document_id"]
        
        # Poll for result
        start = time.time()
        while time.time() - start < timeout:
            result = requests.get(f"{self.base_url}/documents/{doc_id}").json()
            if result["status"] in ["completed", "failed"]:
                return result
            time.sleep(1)
        
        raise TimeoutError("Processing took too long")

# Usage
client = DocumentIntelligenceClient()
result = client.upload_and_wait("invoice.pdf")
print(result["extracted_data"]["fields"]["total_amount"])
```

### JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function uploadDocument(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('extract_data', 'true');
  
  const response = await axios.post(
    'http://localhost:8000/documents/upload',
    form,
    { headers: form.getHeaders() }
  );
  
  return response.data.document_id;
}

async function getResult(documentId) {
  const response = await axios.get(
    `http://localhost:8000/documents/${documentId}`
  );
  return response.data;
}

// Usage
uploadDocument('invoice.pdf')
  .then(id => getResult(id))
  .then(result => console.log(result.extracted_data));
```

---

## Changelog

### v1.0.0
- Initial API release
- Document upload and processing
- OCR with Tesseract/EasyOCR
- AI extraction with GPT-4o-mini
- Batch processing support
