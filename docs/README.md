# Document Intelligence Pipeline

A production-ready AI system that extracts structured data from documents (invoices, receipts, contracts) using OCR and GPT models.

## 🌟 Features

- **Document Upload**: Support for PDF, PNG, JPG, TIFF, BMP formats
- **OCR Processing**: Extract text from images and scanned documents using Tesseract/EasyOCR
- **AI-Powered Extraction**: Intelligent data extraction using OpenAI GPT-4o-mini
- **Document Classification**: Automatic categorization (invoice, receipt, contract, etc.)
- **Batch Processing**: Process multiple documents simultaneously
- **Confidence Scoring**: Quality metrics for all extractions
- **REST API**: FastAPI-based endpoints for easy integration

## 📋 Supported Document Types

| Document Type | Fields Extracted |
|--------------|------------------|
| **Invoices** | Vendor name, invoice number, dates, amounts, line items, payment terms |
| **Receipts** | Merchant name, transaction date/time, items, total, tax, payment method |
| **Contracts** | Parties, effective/expiration dates, contract value, key clauses |

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Document Upload │────▶│  Document        │────▶│  OCR Engine     │
│  (PDF/Image)     │     │  Processor       │     │  (Tesseract/    │
└─────────────────┘     └──────────────────┘     │   EasyOCR)       │
                                                  └────────┬────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  JSON Response   │◀────│  Data Extractor  │◀────│  Raw Text       │
│  (Structured)    │     │  (GPT-4o-mini)   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Tesseract OCR (for local OCR)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/document-intelligence-pipeline.git
cd document-intelligence-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

5. Run the API:
```bash
python -m src.api
# Or on Windows:
.\run_api.ps1
```

## 📖 API Endpoints

### Upload Document
```bash
POST /documents/upload
Content-Type: multipart/form-data

file: <document.pdf>
extract_data: true
language: eng
```

### Get Results
```bash
GET /documents/{document_id}
```

### Batch Upload
```bash
POST /documents/batch
Content-Type: multipart/form-data

files: <doc1.pdf>
files: <doc2.png>
extract_data: true
```

### Health Check
```bash
GET /health
```

## 📁 Project Structure

```
Document-Intelligence-Pipeline/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── document_processor.py    # PDF/image ingestion
│   ├── ocr_engine.py            # OCR with Tesseract/EasyOCR
│   ├── extractor.py             # AI data extraction
│   ├── models.py                # Pydantic models
│   └── api.py                   # FastAPI endpoints
├── tests/
│   └── test_processor.py        # Unit tests
├── docs/
│   ├── README.md                # This file
│   ├── API_DOCUMENTATION.md     # Detailed API docs
│   └── SETUP_GUIDE.md           # Installation guide
├── sample_docs/                 # Add your test documents here
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── config.yaml                  # Configuration file
└── run_api.ps1                  # Windows startup script
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model for extraction | gpt-4o-mini |
| `OCR_ENGINE` | Primary OCR engine | tesseract |
| `OCR_LANGUAGE` | Default OCR language | eng |
| `API_HOST` | API bind address | 0.0.0.0 |
| `API_PORT` | API port | 8000 |
| `MAX_FILE_SIZE` | Max upload size (MB) | 50 |

### config.yaml

```yaml
ocr:
  dpi: 300
  enhance_contrast: true
  languages:
    - eng

extraction:
  model: gpt-4o-mini
  max_tokens: 2000
  temperature: 0.1

api:
  max_file_size: 52428800  # 50MB
  batch_size_limit: 10
```

## 📊 Example Output

### Invoice Extraction
```json
{
  "document_id": "doc_abc123",
  "status": "completed",
  "document_type": "invoice",
  "ocr_result": {
    "text": "Invoice #INV-2024-001...",
    "confidence": 0.94,
    "engine": "tesseract"
  },
  "extracted_data": {
    "document_type": "invoice",
    "fields": {
      "vendor_name": {
        "value": "Acme Corporation",
        "confidence": 0.95,
        "source_text": "Acme Corporation - Invoice"
      },
      "invoice_number": {
        "value": "INV-2024-001",
        "confidence": 0.98,
        "source_text": "Invoice #: INV-2024-001"
      },
      "total_amount": {
        "value": 1250.00,
        "confidence": 0.92,
        "source_text": "Total: $1,250.00"
      }
    },
    "confidence": 0.93,
    "model_used": "gpt-4o-mini",
    "processing_time_ms": 1450
  }
}
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 🐳 Docker Support

```bash
# Build image
docker build -t doc-intel-pipeline .

# Run container
docker run -p 8000:8000 --env-file .env doc-intel-pipeline
```

## 📈 Performance

- **Single Document**: ~2-5 seconds (depending on size)
- **OCR Only**: ~1-2 seconds per page
- **AI Extraction**: ~1-3 seconds per document
- **Batch Processing**: Concurrent processing supported

## 🔒 Security

- API key authentication (configure via middleware)
- File size limits
- Supported file type validation
- No persistent storage of uploaded documents (in-memory only)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI](https://openai.com/)

---

Built with ❤️ by Tony - AI Product Manager
