"""
Pydantic Models Module
Data models and schemas for the Document Intelligence Pipeline.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class ProcessingStatus(str, Enum):
    """Processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"


class ExtractedField(BaseModel):
    """Schema for an extracted field."""
    value: Any = Field(..., description="The extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    source_text: Optional[str] = Field(None, description="Original text snippet")


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    document_type: Optional[DocumentType] = Field(None, description="Optional document type hint")
    extract_data: bool = Field(True, description="Whether to run AI extraction")
    language: str = Field("eng", description="OCR language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "pdf",
                "extract_data": True,
                "language": "eng"
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "filename": "invoice.pdf",
                "status": "processing",
                "message": "Document uploaded successfully, processing started"
            }
        }


class OCRResult(BaseModel):
    """OCR extraction result."""
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    engine: str = Field(..., description="OCR engine used")
    page_count: int = Field(1, description="Number of pages processed")
    language: str = Field("eng", description="Language used")


class ExtractedData(BaseModel):
    """AI-extracted structured data."""
    document_type: str = Field(..., description="Detected document category")
    fields: Dict[str, ExtractedField] = Field(..., description="Extracted fields")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    model_used: str = Field(..., description="AI model used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class DocumentResult(BaseModel):
    """Complete document processing result."""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    status: ProcessingStatus = Field(..., description="Processing status")
    document_type: Optional[str] = Field(None, description="Detected document type")
    ocr_result: Optional[OCRResult] = Field(None, description="OCR extraction results")
    extracted_data: Optional[ExtractedData] = Field(None, description="AI-extracted data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "filename": "invoice.pdf",
                "status": "completed",
                "document_type": "invoice",
                "ocr_result": {
                    "text": "Invoice #123...",
                    "confidence": 0.95,
                    "engine": "tesseract",
                    "page_count": 1,
                    "language": "eng"
                },
                "extracted_data": {
                    "document_type": "invoice",
                    "fields": {
                        "vendor_name": {
                            "value": "Acme Corp",
                            "confidence": 0.92,
                            "source_text": "Acme Corp - Invoice"
                        }
                    },
                    "confidence": 0.88,
                    "model_used": "gpt-4o-mini",
                    "processing_time_ms": 1250
                },
                "created_at": "2024-01-15T10:30:00Z",
                "processed_at": "2024-01-15T10:30:02Z"
            }
        }


class BatchUploadRequest(BaseModel):
    """Request for batch document processing."""
    extract_data: bool = Field(True, description="Whether to run AI extraction")
    language: str = Field("eng", description="OCR language code")


class BatchUploadResponse(BaseModel):
    """Response for batch upload."""
    batch_id: str = Field(..., description="Batch identifier")
    document_count: int = Field(..., description="Number of documents")
    documents: List[DocumentUploadResponse] = Field(..., description="Individual document responses")
    

class BatchResult(BaseModel):
    """Complete batch processing result."""
    batch_id: str = Field(..., description="Batch identifier")
    status: ProcessingStatus = Field(..., description="Overall batch status")
    total_documents: int = Field(..., description="Total documents in batch")
    completed: int = Field(0, description="Successfully processed")
    failed: int = Field(0, description="Failed documents")
    results: List[DocumentResult] = Field(..., description="Individual results")


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = Field("healthy", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")
    components: Dict[str, str] = Field(default_factory=dict, description="Component statuses")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
