"""
Base parser class for all order sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.mapping_utils import MappingUtils

class BaseParser(ABC):
    """Base class for all order parsers"""
    
    def __init__(self):
        self.mapping_utils = MappingUtils()
    
    @abstractmethod
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse the uploaded file and extract order data
        
        Args:
            file_content: Raw file content in bytes
            file_extension: File extension (html, csv, xlsx)
            filename: Original filename
            
        Returns:
            List of dictionaries containing parsed order data
        """
        pass
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that required fields are present in the data"""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        return True
    
    def clean_numeric_value(self, value: str) -> float:
        """Clean and convert string to numeric value"""
        if not value:
            return 0.0
        
        # Remove common currency symbols and formatting
        cleaned = str(value).replace('$', '').replace(',', '').replace('£', '').replace('€', '').strip()
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format"""
        if not date_str:
            return None
            
        import datetime
        
        # Common date formats to try
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',  # Added for 07/25/25 format
            '%d/%m/%Y',
            '%d/%m/%y',  # Added for day/month/year short format
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%B %d, %Y',
            '%d-%m-%Y',
            '%Y%m%d'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.datetime.strptime(str(date_str).strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
