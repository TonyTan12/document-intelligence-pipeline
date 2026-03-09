"""
OCR Engine Module
Handles text extraction from images using Tesseract and EasyOCR.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import pytesseract
import numpy as np

# Try to import EasyOCR, fallback to Tesseract only if not available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    bounding_boxes: List[Dict]
    engine: str
    language: str


@dataclass
class TextRegion:
    """A detected text region with metadata."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    

class OCREngine:
    """
    OCR engine supporting both Tesseract and EasyOCR.
    Automatically selects best engine based on content.
    """
    
    def __init__(self, 
                 primary_engine: str = "tesseract",
                 languages: List[str] = None,
                 use_easyocr_fallback: bool = True):
        """
        Initialize OCR engine.
        
        Args:
            primary_engine: 'tesseract' or 'easyocr'
            languages: List of language codes (e.g., ['eng', 'fra'])
            use_easyocr_fallback: Whether to fallback to EasyOCR on poor results
        """
        self.primary_engine = primary_engine
        self.languages = languages or ['eng']
        self.use_easyocr_fallback = use_easyocr_fallback and EASYOCR_AVAILABLE
        self._easyocr_reader = None
        
        logger.info(f"OCREngine initialized (primary={primary_engine}, languages={self.languages})")
        
        # Validate Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            if not EASYOCR_AVAILABLE:
                raise RuntimeError("No OCR engine available. Install Tesseract or EasyOCR.")
    
    def _get_easyocr_reader(self):
        """Lazy initialization of EasyOCR reader."""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            logger.info("Initializing EasyOCR reader...")
            self._easyocr_reader = easyocr.Reader(
                self.languages,
                gpu=False,  # CPU mode for compatibility
                verbose=False
            )
        return self._easyocr_reader
    
    def extract_text(self, 
                     image: Image.Image,
                     return_regions: bool = False) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image: PIL Image to process
            return_regions: Whether to return individual text regions
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if self.primary_engine == "tesseract":
            result = self._extract_with_tesseract(image, return_regions)
            
            # Fallback to EasyOCR if confidence is low
            if (self.use_easyocr_fallback and 
                result.confidence < 0.6 and 
                EASYOCR_AVAILABLE):
                logger.info("Tesseract confidence low, trying EasyOCR fallback")
                result = self._extract_with_easyocr(image, return_regions)
                
        else:
            result = self._extract_with_easyocr(image, return_regions)
        
        return result
    
    def _extract_with_tesseract(self, 
                                 image: Image.Image,
                                 return_regions: bool = False) -> OCRResult:
        """Extract text using Tesseract OCR."""
        lang_str = '+'.join(self.languages)
        
        # Get detailed data including bounding boxes
        data = pytesseract.image_to_data(
            image,
            lang=lang_str,
            output_type=pytesseract.Output.DICT
        )
        
        # Build text and collect regions
        text_parts = []
        regions = []
        total_confidence = []
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            conf = int(data['conf'][i])
            if conf > 30:  # Filter low confidence
                text = data['text'][i].strip()
                if text:
                    text_parts.append(text)
                    total_confidence.append(conf)
                    
                    if return_regions:
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        regions.append(TextRegion(
                            text=text,
                            confidence=conf / 100.0,
                            bbox=(x, y, x + w, y + h)
                        ))
        
        full_text = ' '.join(text_parts)
        avg_confidence = (sum(total_confidence) / len(total_confidence) / 100.0 
                         if total_confidence else 0.0)
        
        bounding_boxes = [
            {
                'text': r.text,
                'confidence': r.confidence,
                'bbox': r.bbox
            }
            for r in regions
        ]
        
        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            bounding_boxes=bounding_boxes,
            engine='tesseract',
            language=lang_str
        )
    
    def _extract_with_easyocr(self,
                               image: Image.Image,
                               return_regions: bool = False) -> OCRResult:
        """Extract text using EasyOCR."""
        if not EASYOCR_AVAILABLE:
            raise RuntimeError("EasyOCR not available")
        
        reader = self._get_easyocr_reader()
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run OCR
        results = reader.readtext(img_array, detail=1)
        
        text_parts = []
        regions = []
        total_confidence = []
        
        for detection in results:
            bbox, text, conf = detection
            text_parts.append(text)
            total_confidence.append(conf)
            
            if return_regions:
                # Convert bbox to x1,y1,x2,y2 format
                pts = [(int(p[0]), int(p[1])) for p in bbox]
                x_coords = [p[0] for p in pts]
                y_coords = [p[1] for p in pts]
                regions.append(TextRegion(
                    text=text,
                    confidence=conf,
                    bbox=(min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                ))
        
        full_text = ' '.join(text_parts)
        avg_confidence = sum(total_confidence) / len(total_confidence) if total_confidence else 0.0
        
        bounding_boxes = [
            {
                'text': r.text,
                'confidence': r.confidence,
                'bbox': r.bbox
            }
            for r in regions
        ]
        
        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            bounding_boxes=bounding_boxes,
            engine='easyocr',
            language='+'.join(self.languages)
        )
    
    def batch_extract(self, 
                      images: List[Image.Image]) -> List[OCRResult]:
        """
        Process multiple images in batch.
        
        Args:
            images: List of PIL Images
            
        Returns:
            List of OCRResult objects
        """
        results = []
        for i, img in enumerate(images):
            logger.info(f"Processing image {i + 1}/{len(images)}")
            result = self.extract_text(img)
            results.append(result)
        return results
    
    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing optimizations for better OCR.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Apply adaptive thresholding using numpy
        img_array = np.array(image)
        
        # Simple binary threshold
        _, binary = cv2.threshold(
            img_array, 0, 255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        ) if 'cv2' in globals() else (None, img_array)
        
        if 'cv2' in globals():
            return Image.fromarray(binary)
        
        return image


# Try to import cv2 for advanced preprocessing
try:
    import cv2
except ImportError:
    cv2 = None
    logger.warning("OpenCV not available. Some preprocessing features disabled.")
