"""
Financial Rules Module
Defines credit/debit category detection and sign application rules.
"""

from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction type enumeration."""
    CREDIT = "credit"
    DEBIT = "debit"
    UNKNOWN = "unknown"


class CategoryState:
    """
    Tracks the current category context while parsing bank statements.
    Determines whether transactions should be treated as credits or debits.
    """
    
    # Known credit category headers
    CREDIT_HEADERS = {
        "deposits and additions",
        "deposits and other credits",
        "deposits & additions",
        "deposits & other credits",
        "credits",
        "deposits",
    }
    
    # Known debit category headers
    DEBIT_HEADERS = {
        "electronic withdrawals",
        "withdrawals and other debits",
        "withdrawals & other debits",
        "electronic withdrawals & debits",
        "debits",
        "withdrawals",
        "checks paid",
        "atm withdrawals",
    }
    
    def __init__(self):
        """Initialize with UNKNOWN state."""
        self.current_state = TransactionType.UNKNOWN
        self.current_category = None
        self._state_history = []
    
    def update_state(self, line: str) -> bool:
        """
        Check if line is a category header and update state accordingly.
        
        Args:
            line: Text line to check
            
        Returns:
            True if state was updated (line was a category header), False otherwise
        """
        line_lower = line.strip().lower()
        
        # Check for credit category
        if line_lower in self.CREDIT_HEADERS:
            self.current_state = TransactionType.CREDIT
            self.current_category = line.strip()
            self._state_history.append(("CREDIT", self.current_category))
            logger.debug(f"State changed to CREDIT: {self.current_category}")
            return True
        
        # Check for debit category
        if line_lower in self.DEBIT_HEADERS:
            self.current_state = TransactionType.DEBIT
            self.current_category = line.strip()
            self._state_history.append(("DEBIT", self.current_category))
            logger.debug(f"State changed to DEBIT: {self.current_category}")
            return True
        
        return False
    
    def is_valid_state(self) -> bool:
        """
        Check if current state is valid for transaction extraction.
        
        Returns:
            True if state is CREDIT or DEBIT, False if UNKNOWN
        """
        return self.current_state != TransactionType.UNKNOWN
    
    def get_state(self) -> TransactionType:
        """Get current transaction type state."""
        return self.current_state
    
    def get_category(self) -> Optional[str]:
        """Get current category name."""
        return self.current_category
    
    def reset(self):
        """Reset state to UNKNOWN."""
        self.current_state = TransactionType.UNKNOWN
        self.current_category = None
        logger.debug("State reset to UNKNOWN")
    
    def get_history(self) -> list[tuple[str, str]]:
        """Get state change history for debugging."""
        return self._state_history.copy()


def apply_sign_to_amount(amount: float, transaction_type: TransactionType) -> float:
    """
    Apply correct sign to amount based on transaction type.
    
    Credit transactions: positive
    Debit transactions: negative
    
    Args:
        amount: Raw amount (assumed positive)
        transaction_type: Type of transaction
        
    Returns:
        Amount with correct sign applied
    """
    # Ensure we start with absolute value
    amount = abs(amount)
    
    if transaction_type == TransactionType.CREDIT:
        return amount  # Keep positive
    elif transaction_type == TransactionType.DEBIT:
        return -amount  # Make negative
    else:
        logger.warning(f"Unknown transaction type for amount {amount}, keeping positive")
        return amount


def format_amount_display(amount: float) -> str:
    """
    Format amount for display with explicit sign.
    
    Positive amounts: +1600.00
    Negative amounts: -250.00
    
    Args:
        amount: Signed amount
        
    Returns:
        Formatted string with explicit sign
    """
    if amount >= 0:
        return f"+{amount:.2f}"
    else:
        return f"{amount:.2f}"  # Negative sign already included


def is_category_line(line: str) -> bool:
    """
    Quick check if a line might be a category header.
    
    Args:
        line: Line to check
        
    Returns:
        True if line matches a known category
    """
    line_lower = line.strip().lower()
    return (line_lower in CategoryState.CREDIT_HEADERS or 
            line_lower in CategoryState.DEBIT_HEADERS)
