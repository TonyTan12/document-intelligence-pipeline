"""
Document Processor Module
Handles PDF and image ingestion with preprocessing capabilities.
"""

import os
import io
import logging
from pathlib import Path
from typing import Union, List, BinaryIO, Optional
from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pdfplumber
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types."""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"


@dataclass
class ProcessedDocument:
    """Result of document processing."""
    filename: str
    document_type: DocumentType
    text_content: str
    page_count: int
    images: List[Image.Image]
    metadata: dict
    raw_bytes: bytes


class DocumentProcessor:
    """
    Handles document ingestion and preprocessing.
    Supports PDFs and common image formats.
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    
    def __init__(self, dpi: int = 300, enhance_contrast: bool = True):
        """
        Initialize the document processor.
        
        Args:
            dpi: DPI for image conversion (higher = better OCR)
            enhance_contrast: Whether to apply contrast enhancement
        """
        self.dpi = dpi
        self.enhance_contrast = enhance_contrast
        logger.info(f"DocumentProcessor initialized (dpi={dpi}, enhance={enhance_contrast})")
    
    def process_file(self, file_path: Union[str, Path]) -> ProcessedDocument:
        """
        Process a document file from disk.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessedDocument with extracted content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()
        
        return self.process_bytes(raw_bytes, file_path.name)
    
    def process_bytes(self, data: bytes, filename: str) -> ProcessedDocument:
        """
        Process document from bytes.
        
        Args:
            data: Raw file bytes
            filename: Original filename
            
        Returns:
            ProcessedDocument with extracted content
        """
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf':
            return self._process_pdf(data, filename)
        else:
            return self._process_image(data, filename)
    
    def _process_pdf(self, data: bytes, filename: str) -> ProcessedDocument:
        """Process PDF document."""
        logger.info(f"Processing PDF: {filename}")
        
        text_content = ""
        images = []
        metadata = {}
        
        # Extract text and metadata using pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            metadata = {
                'total_pages': len(pdf.pages),
                'pdf_info': pdf.metadata or {}
            }
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                text_content += f"\n--- Page {i + 1} ---\n{page_text}"
                
                # Convert page to image for OCR backup
                try:
                    page_image = page.to_image(resolution=self.dpi).original
                    if self.enhance_contrast:
                        page_image = self._enhance_image(page_image)
                    images.append(page_image)
                except Exception as e:
                    logger.warning(f"Could not convert page {i + 1} to image: {e}")
        
        # Also try PyPDF2 for additional metadata
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            metadata['pypdf_info'] = reader.metadata
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
        
        return ProcessedDocument(
            filename=filename,
            document_type=DocumentType.PDF,
            text_content=text_content.strip(),
            page_count=len(images),
            images=images,
            metadata=metadata,
            raw_bytes=data
        )
    
    def _process_image(self, data: bytes, filename: str) -> ProcessedDocument:
        """Process image document."""
        logger.info(f"Processing image: {filename}")
        
        image = Image.open(io.BytesIO(data))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Apply enhancements
        if self.enhance_contrast:
            image = self._enhance_image(image)
        
        # Extract basic metadata
        metadata = {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'dpi': image.info.get('dpi', 'unknown')
        }
        
        return ProcessedDocument(
            filename=filename,
            document_type=DocumentType(image.format.lower() if image.format else 'png'),
            text_content="",  # Will be populated by OCR
            page_count=1,
            images=[image],
            metadata=metadata,
            raw_bytes=data
        )
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply image enhancements for better OCR."""
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file is valid and supported.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if valid, False otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False
        
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_path.stat().st_size > max_size:
            logger.warning(f"File too large: {file_path}")
            return False
        
        return True
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported file extensions."""
        return list(self.SUPPORTED_EXTENSIONS)
