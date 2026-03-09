"""
AI Data Extractor Module
Uses OpenAI GPT models to extract structured data from document text.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentCategory(Enum):
    """Categories of documents supported."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    RESUME = "resume"
    FORM = "form"
    UNKNOWN = "unknown"


class ExtractedField(BaseModel):
    """A single extracted field with confidence."""
    value: Any = Field(..., description="The extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source_text: Optional[str] = Field(None, description="Original text that produced this value")


class InvoiceData(BaseModel):
    """Structured data model for invoices."""
    document_type: str = Field(default="invoice", description="Type of document")
    vendor_name: Optional[ExtractedField] = Field(None, description="Company/vendor name")
    vendor_address: Optional[ExtractedField] = Field(None, description="Vendor address")
    invoice_number: Optional[ExtractedField] = Field(None, description="Invoice number")
    invoice_date: Optional[ExtractedField] = Field(None, description="Invoice date")
    due_date: Optional[ExtractedField] = Field(None, description="Payment due date")
    total_amount: Optional[ExtractedField] = Field(None, description="Total amount due")
    subtotal: Optional[ExtractedField] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[ExtractedField] = Field(None, description="Tax amount")
    currency: Optional[ExtractedField] = Field(None, description="Currency code (USD, EUR, etc.)")
    line_items: Optional[ExtractedField] = Field(None, description="List of line items")
    payment_terms: Optional[ExtractedField] = Field(None, description="Payment terms")
    notes: Optional[ExtractedField] = Field(None, description="Additional notes")


class ReceiptData(BaseModel):
    """Structured data model for receipts."""
    document_type: str = Field(default="receipt", description="Type of document")
    merchant_name: Optional[ExtractedField] = Field(None, description="Store/merchant name")
    merchant_address: Optional[ExtractedField] = Field(None, description="Merchant address")
    transaction_date: Optional[ExtractedField] = Field(None, description="Date of purchase")
    transaction_time: Optional[ExtractedField] = Field(None, description="Time of purchase")
    total_amount: Optional[ExtractedField] = Field(None, description="Total amount paid")
    subtotal: Optional[ExtractedField] = Field(None, description="Subtotal")
    tax_amount: Optional[ExtractedField] = Field(None, description="Tax amount")
    tip_amount: Optional[ExtractedField] = Field(None, description="Tip amount")
    payment_method: Optional[ExtractedField] = Field(None, description="Payment method used")
    items: Optional[ExtractedField] = Field(None, description="List of purchased items")
    receipt_number: Optional[ExtractedField] = Field(None, description="Receipt/transaction number")


class ContractData(BaseModel):
    """Structured data model for contracts."""
    document_type: str = Field(default="contract", description="Type of document")
    contract_title: Optional[ExtractedField] = Field(None, description="Title of contract")
    party_a_name: Optional[ExtractedField] = Field(None, description="First party name")
    party_b_name: Optional[ExtractedField] = Field(None, description="Second party name")
    effective_date: Optional[ExtractedField] = Field(None, description="When contract takes effect")
    expiration_date: Optional[ExtractedField] = Field(None, description="When contract expires")
    contract_value: Optional[ExtractedField] = Field(None, description="Total contract value")
    payment_terms: Optional[ExtractedField] = Field(None, description="Payment terms")
    termination_clause: Optional[ExtractedField] = Field(None, description="Termination conditions")
    governing_law: Optional[ExtractedField] = Field(None, description="Governing law jurisdiction")
    key_clauses: Optional[ExtractedField] = Field(None, description="Key contractual clauses")


@dataclass
class ExtractionResult:
    """Result of AI extraction."""
    category: DocumentCategory
    data: Dict[str, Any]
    confidence: float
    raw_response: str
    processing_time_ms: int
    model_used: str


class DataExtractor:
    """
    AI-powered data extraction from document text.
    Uses OpenAI GPT models for intelligent parsing.
    """
    
    # System prompts for different document types
    SYSTEM_PROMPTS = {
        DocumentCategory.INVOICE: """You are an expert invoice parser. Extract all relevant fields from the invoice text provided.
Return a JSON object with these fields (all optional except document_type):
- vendor_name: Company name
- vendor_address: Full address
- invoice_number: Invoice identifier
- invoice_date: Date issued (ISO format)
- due_date: Payment due date (ISO format)
- total_amount: Total amount (number)
- subtotal: Subtotal (number)
- tax_amount: Tax amount (number)
- currency: Currency code
- line_items: Array of {description, quantity, unit_price, total}
- payment_terms: Payment terms description
- notes: Additional notes

Each field should have: value, confidence (0-1), and source_text.
Be precise with dates and amounts.""",
        
        DocumentCategory.RECEIPT: """You are an expert receipt parser. Extract all relevant fields from the receipt text provided.
Return a JSON object with these fields:
- merchant_name: Store name
- merchant_address: Store address
- transaction_date: Purchase date (ISO format)
- transaction_time: Purchase time
- total_amount: Total paid (number)
- subtotal: Subtotal (number)
- tax_amount: Tax (number)
- tip_amount: Tip (number)
- payment_method: How paid
- items: Array of {name, quantity, price}
- receipt_number: Transaction ID

Each field should have: value, confidence (0-1), and source_text.""",
        
        DocumentCategory.CONTRACT: """You are an expert contract analyst. Extract key information from the contract text.
Return a JSON object with these fields:
- contract_title: Document title
- party_a_name: First party
- party_b_name: Second party
- effective_date: Start date (ISO format)
- expiration_date: End date (ISO format)
- contract_value: Total value (number)
- payment_terms: Payment schedule
- termination_clause: How to terminate
- governing_law: Jurisdiction
- key_clauses: Array of important clauses

Each field should have: value, confidence (0-1), and source_text."""
    }
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 max_tokens: int = 2000):
        """
        Initialize the data extractor.
        
        Args:
            api_key: OpenAI API key (or from env var OPENAI_API_KEY)
            model: Model to use for extraction
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        
        logger.info(f"DataExtractor initialized (model={model})")
    
    def classify_document(self, text: str) -> DocumentCategory:
        """
        Classify the document type based on content.
        
        Args:
            text: Document text content
            
        Returns:
            DocumentCategory enum value
        """
        # Simple keyword-based classification
        text_lower = text.lower()
        
        invoice_keywords = ['invoice', 'bill to', 'invoice number', 'payment due', 'terms']
        receipt_keywords = ['receipt', 'thank you', 'cashier', 'pos', 'store #', 'change']
        contract_keywords = ['agreement', 'contract', 'parties', 'hereby', 'witnesseth', 'clause']
        
        scores = {
            DocumentCategory.INVOICE: sum(1 for kw in invoice_keywords if kw in text_lower),
            DocumentCategory.RECEIPT: sum(1 for kw in receipt_keywords if kw in text_lower),
            DocumentCategory.CONTRACT: sum(1 for kw in contract_keywords if kw in text_lower),
        }
        
        best_match = max(scores, key=scores.get)
        
        if scores[best_match] == 0:
            return DocumentCategory.UNKNOWN
        
        return best_match
    
    def extract(self, 
                text: str,
                category: Optional[DocumentCategory] = None) -> ExtractionResult:
        """
        Extract structured data from document text.
        
        Args:
            text: Document text content
            category: Optional document category (auto-detected if not provided)
            
        Returns:
            ExtractionResult with structured data
        """
        import time
        start_time = time.time()
        
        # Auto-classify if category not provided
        if category is None:
            category = self.classify_document(text)
            logger.info(f"Auto-classified document as: {category.value}")
        
        # Get appropriate system prompt
        system_prompt = self.SYSTEM_PROMPTS.get(
            category, 
            self.SYSTEM_PROMPTS[DocumentCategory.INVOICE]
        )
        
        # Truncate text if too long
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract data from this document:\n\n{truncated_text}"}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                data = json.loads(raw_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {raw_response[:200]}")
                data = {"error": "Failed to parse response", "raw": raw_response}
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(data)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ExtractionResult(
                category=category,
                data=data,
                confidence=confidence,
                raw_response=raw_response,
                processing_time_ms=processing_time,
                model_used=self.model
            )
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return ExtractionResult(
                category=category,
                data={"error": str(e)},
                confidence=0.0,
                raw_response="",
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate overall confidence from field confidences."""
        confidences = []
        
        for key, value in data.items():
            if isinstance(value, dict) and 'confidence' in value:
                confidences.append(value['confidence'])
        
        if not confidences:
            return 0.5  # Default confidence
        
        return sum(confidences) / len(confidences)
    
    def batch_extract(self, 
                      texts: List[str]) -> List[ExtractionResult]:
        """
        Process multiple documents in batch.
        
        Args:
            texts: List of document texts
            
        Returns:
            List of ExtractionResult objects
        """
        results = []
        for i, text in enumerate(texts):
            logger.info(f"Processing document {i + 1}/{len(texts)}")
            result = self.extract(text)
            results.append(result)
        return results
