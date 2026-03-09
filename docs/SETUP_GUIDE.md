# Setup Guide

Step-by-step instructions to set up and run the Document Intelligence Pipeline.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the API](#running-the-api)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Tesseract OCR**: For text extraction from images
- **Git**: For cloning the repository

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/document-intelligence-pipeline.git
cd document-intelligence-pipeline
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install Tesseract OCR

#### Windows

1. Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (tesseract-ocr-w64-setup-5.x.x.exe)
3. Add Tesseract to PATH:
   - Open System Properties → Advanced → Environment Variables
   - Edit "Path" variable
   - Add: `C:\Program Files\Tesseract-OCR`
4. Verify installation:
   ```powershell
   tesseract --version
   ```

#### macOS

```bash
# Using Homebrew
brew install tesseract

# Verify
tesseract --version
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

# Verify
tesseract --version
```

#### Linux (CentOS/RHEL/Fedora)

```bash
sudo yum install tesseract
# or
sudo dnf install tesseract
```

### Step 5: Install Language Data (Optional)

For non-English documents:

**Windows:**
- Download language data from [tessdata](https://github.com/tesseract-ocr/tessdata)
- Place `.traineddata` files in `C:\Program Files\Tesseract-OCR\tessdata`

**macOS/Linux:**
```bash
# Install specific language
sudo apt-get install tesseract-ocr-fra  # French
sudo apt-get install tesseract-ocr-spa  # Spanish
sudo apt-get install tesseract-ocr-deu  # German
```

---

## Configuration

### Step 1: Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Configure Environment Variables

Edit `.env` file with your settings:

```bash
# Required: OpenAI API Key
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-api-key-here

# Optional: OpenAI Model (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Optional: OCR Settings
OCR_ENGINE=tesseract
OCR_LANGUAGE=eng

# Optional: API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Optional: File Upload Limits
MAX_FILE_SIZE=52428800
```

### Step 3: Configure YAML Settings (Optional)

Edit `config.yaml` for fine-tuning:

```yaml
ocr:
  dpi: 300                    # Image resolution for OCR
  enhance_contrast: true      # Apply contrast enhancement
  languages:
    - eng                     # Primary language
    # - fra                   # Additional languages

extraction:
  model: gpt-4o-mini
  max_tokens: 2000
  temperature: 0.1            # Lower = more consistent

api:
  max_file_size: 52428800     # 50MB in bytes
  batch_size_limit: 10
```

---

## Running the API

### Option 1: Using PowerShell Script (Windows)

```powershell
.\run_api.ps1
```

### Option 2: Using Python Module

```bash
# From project root
python -m src.api
```

### Option 3: Using Uvicorn Directly

```bash
# Development with auto-reload
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify API is Running

Open browser or use curl:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "document_processor": "ready",
    "ocr_engine": "ready",
    "data_extractor": "ready"
  }
}
```

---

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_processor.py

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Manual Testing with curl

**Test document upload:**
```bash
# Create a test file first
echo "Invoice #12345 from Acme Corp" > test_invoice.txt

# Upload (replace with actual PDF/PNG for real testing)
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sample_docs/test_invoice.pdf" \
  -F "extract_data=true"
```

**Test with sample Python script:**
```python
import requests

# Upload
with open("sample_docs/invoice.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/documents/upload",
        files={"file": f},
        data={"extract_data": "true"}
    )

doc_id = response.json()["document_id"]
print(f"Document ID: {doc_id}")

# Get results
import time
time.sleep(5)  # Wait for processing

result = requests.get(f"http://localhost:8000/documents/{doc_id}")
print(result.json())
```

---

## Troubleshooting

### Common Issues

#### 1. "tesseract is not installed or it's not in your PATH"

**Solution:**
- Verify Tesseract is installed: `tesseract --version`
- Add Tesseract to system PATH
- On Windows, restart terminal after adding to PATH

#### 2. "OPENAI_API_KEY not found"

**Solution:**
- Create `.env` file from `.env.example`
- Add your OpenAI API key: `OPENAI_API_KEY=sk-...`
- Restart the API server

#### 3. "ModuleNotFoundError: No module named 'src'"

**Solution:**
- Ensure you're in the project root directory
- Run with: `python -m src.api`
- Or add to PYTHONPATH: `$env:PYTHONPATH="."` (PowerShell)

#### 4. PIL/Pillow Import Errors

**Solution:**
```bash
pip uninstall pillow
pip install --upgrade pillow
```

#### 5. PDF Processing Errors

**Solution:**
- Ensure pdfplumber is installed: `pip install pdfplumber`
- Check PDF is not corrupted or password-protected
- Try converting to images first

#### 6. "File too large" Error

**Solution:**
- Default limit is 50MB
- Increase in `.env`: `MAX_FILE_SIZE=104857600` (100MB)
- Or compress/optimize the document

#### 7. OCR Poor Quality Results

**Solution:**
- Increase DPI in config.yaml: `dpi: 400`
- Enable contrast enhancement: `enhance_contrast: true`
- Try EasyOCR fallback (auto-enabled)
- Pre-process images (deskew, denoise)

#### 8. API Returns 500 Errors

**Solution:**
- Check logs for detailed error messages
- Verify all dependencies are installed
- Check OpenAI API key is valid
- Ensure sufficient disk space and memory

### Getting Help

1. Check logs in terminal output
2. Review [API Documentation](API_DOCUMENTATION.md)
3. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - System information

---

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t doc-intel-pipeline .
docker run -p 8000:8000 --env-file .env doc-intel-pipeline
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./sample_docs:/app/sample_docs
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

---

## Next Steps

1. Add sample documents to `sample_docs/` folder
2. Test the API with your documents
3. Integrate with your application
4. Customize extraction models for your use case

For more information, see:
- [README.md](README.md) - Project overview
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
