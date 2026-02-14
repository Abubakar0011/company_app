# Project Structure

## Overview
Clean separation between backend (Python processing) and frontend (web interface).

## Directory Layout

```
text_extractor/
│
├── backend/                      # 🐍 Python Backend
│   ├── extractors/              # Transaction parsing & categorization
│   │   ├── financial_rules.py   # Credit/debit rules & sign logic
│   │   └── regex_extractor.py   # Pattern-based transaction extraction
│   │
│   ├── loaders/                 # PDF input processing
│   │   └── pdf_loader.py        # Multi-page PDF text extraction
│   │
│   ├── validators/              # Data validation
│   │   └── financial_validator.py  # Transaction validation rules
│   │
│   ├── output/                  # Report generation
│   │   ├── writer.py            # PDF report formatting
│   │   └── .gitkeep            # Preserve directory structure
│   │
│   ├── main.py                  # 🚀 Main pipeline orchestration
│   ├── requirements.txt         # Python dependencies
│   ├── README.md               # Backend documentation
│   └── __init__.py             # Package initialization
│
├── frontend/                    # 🌐 Web Interface (Planned)
│   └── README.md               # Frontend documentation & roadmap
│
├── tests/                       # 🧪 Integration Tests
│   └── test_pipeline.py        # End-to-end pipeline tests
│
├── docs/                        # 📚 Documentation
│   └── bank_statement_extractor_implementation_doc.md
│
├── .venv/                       # Virtual environment (not in git)
├── .gitignore                   # Git ignore rules
├── pyproject.toml              # Project metadata
├── uv.lock                     # UV dependency lock file
└── README.md                   # Main project documentation
```

## Module Responsibilities

### Backend Modules

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| **loaders.pdf_loader** | PDF text extraction | `load_pdf()`, `load_multiple_pdfs()` |
| **extractors.financial_rules** | Category & sign management | `apply_sign_to_amount()`, `format_amount_display()` |
| **extractors.regex_extractor** | Transaction parsing | `extract_transactions_from_text()`, `Transaction` class |
| **validators.financial_validator** | Data validation | `validate_transactions()` |
| **output.writer** | PDF report generation | `generate_pdf_report()` |
| **main** | Pipeline orchestration | `BankStatementExtractor`, `TransactionFilter`, `TransactionGrouper` |

### Frontend (Coming Soon)

- Web-based UI for file upload
- Interactive filtering interface
- Real-time transaction preview
- Download formatted reports

## Running the System

### Backend
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run extraction
python backend/main.py <pdf> <keyword> <start> <end> <output>
```

### Tests
```bash
python tests/test_pipeline.py
```

## Development Workflow

1. **Backend Development** → Work in `backend/` directory
2. **Testing** → Add tests in `tests/` directory
3. **Documentation** → Update relevant README files
4. **Frontend Development** → Will work in `frontend/` directory

## Code Quality

- ✅ Modular architecture with clear separation
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Type hints and docstrings
- ✅ Integration tests

## Next Steps

1. ✅ Backend complete and tested
2. 🚧 Create REST API for backend
3. 🚧 Develop frontend interface
4. 🚧 Add user authentication
5. 🚧 Implement batch processing

---

**Status:** Backend ✅ Complete | Frontend 🚧 In Planning
