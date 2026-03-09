"""
Tests for Document Processor
"""

import unittest
import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_processor import DocumentProcessor, DocumentType, ProcessedDocument


class TestDocumentProcessor(unittest.TestCase):
    """Test cases for DocumentProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor(dpi=200, enhance_contrast=True)
    
    def test_supported_extensions(self):
        """Test that supported extensions are defined."""
        extensions = self.processor.get_supported_types()
        self.assertIn('.pdf', extensions)
        self.assertIn('.png', extensions)
        self.assertIn('.jpg', extensions)
    
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file."""
        result = self.processor.validate_file("/nonexistent/file.pdf")
        self.assertFalse(result)
    
    @patch('document_processor.pytesseract')
    @patch('document_processor.pdfplumber')
    def test_process_image_bytes(self, mock_pdfplumber, mock_tesseract):
        """Test processing image from bytes."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        result = self.processor.process_bytes(img_bytes.read(), "test.png")
        
        self.assertEqual(result.filename, "test.png")
        self.assertEqual(result.document_type, DocumentType.PNG)
        self.assertEqual(result.page_count, 1)
        self.assertEqual(len(result.images), 1)
    
    def test_process_bytes_unsupported_type(self):
        """Test processing unsupported file type."""
        with self.assertRaises(ValueError):
            self.processor.process_bytes(b"test", "file.xyz")
    
    @patch('document_processor.pytesseract')
    @patch('document_processor.pdfplumber')
    def test_enhance_image(self, mock_pdfplumber, mock_tesseract):
        """Test image enhancement."""
        img = Image.new('RGB', (100, 100), color='gray')
        enhanced = self.processor._enhance_image(img)
        
        self.assertIsInstance(enhanced, Image.Image)
        self.assertEqual(enhanced.size, (100, 100))


class TestOCREngine(unittest.TestCase):
    """Test cases for OCREngine."""
    
    @patch('ocr_engine.pytesseract')
    def setUp(self, mock_tesseract):
        """Set up test fixtures."""
        mock_tesseract.get_tesseract_version.return_value = "5.0.0"
        
        from ocr_engine import OCREngine
        self.engine = OCREngine(primary_engine="tesseract", languages=["eng"])
    
    @patch('ocr_engine.pytesseract')
    def test_extract_text_tesseract(self, mock_tesseract):
        """Test text extraction with Tesseract."""
        # Mock Tesseract output
        mock_tesseract.image_to_data.return_value = {
            'text': ['Hello', 'World'],
            'conf': [95, 90],
            'left': [10, 50],
            'top': [10, 10],
            'width': [30, 40],
            'height': [20, 20]
        }
        
        img = Image.new('RGB', (100, 100), color='white')
        result = self.engine.extract_text(img)
        
        self.assertIn("Hello", result.text)
        self.assertIn("World", result.text)
        self.assertEqual(result.engine, "tesseract")


class TestDataExtractor(unittest.TestCase):
    """Test cases for DataExtractor."""
    
    @patch('extractor.OpenAI')
    def setUp(self, mock_openai_class):
        """Set up test fixtures."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        from extractor import DataExtractor
        self.extractor = DataExtractor(api_key="test-key", model="gpt-4o-mini")
    
    def test_classify_invoice(self):
        """Test invoice classification."""
        text = "Invoice #123 Bill To: Customer Payment Due: 30 days"
        from extractor import DocumentCategory
        
        category = self.extractor.classify_document(text)
        self.assertEqual(category, DocumentCategory.INVOICE)
    
    def test_classify_receipt(self):
        """Test receipt classification."""
        text = "Thank you for your purchase! Store #123 Cashier: John"
        from extractor import DocumentCategory
        
        category = self.extractor.classify_document(text)
        self.assertEqual(category, DocumentCategory.RECEIPT)
    
    def test_classify_contract(self):
        """Test contract classification."""
        text = "Agreement between parties hereby witnesseth clause 1"
        from extractor import DocumentCategory
        
        category = self.extractor.classify_document(text)
        self.assertEqual(category, DocumentCategory.CONTRACT)
    
    def test_classify_unknown(self):
        """Test unknown document classification."""
        text = "Random text with no keywords"
        from extractor import DocumentCategory
        
        category = self.extractor.classify_document(text)
        self.assertEqual(category, DocumentCategory.UNKNOWN)


class TestAPI(unittest.TestCase):
    """Test cases for API endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint exists."""
        # This would require FastAPI test client in real implementation
        pass


if __name__ == '__main__':
    unittest.main()
