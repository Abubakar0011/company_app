"""
Regex Extractor Module
Parses bank statement text into structured transactions using regex patterns.
Handles multi-line descriptions and category-based extraction.
"""

import re
import logging
from typing import Optional
from datetime import datetime
from extractors.financial_rules import CategoryState, TransactionType, apply_sign_to_amount, format_amount_display

logger = logging.getLogger(__name__)


class Transaction:
    """Represents a single financial transaction."""
    
    def __init__(
        self,
        date: str,
        description: str,
        amount: float,
        transaction_type: TransactionType,
        category: Optional[str] = None
    ):
        self.date = date
        self.description = description.strip()
        self.amount = amount
        self.amount_display = format_amount_display(amount)
        self.type = transaction_type.value
        self.category = category
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "amount_display": self.amount_display,
            "type": self.type,
            "category": self.category
        }
    
    def __repr__(self) -> str:
        return f"Transaction(date={self.date}, desc={self.description[:30]}..., amount={self.amount_display})"


class TransactionExtractor:
    """
    Extracts transactions from bank statement text.
    Handles line-by-line parsing with category state tracking.
    """
    
    # Date patterns (MM/DD/YYYY or MM/DD)
    DATE_PATTERN = re.compile(r'^(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2})')
    
    # Amount patterns - matches numbers with optional commas and decimals
    AMOUNT_PATTERN = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
    
    def __init__(self):
        """Initialize extractor with category state tracker."""
        self.category_state = CategoryState()
        self.transactions = []
        self.current_transaction = None
        self.pending_date = None  # Track date-only lines
        self.pending_description = []  # Track description lines
        self.stats = {
            "lines_processed": 0,
            "category_changes": 0,
            "transactions_found": 0,
            "multi_line_merges": 0
        }
    
    def extract_transactions(self, text: str) -> list[Transaction]:
        """
        Extract all transactions from statement text.
        
        Args:
            text: Full bank statement text
            
        Returns:
            List of Transaction objects
        """
        if not text or not isinstance(text, str):
            logger.error("Invalid input: text must be a non-empty string")
            return []
        
        if not text.strip():
            logger.warning("Empty text provided for extraction")
            return []
        
        lines = text.split('\n')
        logger.info(f"Starting extraction from {len(lines)} lines")
        
        try:
            for line_num, line in enumerate(lines, 1):
                self.stats["lines_processed"] += 1
                try:
                    self._process_line(line)
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    logger.debug(f"Problematic line: {line[:100]}...")
                    continue
            
            # Finalize last transaction if exists
            if self.current_transaction:
                self._finalize_transaction()
            
            # Finalize any pending stacked transaction
            self._finalize_pending_transaction()
            
            logger.info(
                f"Extraction complete: {self.stats['transactions_found']} transactions found, "
                f"{self.stats['multi_line_merges']} multi-line merges, "
                f"{self.stats['category_changes']} category changes"
            )
            
            if self.stats['transactions_found'] == 0:
                logger.warning(
                    f"No transactions found in {len(lines)} lines. "
                    f"Category changes detected: {self.stats['category_changes']}"
                )
            
            return self.transactions
            
        except Exception as e:
            logger.error(f"Fatal error during transaction extraction: {e}", exc_info=True)
            return self.transactions  # Return what we have so far
    
    def _process_line(self, line: str):
        """Process a single line of statement text."""
        line = line.strip()
        
        if not line:
            return
        
        # Skip common table column headers
        if line.lower() in ['date', 'description', 'amount', 'transaction', 'details', 'debit', 'credit']:
            logger.debug(f"Skipping column header: {line}")
            return
        
        # Check if line is a category header
        if self.category_state.update_state(line):
            self.stats["category_changes"] += 1
            # Finalize any pending transaction when category changes
            self._finalize_pending_transaction()
            return
        
        # Only process transaction lines if we're in a valid category
        if not self.category_state.is_valid_state():
            return
        
        # Check if line is just a date (MM/DD or MM/DD/YYYY)
        date_match = self.DATE_PATTERN.match(line)
        if date_match and line.strip() == date_match.group(1):
            # Just a date, no other content - start collecting transaction parts
            self._finalize_pending_transaction()  # Finalize previous pending transaction
            self.pending_date = date_match.group(1)
            self.pending_description = []
            return
        
        # Check if line is just an amount (number with optional comma/decimal)
        amount_only_match = re.match(r'^\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', line)
        if amount_only_match and self.pending_date:
            # This is the amount for the pending transaction
            amount_str = amount_only_match.group(1)
            try:
                amount = self._parse_amount(amount_str)
                description = ' '.join(self.pending_description).strip()
                
                if not description:
                    description = "[No description]"
                
                # Apply sign based on category
                signed_amount = apply_sign_to_amount(amount, self.category_state.current_state)
                
                # Create transaction
                year = datetime.now().year
                date_parts = self.pending_date.split('/')
                if len(date_parts) == 2:
                    full_date = f"{self.pending_date}/{year}"
                else:
                    full_date = self.pending_date
                
                transaction = Transaction(
                    date=full_date,
                    description=description,
                    amount=signed_amount,
                    transaction_type=self.category_state.current_state,
                    category=self.category_state.current_category
                )
                
                self.transactions.append(transaction)
                self.stats["transactions_found"] += 1
                logger.info(f"Created transaction: {full_date} | {description[:50]}... | {signed_amount:+.2f}")
                
                # Reset pending data
                self.pending_date = None
                self.pending_description = []
                
            except ValueError as e:
                logger.warning(f"Failed to parse amount '{amount_str}': {e}")
                self.pending_date = None
                self.pending_description = []
            return
        
        # If we have a pending date, this line is part of the description
        if self.pending_date:
            self.pending_description.append(line)
            return
        
        # Fall back to original logic for single-line format
        # Check if line is a transaction anchor (starts with date)
        if self._is_transaction_anchor(line):
            # Finalize previous transaction before starting new one
            if self.current_transaction:
                self._finalize_transaction()
            
            # Parse new transaction
            self._parse_transaction_anchor(line)
        
        # Check if line is a continuation of current transaction
        elif self.current_transaction and self._is_continuation_line(line):
            self._append_to_description(line)
    
    def _is_transaction_anchor(self, line: str) -> bool:
        """
        Check if line is a transaction anchor.
        Must start with date and contain an amount.
        """
        if not self.DATE_PATTERN.match(line):
            return False
        
        # Check if line contains an amount
        if not self.AMOUNT_PATTERN.search(line):
            return False
        
        return True
    
    def _parse_transaction_anchor(self, line: str):
        """
        Parse a transaction anchor line.
        Extracts date, amount, and initial description.
        """
        try:
            # Extract date (first token)
            date_match = self.DATE_PATTERN.match(line)
            if not date_match:
                logger.debug(f"No date match in line: {line[:50]}...")
                return
            
            date_str = date_match.group(1)
            remaining = line[len(date_str):].strip()
            
            if not remaining:
                logger.debug(f"No content after date in line: {line}")
                return
            
            # Extract all amounts from the line
            amounts = self.AMOUNT_PATTERN.findall(remaining)
            if not amounts:
                logger.debug(f"No amount found in line: {line[:50]}...")
                return
            
            # Take the last amount as the transaction amount
            amount_str = amounts[-1]
            
            try:
                amount = self._parse_amount(amount_str)
            except ValueError as e:
                logger.warning(f"Failed to parse amount '{amount_str}': {e}")
                return
            
            # Everything between date and amount is description
            amount_pos = remaining.rfind(amount_str)
            description = remaining[:amount_pos].strip()
            
            if not description:
                logger.debug(f"Empty description for transaction on {date_str}")
                description = "[No description]"  # Provide fallback
            
            # Apply sign based on category
            signed_amount = apply_sign_to_amount(amount, self.category_state.get_state())
            
            # Create new transaction (not finalized yet)
            self.current_transaction = {
                "date": date_str,
                "description": description,
                "amount": signed_amount,
                "type": self.category_state.get_state(),
                "category": self.category_state.get_category()
            }
            
            logger.debug(
                f"Parsed anchor: {date_str} | {description[:30]}{'...' if len(description) > 30 else ''} | "
                f"{'+' if signed_amount >= 0 else ''}{signed_amount:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error parsing transaction anchor: {e}")
            logger.debug(f"Problematic line: {line}")
            self.current_transaction = None
    
    def _is_continuation_line(self, line: str) -> bool:
        """
        Check if line is a continuation of the current transaction.
        Continuation lines don't start with dates and aren't category headers.
        """
        # Not a date line
        if self.DATE_PATTERN.match(line):
            return False
        
        # Not a category header
        if self.category_state.update_state(line):
            return False
        
        # Has some text content
        if not line.strip():
            return False
        
        # Avoid lines that look like headers or summaries
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in ["total", "balance", "subtotal", "page", "continued"]):
            return False
        
        return True
    
    def _append_to_description(self, line: str):
        """Append line to current transaction description."""
        if self.current_transaction:
            self.current_transaction["description"] += " " + line.strip()
            self.stats["multi_line_merges"] += 1
            logger.debug(f"Appended to description: {line[:30]}...")
    
    def _finalize_transaction(self):
        """Convert current transaction dict to Transaction object and add to list."""
        if not self.current_transaction:
            return
        
        txn = Transaction(
            date=self.current_transaction["date"],
            description=self.current_transaction["description"],
            amount=self.current_transaction["amount"],
            transaction_type=self.current_transaction["type"],
            category=self.current_transaction["category"]
        )
        
        self.transactions.append(txn)
        self.stats["transactions_found"] += 1
        self.current_transaction = None
        
        logger.debug(f"Finalized: {txn}")
    
    def _finalize_pending_transaction(self):
        """Finalize a pending stacked transaction if we have incomplete data."""
        if self.pending_date and self.pending_description:
            # We have date and description but no amount - log warning
            logger.warning(f"Incomplete transaction: date={self.pending_date}, description={' '.join(self.pending_description)[:50]}... (missing amount)")
        
        # Reset pending data
        self.pending_date = None
        self.pending_description = []
    
    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """
        Parse amount string to float.
        Handles commas in thousands.
        
        Raises:
            ValueError: If amount cannot be parsed
        """
        try:
            # Remove commas
            clean = amount_str.replace(',', '')
            amount = float(clean)
            
            if amount < 0:
                logger.warning(f"Negative amount in raw data: {amount_str}")
            
            return amount
            
        except ValueError as e:
            logger.error(f"Cannot parse amount '{amount_str}': {e}")
            raise ValueError(f"Invalid amount format: {amount_str}") from e
    
    def get_stats(self) -> dict:
        """Get extraction statistics."""
        return self.stats.copy()


def extract_transactions_from_text(text: str) -> list[Transaction]:
    """
    Convenience function to extract transactions from text.
    
    Args:
        text: Bank statement text
        
    Returns:
        List of Transaction objects
    """
    extractor = TransactionExtractor()
    return extractor.extract_transactions(text)
