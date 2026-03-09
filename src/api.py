"""
FastAPI Application
REST API endpoints for the Document Intelligence Pipeline.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    DocumentUploadResponse, DocumentResult, BatchUploadResponse,
    BatchResult, HealthResponse, ErrorResponse, ProcessingStatus,
    OCRResult, ExtractedData, ExtractedField
)
from .document_processor import DocumentProcessor
from .ocr_engine import OCREngine
from .extractor import DataExtractor, DocumentCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage (replace with database in production)
document_store = {}
batch_store = {}

# Global processors
doc_processor: Optional[DocumentProcessor] = None
ocr_engine: Optional[OCREngine] = None
data_extractor: Optional[DataExtractor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global doc_processor, ocr_engine, data_extractor
    
    # Startup
    logger.info("Starting Document Intelligence Pipeline API...")
    
    doc_processor = DocumentProcessor(dpi=300, enhance_contrast=True)
    ocr_engine = OCREngine(
        primary_engine="tesseract",
        languages=["eng"],
        use_easyocr_fallback=True
    )
    
    try:
        data_extractor = DataExtractor(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        )
        logger.info("Data extractor initialized")
    except ValueError as e:
        logger.warning(f"Data extractor not available: {e}")
        data_extractor = None
    
    logger.info("API ready!")
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    document_store.clear()
    batch_store.clear()


# Create FastAPI app
app = FastAPI(
    title="Document Intelligence Pipeline API",
    description="""
    AI-powered document processing API that extracts structured data from 
    invoices, receipts, contracts, and other documents using OCR and GPT models.
    
    ## Features
    
    * **Document Upload**: Support for PDF, PNG, JPG, TIFF, BMP
    * **OCR Processing**: Extract text from images and scanned documents
    * **AI Extraction**: Intelligent data extraction using GPT-4o-mini
    * **Batch Processing**: Process multiple documents at once
    * **Confidence Scoring**: Quality metrics for all extractions
    
    ## Supported Documents
    
    * Invoices
    * Receipts
    * Contracts
    * Forms
    * General documents
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API info."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        components={
            "document_processor": "ready" if doc_processor else "unavailable",
            "ocr_engine": "ready" if ocr_engine else "unavailable",
            "data_extractor": "ready" if data_extractor else "unavailable"
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return await root()


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPG)"),
    extract_data: bool = Form(True, description="Enable AI data extraction"),
    language: str = Form("eng", description="OCR language code")
):
    """
    Upload and process a single document.
    
    The document will be processed asynchronously. Use the returned document_id
    to check processing status and retrieve results.
    
    - **file**: Document file (PDF, PNG, JPG, TIFF, BMP)
    - **extract_data**: Whether to run AI extraction (default: true)
    - **language**: OCR language code, e.g., 'eng', 'fra' (default: 'eng')
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_extensions}"
        )
    
    # Generate document ID
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Read file content
    content = await file.read()
    
    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    # Store document info
    document_store[doc_id] = {
        "document_id": doc_id,
        "filename": file.filename,
        "status": ProcessingStatus.PROCESSING,
        "content": content,
        "extract_data": extract_data,
        "language": language,
        "created_at": datetime.utcnow(),
        "result": None
    }
    
    # Process in background
    background_tasks.add_task(process_document, doc_id)
    
    logger.info(f"Document uploaded: {doc_id} ({file.filename})")
    
    return DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename,
        status=ProcessingStatus.PROCESSING,
        message="Document uploaded successfully, processing started"
    )


@app.get("/documents/{document_id}", response_model=DocumentResult)
async def get_document_result(document_id: str):
    """
    Get processing results for a document.
    
    Returns the complete processing result including OCR text and 
    AI-extracted structured data (if extraction was enabled).
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_store[document_id]
    result = doc.get("result")
    
    if result:
        return result
    
    # Return pending status
    return DocumentResult(
        document_id=document_id,
        filename=doc["filename"],
        status=doc["status"],
        created_at=doc["created_at"]
    )


@app.post("/documents/batch", response_model=BatchUploadResponse)
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple document files"),
    extract_data: bool = Form(True, description="Enable AI data extraction"),
    language: str = Form("eng", description="OCR language code")
):
    """
    Upload and process multiple documents in batch.
    
    - **files**: List of document files
    - **extract_data**: Whether to run AI extraction (default: true)
    - **language**: OCR language code (default: 'eng')
    
    Maximum 10 files per batch, 50MB each.
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
    
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    doc_responses = []
    doc_ids = []
    
    for file in files:
        if not file.filename:
            continue
            
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}:
            continue
        
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        content = await file.read()
        
        if len(content) > 50 * 1024 * 1024:
            continue
        
        document_store[doc_id] = {
            "document_id": doc_id,
            "filename": file.filename,
            "status": ProcessingStatus.PROCESSING,
            "content": content,
            "extract_data": extract_data,
            "language": language,
            "batch_id": batch_id,
            "created_at": datetime.utcnow(),
            "result": None
        }
        
        doc_ids.append(doc_id)
        doc_responses.append(DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            status=ProcessingStatus.PROCESSING,
            message="Processing started"
        ))
        
        background_tasks.add_task(process_document, doc_id)
    
    batch_store[batch_id] = {
        "batch_id": batch_id,
        "document_ids": doc_ids,
        "status": ProcessingStatus.PROCESSING,
        "created_at": datetime.utcnow()
    }
    
    logger.info(f"Batch uploaded: {batch_id} ({len(doc_ids)} documents)")
    
    return BatchUploadResponse(
        batch_id=batch_id,
        document_count=len(doc_responses),
        documents=doc_responses
    )


@app.get("/batch/{batch_id}", response_model=BatchResult)
async def get_batch_result(batch_id: str):
    """Get results for a batch of documents."""
    if batch_id not in batch_store:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch = batch_store[batch_id]
    results = []
    completed = 0
    failed = 0
    
    for doc_id in batch["document_ids"]:
        if doc_id in document_store:
            doc = document_store[doc_id]
            if doc["result"]:
                results.append(doc["result"])
                if doc["result"].status == ProcessingStatus.COMPLETED:
                    completed += 1
                elif doc["result"].status == ProcessingStatus.FAILED:
                    failed += 1
    
    status = ProcessingStatus.PROCESSING
    if completed + failed == len(batch["document_ids"]):
        status = ProcessingStatus.COMPLETED if failed == 0 else ProcessingStatus.FAILED
    
    return BatchResult(
        batch_id=batch_id,
        status=status,
        total_documents=len(batch["document_ids"]),
        completed=completed,
        failed=failed,
        results=results
    )


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its results."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    del document_store[document_id]
    logger.info(f"Document deleted: {document_id}")
    
    return {"message": "Document deleted successfully"}


async def process_document(doc_id: str):
    """Background task to process a document."""
    doc = document_store.get(doc_id)
    if not doc:
        return
    
    try:
        logger.info(f"Processing document: {doc_id}")
        
        # Process document
        processed = doc_processor.process_bytes(
            doc["content"], 
            doc["filename"]
        )
        
        # OCR processing
        ocr_text_parts = []
        ocr_confidences = []
        
        if processed.images:
            for img in processed.images:
                ocr_result = ocr_engine.extract_text(img)
                ocr_text_parts.append(ocr_result.text)
                ocr_confidences.append(ocr_result.confidence)
        
        # Use PDF text if available, otherwise use OCR
        if processed.text_content.strip():
            full_text = processed.text_content
        else:
            full_text = "\n".join(ocr_text_parts)
        
        avg_ocr_conf = sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 0.0
        
        ocr_result_model = OCRResult(
            text=full_text[:5000],  # Limit stored text
            confidence=avg_ocr_conf,
            engine="tesseract",
            page_count=processed.page_count,
            language=doc["language"]
        )
        
        # AI extraction
        extracted_data_model = None
        if doc["extract_data"] and data_extractor and full_text.strip():
            try:
                extraction = data_extractor.extract(full_text)
                
                # Convert to model format
                fields = {}
                for key, value in extraction.data.items():
                    if isinstance(value, dict) and "value" in value:
                        fields[key] = ExtractedField(
                            value=value["value"],
                            confidence=value.get("confidence", 0.5),
                            source_text=value.get("source_text")
                        )
                
                extracted_data_model = ExtractedData(
                    document_type=extraction.category.value,
                    fields=fields,
                    confidence=extraction.confidence,
                    model_used=extraction.model_used,
                    processing_time_ms=extraction.processing_time_ms
                )
            except Exception as e:
                logger.error(f"AI extraction failed for {doc_id}: {e}")
        
        # Build result
        result = DocumentResult(
            document_id=doc_id,
            filename=doc["filename"],
            status=ProcessingStatus.COMPLETED,
            document_type=extracted_data_model.document_type if extracted_data_model else None,
            ocr_result=ocr_result_model,
            extracted_data=extracted_data_model,
            created_at=doc["created_at"],
            processed_at=datetime.utcnow()
        )
        
        doc["status"] = ProcessingStatus.COMPLETED
        doc["result"] = result
        
        logger.info(f"Document completed: {doc_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed {doc_id}: {e}")
        doc["status"] = ProcessingStatus.FAILED
        doc["result"] = DocumentResult(
            document_id=doc_id,
            filename=doc["filename"],
            status=ProcessingStatus.FAILED,
            error_message=str(e),
            created_at=doc["created_at"],
            processed_at=datetime.utcnow()
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )
