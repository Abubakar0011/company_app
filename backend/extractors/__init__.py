"""
Extractors Module - Transaction parsing and categorization.
"""

from .regex_extractor import (
    Transaction,
    TransactionExtractor,
    extract_transactions_from_text
)

from .financial_rules import (
    TransactionType,
    CategoryState,
    apply_sign_to_amount,
    format_amount_display,
    is_category_line
)

__all__ = [
    'Transaction',
    'TransactionExtractor',
    'extract_transactions_from_text',
    'TransactionType',
    'CategoryState',
    'apply_sign_to_amount',
    'format_amount_display',
    'is_category_line',
]
