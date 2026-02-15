"""
Financial Validator Module
Validates extracted transaction data for correctness and completeness.
"""

import logging
from datetime import datetime
from typing import Optional
from extractors.regex_extractor import Transaction

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class TransactionValidator:
    """Validates transaction data."""
    
    def __init__(
        self, 
        strict_mode: bool = False,
        allow_zero_amounts: bool = False,
        min_description_length: int = 2
    ):
        """
        Initialize validator with configurable settings.
        
        Args:
            strict_mode: If True, raise exceptions on invalid data.
                        If False, log warnings and skip invalid transactions.
            allow_zero_amounts: If True, allow transactions with 0 amount.
            min_description_length: Minimum characters required in description.
        
        Note: No maximum amount validation - business transactions can be millions/billions!
        """
        self.strict_mode = strict_mode
        self.allow_zero_amounts = allow_zero_amounts
        self.min_description_length = min_description_length
        
        self.validation_stats = {
            "total_validated": 0,
            "valid": 0,
            "invalid": 0,
            "invalid_date": 0,
            "invalid_amount": 0,
            "invalid_description": 0,
            "invalid_category": 0
        }
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate a single transaction.
        
        Args:
            transaction: Transaction object to validate
            
        Returns:
            True if valid, False if invalid
            
        Raises:
            ValidationError: If strict_mode is True and validation fails
        """
        self.validation_stats["total_validated"] += 1
        
        # Validate date
        if not self._validate_date(transaction.date):
            self.validation_stats["invalid_date"] += 1
            self.validation_stats["invalid"] += 1
            msg = f"Invalid date: {transaction.date}"
            if self.strict_mode:
                raise ValidationError(msg)
            logger.warning(f"{msg} in transaction: {transaction}")
            return False
        
        # Validate amount
        if not self._validate_amount(transaction.amount):
            self.validation_stats["invalid_amount"] += 1
            self.validation_stats["invalid"] += 1
            msg = f"Invalid amount: {transaction.amount}"
            if self.strict_mode:
                raise ValidationError(msg)
            logger.warning(f"{msg} in transaction: {transaction}")
            return False
        
        # Validate description
        if not self._validate_description(transaction.description):
            self.validation_stats["invalid_description"] += 1
            self.validation_stats["invalid"] += 1
            msg = f"Invalid description: empty or too short"
            if self.strict_mode:
                raise ValidationError(msg)
            logger.warning(f"{msg} in transaction: {transaction}")
            return False
        
        # Validate type and category
        if not self._validate_type_and_category(transaction.type, transaction.category):
            self.validation_stats["invalid_category"] += 1
            self.validation_stats["invalid"] += 1
            msg = f"Invalid type/category: {transaction.type}/{transaction.category}"
            if self.strict_mode:
                raise ValidationError(msg)
            logger.warning(f"{msg} in transaction: {transaction}")
            return False
        
        self.validation_stats["valid"] += 1
        return True
    
    def validate_transactions(self, transactions: list[Transaction]) -> list[Transaction]:
        """
        Validate a list of transactions.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            List of valid transactions (invalid ones filtered out)
        """
        valid_transactions = []
        
        for txn in transactions:
            if self.validate_transaction(txn):
                valid_transactions.append(txn)
        
        logger.info(
            f"Validation complete: {self.validation_stats['valid']} valid, "
            f"{self.validation_stats['invalid']} invalid out of "
            f"{self.validation_stats['total_validated']} total"
        )
        
        return valid_transactions
    
    def _validate_date(self, date_str: str) -> bool:
        """
        Validate date string.
        
        Supports formats:
        - MM/DD/YYYY (4-digit year)
        - MM/DD/YY (2-digit year)
        - MM/DD (no year, assumes current year)
        - MM-DD-YYYY (with hyphens, 4-digit year)
        - MM-DD-YY (with hyphens, 2-digit year)
        - YYYY-MM-DD (ISO format)
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        # List of supported date formats
        date_formats = [
            '%m/%d/%Y',    # MM/DD/YYYY
            '%m/%d/%y',    # MM/DD/YY (NEW - supports 2-digit year)
            '%m/%d',       # MM/DD
            '%m-%d-%Y',    # MM-DD-YYYY
            '%m-%d-%y',    # MM-DD-YY
            '%Y-%m-%d'     # YYYY-MM-DD
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _validate_amount(self, amount: float) -> bool:
        """
        Validate amount with configurable settings.
        
        Must be:
        - A number
        - Non-zero (unless allow_zero_amounts is True)
        - Within reasonable range (configurable max_amount)
        """
        if not isinstance(amount, (int, float)):
            return False
        
        # Check if zero (configurable)
        if amount == 0:
            if not self.allow_zero_amounts:
                logger.debug("Amount is zero (rejected - allow_zero_amounts=False)")
                return False
            else:
                logger.debug("Amount is zero (accepted - allow_zero_amounts=True)")
        
        # NO MAX AMOUNT CHECK - Business transactions can be millions or billions!
        # We don't reject based on amount size, only based on description keywords in the extractor.
        
        return True
    
    def _validate_description(self, description: str) -> bool:
        """
        Validate description with configurable minimum length.
        
        Must be:
        - Non-empty
        - At least min_description_length characters (configurable)
        - String type
        """
        if not isinstance(description, str):
            return False
        
        if not description.strip():
            return False
        
        # Use configurable minimum length
        if len(description.strip()) < self.min_description_length:
            logger.debug(f"Description too short: '{description}' (min: {self.min_description_length})")
            return False
        
        return True
    
    def _validate_type_and_category(self, txn_type: str, category: Optional[str]) -> bool:
        """
        Validate transaction type and category.
        
        Type must be 'credit', 'debit', or 'unknown'
        Category should be present unless type is 'unknown'
        """
        valid_types = {"credit", "debit", "unknown"}
        
        if txn_type not in valid_types:
            return False
        
        # If type is unknown, it's acceptable if category is None
        if txn_type == "unknown":
            logger.debug("Transaction type is unknown - may need review")
            # We can choose to accept or reject unknown types
            # For now, we'll reject them to ensure quality
            return False
        
        # For credit/debit, category should be present
        if category is None or not category.strip():
            logger.warning(f"Transaction type {txn_type} but no category specified")
            # Still valid, just log warning
        
        return True
    
    def get_stats(self) -> dict:
        """Get validation statistics."""
        return self.validation_stats.copy()
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            "total_validated": 0,
            "valid": 0,
            "invalid": 0,
            "invalid_date": 0,
            "invalid_amount": 0,
            "invalid_description": 0,
            "invalid_category": 0
        }


def validate_transactions(transactions: list[Transaction], strict_mode: bool = False) -> list[Transaction]:
    """
    Convenience function to validate a list of transactions.
    
    Args:
        transactions: List of Transaction objects
        strict_mode: If True, raise exceptions on invalid data
        
    Returns:
        List of valid transactions
    """
    validator = TransactionValidator(strict_mode=strict_mode)
    return validator.validate_transactions(transactions)
