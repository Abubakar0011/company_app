# Backend - Bank Statement Transaction Extractor

Python-based backend for extracting, validating, and filtering bank statement transactions from PDF files.

## Structure

```
backend/
├── loaders/           # PDF loading and text extraction
│   └── pdf_loader.py
├── extractors/        # Transaction parsing and categorization
│   ├── financial_rules.py
│   └── regex_extractor.py
├── validators/        # Transaction validation
│   └── financial_validator.py
├── output/           # Report generation
│   └── writer.py
├── main.py           # Main pipeline orchestration
└── requirements.txt  # Python dependencies
```

## Features

- **Multi-page PDF Processing**: Extract text from bank statement PDFs
- **Smart Transaction Detection**: Automatic credit/debit categorization
- **Multi-line Description Handling**: Merge continuation lines
- **Sign Management**: Explicit +/- display for deposits/withdrawals
- **Flexible Filtering**: Filter by keyword and date range
- **PDF Report Generation**: Formatted monthly transaction reports

## Installation

```bash
# Install dependencies
uv pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python backend/main.py <pdf_path> <keyword> <start_month> <end_month> <output_path>
```

**Example:**
```bash
python backend/main.py statement.pdf "Bank of America" 2025-01 2025-03 report.pdf
```

### Programmatic Usage

```python
from backend.main import BankStatementExtractor

extractor = BankStatementExtractor()
extractor.process_statement(
    pdf_path="statement.pdf",
    keyword="Bank of America",
    start_month="2025-01",
    end_month="2025-03",
    output_path="report.pdf"
)
```

## API Modules

### PDF Loader (`loaders.pdf_loader`)
- `load_pdf(pdf_path)` - Extract text from single PDF
- `load_multiple_pdfs(pdf_paths)` - Process multiple PDFs

### Transaction Extractor (`extractors.regex_extractor`)
- `extract_transactions_from_text(text)` - Parse transactions from text
- `Transaction` - Transaction data class

### Financial Rules (`extractors.financial_rules`)
- Category definitions (credit/debit)
- Sign application logic
- Amount formatting

### Validator (`validators.financial_validator`)
- `validate_transactions(transactions, strict_mode)` - Validate transaction data

### Report Writer (`output.writer`)
- `generate_pdf_report(...)` - Create formatted PDF reports

## Configuration

Logging is configured in `main.py` and outputs to:
- Console (INFO level)
- `transaction_extractor.log` file (detailed)

## Error Handling

All modules implement comprehensive error handling:
- PDF loading errors
- Transaction parsing validation
- Date format validation
- File I/O errors

See logs for detailed error information.
