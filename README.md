# Bank Statement Transaction Extractor

Professional bank statement PDF transaction extraction, filtering, and reporting system with clean separation between backend processing engine and frontend user interface.

## 🎯 Overview

Extract, validate, filter, and report on bank transactions from PDF statements. The system intelligently categorizes transactions as credits or debits, handles multi-line descriptions, and generates formatted reports.

## 📁 Project Structure

```
text_extractor/
├── backend/                  # Python processing engine
│   ├── loaders/             # PDF text extraction
│   ├── extractors/          # Transaction parsing & categorization
│   ├── validators/          # Data validation
│   ├── output/              # Report generation
│   ├── main.py             # Pipeline orchestration
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Backend documentation
├── frontend/                # Web interface (planned)
│   └── README.md           # Frontend documentation
├── docs/                    # Project documentation
│   └── bank_statement_extractor_implementation_doc.md
├── tests/                   # Test files
│   └── test_pipeline.py    # Integration tests
├── pyproject.toml          # Project configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## ✨ Features

### Backend (Python)
- ✅ Multi-page PDF text extraction
- ✅ Automatic credit/debit categorization
- ✅ Multi-line transaction description handling
- ✅ Explicit +/- sign display
- ✅ Keyword-based filtering
- ✅ Date range filtering (month-based)
- ✅ Monthly transaction grouping
- ✅ Formatted PDF report generation
- ✅ Comprehensive error handling & logging

### Frontend (Coming Soon)
- 🚧 Web-based file upload interface
- 🚧 Interactive transaction preview
- 🚧 Real-time filtering
- 🚧 Download reports
- 🚧 Batch processing

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- UV package manager (recommended) or pip

### Installation

1. **Clone the repository**
```bash
cd text_extractor
```

2. **Set up virtual environment**
```bash
# Using UV (recommended)
uv venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Or using Python
python -m venv .venv
.venv\Scripts\activate      # Windows
```

3. **Install backend dependencies**
```bash
uv pip install -r backend/requirements.txt
# Or: pip install -r backend/requirements.txt
```

### Usage

#### Command Line
```bash
python backend/main.py <pdf_path> <keyword> <start_month> <end_month> <output_path>
```

**Example:**
```bash
python backend/main.py statement.pdf "Bank of America" 2025-01 2025-03 filtered_report.pdf
```

**Parameters:**
- `pdf_path`: Path to bank statement PDF file
- `keyword`: Search term to filter transactions (case-insensitive)
- `start_month`: Start month in YYYY-MM format (e.g., 2025-01)
- `end_month`: End month in YYYY-MM format (e.g., 2025-03)
- `output_path`: Output PDF report path

#### Programmatic Usage
```python
from backend.main import BankStatementExtractor

extractor = BankStatementExtractor()
extractor.process_statement(
    pdf_path="bank_statement.pdf",
    keyword="Bank of America",
    start_month="2025-01",
    end_month="2025-03",
    output_path="output/report.pdf"
)
```

## 🧪 Testing

Run integration tests to verify the system:

```bash
python tests/test_pipeline.py
```

Expected output:
```
✅ Extraction Pipeline: PASSED
✅ PDF Report: PASSED
Overall: 2/2 tests passed
🎉 ALL TESTS PASSED!
```

## 📊 How It Works

### Transaction Extraction Pipeline

1. **PDF Loading** → Extract text from PDF files (PyMuPDF)
2. **Category Detection** → Identify credit/debit sections
3. **Transaction Parsing** → Extract date, description, amount
4. **Multi-line Merging** → Combine continuation lines
5. **Sign Application** → Apply +/- based on category
6. **Validation** → Validate dates, amounts, descriptions
7. **Filtering** → Apply keyword and date filters
8. **Grouping** → Group by month
9. **Report Generation** → Create formatted PDF (ReportLab)

### Category Recognition

The system recognizes these patterns as credit/debit headers:
- **Credits:** "Deposits and other credits", "Deposits and additions"
- **Debits:** "Electronic Withdrawals", "Withdrawals and other debits", "Checks paid"

### Sign Logic
- Credit transactions → positive amounts (+1000.00)
- Debit transactions → negative amounts (-500.00)
- Amounts in PDFs are converted using `abs()` then signed by category context

## 📚 Documentation

- [Backend Documentation](backend/README.md) - API and module details
- [Frontend Documentation](frontend/README.md) - UI and integration
- [Implementation Doc](docs/bank_statement_extractor_implementation_doc.md) - Detailed specifications

## 🛠️ Technology Stack

### Backend
- **Python 3.9+**
- **PyMuPDF (fitz)** - PDF text extraction
- **ReportLab** - PDF report generation
- **python-dateutil** - Date parsing
- **pytest** - Testing framework

### Frontend (Planned)
- React/Vue.js - UI framework
- REST API - Backend communication
- Modern component library

## 📝 Development

### Code Quality Standards
- ✅ Production-grade error handling
- ✅ Comprehensive logging (INFO/DEBUG/WARNING/ERROR)
- ✅ Type hints and documentation
- ✅ Modular architecture
- ✅ Clean separation of concerns

### Adding New Features

1. Backend modules follow this structure:
   - Clear function/class names
   - Try-except-finally blocks
   - Detailed logging
   - Input validation
   - Docstrings

2. Test new features in `tests/test_pipeline.py`

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing style and quality standards
- All tests pass
- Documentation is updated
- Error handling is comprehensive

## 📄 License

[Add your license here]

## 👥 Authors

[Add authors here]

## 🐛 Issues & Support

Check `transaction_extractor.log` for detailed error information.

For issues, see the error messages in the log file which include:
- Stack traces
- Input validation errors
- PDF processing errors
- Transaction parsing warnings

---

**Status:** Backend complete ✅ | Frontend in development 🚧
