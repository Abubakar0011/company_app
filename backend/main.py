"""
Bank Statement Transaction Extractor - Main Pipeline
Orchestrates the full extraction, filtering, and report generation process.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict

# Import core modules (PDF loader imported conditionally where needed)
from extractors.regex_extractor import extract_transactions_from_text, Transaction
from validators.financial_validator import validate_transactions
from output.writer import generate_pdf_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('transaction_extractor.log')
    ]
)

logger = logging.getLogger(__name__)



class TransactionFilter:
    """Filters transactions by keyword and date range."""
    
    @staticmethod
    def filter_by_keyword(transactions: list[Transaction], keyword: str) -> list[Transaction]:
        """
        Filter transactions by keyword (case-insensitive substring match).
        
        Args:
            transactions: List of transactions
            keyword: Keyword to search for
            
        Returns:
            Filtered list of transactions
        """
        if not keyword:
            return transactions
        
        keyword_lower = keyword.lower()
        filtered = [
            txn for txn in transactions
            if keyword_lower in txn.description.lower()
        ]
        
        logger.info(f"Keyword filter '{keyword}': {len(filtered)}/{len(transactions)} transactions matched")
        return filtered
    
    @staticmethod
    def filter_by_keywords(
        transactions: list[Transaction],
        keywords: list[str]
    ) -> dict[str, list[Transaction]]:
        """
        Filter transactions by multiple keywords (banks).
        Each transaction is assigned to the first matching keyword.
        
        Args:
            transactions: List of all transactions
            keywords: List of keywords/bank names to filter by
            
        Returns:
            Dict mapping keyword to list of matching transactions.
            Includes 'Unmatched' key for transactions that don't match any keyword.
        """
        if not keywords:
            return {'All': transactions}
        
        results = {keyword: [] for keyword in keywords}
        matched_indices = set()
        
        # Match each transaction to first matching keyword
        for idx, txn in enumerate(transactions):
            desc_lower = txn.description.lower()
            matched = False
            
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    results[keyword].append(txn)
                    matched_indices.add(idx)
                    matched = True
                    break  # First match wins
        
        # Collect unmatched transactions
        unmatched = [
            txn for idx, txn in enumerate(transactions)
            if idx not in matched_indices
        ]
        
        if unmatched:
            results['Unmatched'] = unmatched
            logger.info(f"Found {len(unmatched)} unmatched transactions")
        
        # Log results
        for keyword, txns in results.items():
            if txns:
                logger.info(f"Keyword '{keyword}': {len(txns)} transactions matched")
        
        return results
    
    @staticmethod
    def filter_by_date_range(
        transactions: list[Transaction],
        start_month: str,
        end_month: str
    ) -> list[Transaction]:
        """
        Filter transactions by month range.
        
        Args:
            transactions: List of transactions
            start_month: Start month (YYYY-MM)
            end_month: End month (YYYY-MM)
            
        Returns:
            Filtered list of transactions
        """
        if not start_month or not end_month:
            return transactions
        
        filtered = []
        for txn in transactions:
            txn_month = TransactionFilter._extract_month(txn.date)
            if txn_month and start_month <= txn_month <= end_month:
                filtered.append(txn)
        
        logger.info(
            f"Date range filter ({start_month} to {end_month}): "
            f"{len(filtered)}/{len(transactions)} transactions matched"
        )
        return filtered
    
    @staticmethod
    def _extract_month(date_str: str) -> Optional[str]:
        """
        Extract YYYY-MM from date string.
        
        Supports multiple date formats:
        - MM/DD/YYYY (01/15/2026)
        - MM/DD/YY (01/15/25) - 2-digit year
        - MM/DD (01/15) - assumes current year
        - MM-DD-YYYY (01-15-2026)
        - MM-DD-YY (01-15-25)
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            YYYY-MM string or None if parsing fails
        """
        try:
            # Try slash separator first
            if '/' in date_str:
                parts = date_str.split('/')
            # Try hyphen separator
            elif '-' in date_str and not date_str.startswith('20'):  # Not YYYY-MM-DD
                parts = date_str.split('-')
            # Try YYYY-MM-DD format
            elif '-' in date_str:
                # YYYY-MM-DD format
                return date_str[:7]  # Return YYYY-MM
            else:
                return None
            
            if len(parts) == 3:  # MM/DD/YYYY or MM/DD/YY
                month, day, year = parts
                
                # Check if year is 2-digit
                if len(year) == 2:
                    # Convert 2-digit year to 4-digit
                    # Assume years 00-49 are 2000-2049, and 50-99 are 1950-1999
                    year_int = int(year)
                    if year_int <= 49:
                        year = f"20{year}"
                    else:
                        year = f"19{year}"
                
                return f"{year}-{month.zfill(2)}"
            
            elif len(parts) == 2:  # MM/DD - assume current year
                month, day = parts
                current_year = datetime.now().year
                return f"{current_year}-{month.zfill(2)}"
            
            return None
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None


class TransactionGrouper:
    """Groups transactions by month and type (deposits/withdrawals)."""
    
    @staticmethod
    def group_by_month(transactions: list[Transaction]) -> dict[str, list[Transaction]]:
        """
        Group transactions by month (YYYY-MM).
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary mapping month to list of transactions
        """
        grouped = defaultdict(list)
        
        for txn in transactions:
            month = TransactionFilter._extract_month(txn.date)
            if month:
                grouped[month].append(txn)
        
        logger.info(f"Grouped {len(transactions)} transactions into {len(grouped)} months")
        return dict(grouped)
    
    @staticmethod
    def group_by_bank_month_type(
        transactions_by_bank: dict[str, list[Transaction]]
    ) -> dict[str, dict[str, dict[str, list[Transaction]]]]:
        """
        Group transactions by bank, then month, then type (deposits/withdrawals).
        
        Args:
            transactions_by_bank: Dict mapping bank/keyword to transactions
            
        Returns:
            Nested dict: {bank: {month: {'deposits': [...], 'withdrawals': [...]}}}
        """
        result = {}
        
        for bank, transactions in transactions_by_bank.items():
            if not transactions:
                continue
            
            bank_data = {}
            
            # Group by month first
            months = TransactionGrouper.group_by_month(transactions)
            
            # Then separate by type within each month
            for month, month_txns in months.items():
                deposits = [txn for txn in month_txns if txn.type == "credit"]
                withdrawals = [txn for txn in month_txns if txn.type == "debit"]
                
                # Only include month if it has transactions
                month_data = {}
                if deposits:
                    month_data['deposits'] = deposits
                if withdrawals:
                    month_data['withdrawals'] = withdrawals
                
                if month_data:  # Only add month if it has data
                    bank_data[month] = month_data
            
            if bank_data:  # Only add bank if it has data
                result[bank] = bank_data
                logger.info(
                    f"Bank '{bank}': {len(bank_data)} months, "
                    f"{len(transactions)} total transactions"
                )
        
        return result


class BankStatementExtractor:
    """Main orchestrator for bank statement extraction pipeline."""
    
    def __init__(self):
        """Initialize extractor."""
        self.stats = {
            "pdf_pages": 0,
            "total_extracted": 0,
            "valid_transactions": 0,
            "after_keyword_filter": 0,
            "after_date_filter": 0,
            "final_output": 0
        }
    
    def _validate_inputs(
        self,
        pdf_path: str,
        keywords: list[str],
        start_month: str,
        end_month: str,
        output_path: str
    ):
        """Validate all input parameters."""
        if not pdf_path or not isinstance(pdf_path, str):
            raise ValueError("pdf_path must be a non-empty string")
        
        if not Path(pdf_path).exists():
            raise ValueError(f"PDF file not found: {pdf_path}")
        
        if not keywords or not isinstance(keywords, list):
            raise ValueError("keywords must be a non-empty list")
        
        if not all(isinstance(k, str) and k.strip() for k in keywords):
            raise ValueError("All keywords must be non-empty strings")
        
        if not start_month or not isinstance(start_month, str):
            raise ValueError("start_month must be a non-empty string (YYYY-MM)")
        
        if not end_month or not isinstance(end_month, str):
            raise ValueError("end_month must be a non-empty string (YYYY-MM)")
        
        # Validate date format
        try:
            datetime.strptime(start_month, '%Y-%m')
            datetime.strptime(end_month, '%Y-%m')
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM format")
        
        if start_month > end_month:
            raise ValueError(f"start_month ({start_month}) must be <= end_month ({end_month})")
        
        if not output_path or not isinstance(output_path, str):
            raise ValueError("output_path must be a non-empty string")
        
        if not output_path.endswith('.pdf'):
            raise ValueError("output_path must end with .pdf")
        
        logger.info("Input validation passed")
    
    def process(
        self,
        pdf_path: str,
        keywords: list[str],
        start_month: str,
        end_month: str,
        output_path: str
    ):
        """
        Process bank statement PDF and generate multi-bank report.
        
        Args:
            pdf_path: Path to PDF file
            keywords: List of keywords/bank names to filter by
            start_month: Start month (YYYY-MM)
            end_month: End month (YYYY-MM)
            output_path: Path for output PDF report
            
        Raises:
            ValueError: If inputs are invalid
            Exception: If PDF cannot be loaded or PyMuPDF is not installed
            Exception: For other processing errors
        """
        logger.info("=" * 80)
        logger.info("Starting Bank Statement Extraction Pipeline")
        logger.info(f"Processing {len(keywords)} bank(s)/keyword(s)")
        logger.info("=" * 80)
        
        # Input validation
        try:
            self._validate_inputs(pdf_path, keywords, start_month, end_month, output_path)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        
        try:
            # Step 1: Load PDF
            logger.info(f"Step 1: Loading PDF - {pdf_path}")
            try:
                from loaders.pdf_loader import load_pdf, PDFLoadError
                text = load_pdf(pdf_path)
                self.stats["pdf_pages"] = text.count('\n\n') + 1
                logger.info(f"Extracted {len(text)} characters from PDF")
            except PDFLoadError as e:
                logger.error(f"Failed to load PDF: {e}")
                raise
            except ImportError as e:
                logger.error(f"PDF loader not available: {e}")
                raise ImportError("PyMuPDF is required for PDF loading. Install with: uv pip install pymupdf") from e
            
            if not text.strip():
                raise ValueError("PDF contains no extractable text")
            
            # Step 2: Extract transactions
            logger.info("Step 2: Extracting transactions from text")
            try:
                transactions = extract_transactions_from_text(text)
                self.stats["total_extracted"] = len(transactions)
                logger.info(f"Extracted {len(transactions)} raw transaction candidates")
            except Exception as e:
                logger.error(f"Transaction extraction failed: {e}", exc_info=True)
                raise Exception("Failed to extract transactions from PDF") from e
            
            if not transactions:
                logger.warning("No transactions found in PDF. Check if PDF contains transaction data in expected format.")
            
            # Step 3: Validate transactions
            logger.info("Step 3: Validating transactions")
            try:
                valid_transactions = validate_transactions(transactions, strict_mode=False)
                self.stats["valid_transactions"] = len(valid_transactions)
                logger.info(f"{len(valid_transactions)} valid transactions (filtered {len(transactions) - len(valid_transactions)} invalid)")
            except Exception as e:
                logger.error(f"Transaction validation failed: {e}", exc_info=True)
                raise Exception("Failed to validate transactions") from e
            
            # Step 4: Filter by keywords (multi-bank)
            logger.info(f"Step 4: Filtering by {len(keywords)} keyword(s)/bank(s)")
            try:
                transactions_by_bank = TransactionFilter.filter_by_keywords(valid_transactions, keywords)
                total_matched = sum(len(txns) for txns in transactions_by_bank.values())
                self.stats["after_keyword_filter"] = total_matched
                logger.info(f"Matched {total_matched} transactions across {len(transactions_by_bank)} banks")
            except Exception as e:
                logger.error(f"Keyword filtering failed: {e}", exc_info=True)
                raise Exception("Failed to filter by keywords") from e
            
            # Step 5: Filter by date range for each bank
            logger.info(f"Step 5: Filtering by date range - {start_month} to {end_month}")
            try:
                date_filtered_by_bank = {}
                total_after_date = 0
                
                for bank, txns in transactions_by_bank.items():
                    filtered = TransactionFilter.filter_by_date_range(txns, start_month, end_month)
                    if filtered:  # Only include banks with transactions
                        date_filtered_by_bank[bank] = filtered
                        total_after_date += len(filtered)
                
                self.stats["after_date_filter"] = total_after_date
                logger.info(f"{total_after_date} transactions after date filtering")
            except Exception as e:
                logger.error(f"Date range filtering failed: {e}", exc_info=True)
                raise Exception("Failed to filter by date range") from e
            
            # Step 6: Group by bank, month, and type (deposits/withdrawals)
            logger.info("Step 6: Grouping transactions by bank, month, and type")
            try:
                grouped = TransactionGrouper.group_by_bank_month_type(date_filtered_by_bank)
                self.stats["final_output"] = total_after_date
            except Exception as e:
                logger.error(f"Transaction grouping failed: {e}", exc_info=True)
                raise Exception("Failed to group transactions") from e
            
            # Step 7: Generate PDF report
            logger.info(f"Step 7: Generating PDF report - {output_path}")
            try:
                generate_pdf_report(
                    output_path=output_path,
                    grouped_data=grouped,
                    keywords=keywords,
                    start_month=start_month,
                    end_month=end_month,
                    total_transactions=total_after_date
                )
            except Exception as e:
                logger.error(f"PDF report generation failed: {e}", exc_info=True)
                raise Exception(f"Failed to generate PDF report at {output_path}") from e
            
            # Print summary
            self._print_summary()
            
            logger.info("=" * 80)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Report saved to: {output_path}")
            logger.info("=" * 80)
            
        except (ImportError, ValueError):
            raise
        except Exception as e:
            logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
            raise
    
    def _print_summary(self):
        """Print extraction summary."""
        logger.info("\n" + "=" * 80)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total transactions extracted:    {self.stats['total_extracted']}")
        logger.info(f"Valid transactions:              {self.stats['valid_transactions']}")
        logger.info(f"After keyword filter:            {self.stats['after_keyword_filter']}")
        logger.info(f"After date range filter:         {self.stats['after_date_filter']}")
        logger.info(f"Final transactions in report:    {self.stats['final_output']}")
        logger.info("=" * 80 + "\n")


def main():
    """Main entry point - example usage."""
    
    # Example configuration
    pdf_path = "sample_statement.pdf"  # Path to your bank statement
    keywords = ["Bank of America", "Chase"]  # List of bank names/keywords
    start_month = "2025-01"             # Start month
    end_month = "2025-03"               # End month
    output_path = "output/transaction_report.pdf"  # Output file
    
    # Validate inputs before starting
    if not Path(pdf_path).exists():
        logger.error(f"PDF file not found: {pdf_path}")
        print(f"\n❌ Error: PDF file not found: {pdf_path}")
        print("Please update the pdf_path variable in main.py with a valid PDF file path.")
        sys.exit(1)
    
    try:
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ready: {output_dir}")
        
    except Exception as e:
        logger.error(f"Cannot create output directory: {e}")
        print(f"\n❌ Error: Cannot create output directory: {e}")
        sys.exit(1)
    
    # Run extraction
    extractor = BankStatementExtractor()
    
    try:
        logger.info("Starting extraction process...")
        extractor.process(
            pdf_path=pdf_path,
            keywords=keywords,
            start_month=start_month,
            end_month=end_month,
            output_path=output_path
        )
        
        print(f"\n✅ Success! Report generated: {output_path}")
        print(f"Total transactions in report: {extractor.stats['final_output']}")
        print(f"Banks processed: {len(keywords)}")
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"\n❌ Input Error: {e}")
        sys.exit(1)
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"\n❌ Import Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Check transaction_extractor.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
