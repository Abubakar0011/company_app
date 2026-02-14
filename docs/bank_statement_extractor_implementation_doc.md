# Bank Statement PDF Transaction Extractor & Month-Grouped Report Generator  
**End-to-End Implementation Document (v1 – Rule-Based, ML-ready)**

---

## 1) Overview & Goal

This system allows a user to upload one (or multiple) **multi-page bank statement PDFs** and generate a **new PDF report** containing only the transactions that match:

- A **keyword** (bank name / merchant / description term)
- A **time window** (e.g., **January → March**)

The extracted transactions are grouped by month and written back into a clean output PDF for user verification and download.

The system extracts **only valid financial transactions** from bank statement PDFs under **specific credit or debit categories**, normalizes them into a clean structure (Date, Description, Amount), filters them by **keyword and month range**, and generates a **new PDF report** grouped by month.

**The system intentionally ignores all non-transactional content** such as summaries, balances, disclaimers, headers, and footers.

---

## 2) Core Principle

**We only trust transactions that appear under known credit or debit categories.**

Everything else in the PDF is treated as noise.

Category context determines:

* Whether a line is eligible to be a transaction
* Whether the amount is positive (credit) or negative (debit)

This principle ensures we extract only valid financial transactions and ignore summaries, balances, disclaimers, headers, and footers.

---

## 3) Core Requirements (What the system must do)

### Inputs
1. **PDF statement(s)**  
   - Multi-page  
   - Contains transaction records across pages  
   - Contains section/category headings

2. **User query**
   - `keyword` (string): e.g., `"Bank of America"`, `"ATM"`, `"Netflix"`
   - `start_month` (YYYY-MM): e.g., `"2025-01"`
   - `end_month` (YYYY-MM): e.g., `"2025-03"`

### Output
- A **generated PDF report** with:
  - Month sections (Jan, Feb, Mar…)
  - Transaction table per month: **Date | Description | Amount**
  - Correct **sign logic** for debit vs credit
  - Totals per month (optional but recommended)

---

## 4) Important Business Logic: Credit vs Debit (Sign Handling)

Bank statements may not include explicit `+`/`-` signs for amounts.  
Instead, the sign is implied by the **transaction category section**.

**Amount sign is never trusted from the raw PDF** - the sign is determined **only** by category context.

### Credit categories (positive with + sign)
- Deposits and additions  
- Deposits and other credits  

### Debit categories (negative with - sign)
- Electronic Withdrawals  
- Withdrawals and other debits  

### Rule
- If a transaction appears under a **credit category** → apply positive sign (+) to amount  
- If a transaction appears under a **debit category** → apply negative sign (-) to amount  

This is an essential edge case and must be handled.

---

## 5) System Architecture

### High-level pipeline

```
PDF(s)
  ↓
Text Extraction (multi-page)
  ↓
Line Stream
  ↓
Category State Tracker (CREDIT / DEBIT / UNKNOWN)
  ↓
Transaction Detection (date + amount anchor)
  ↓
Multi-line Description Merge
  ↓
Transaction Validator
  ↓
User Query Filter (keyword + month range)
  ↓
Month Grouping
  ↓
PDF Report Generation
  ↓
User Preview + Download
```

---

## 5) Project Structure (Same as your current plan)

```
project/
│
├── loaders/
│   ├── pdf_loader.py
│   ├── txt_loader.py              # optional for debugging
│
├── extractors/
│   ├── regex_extractor.py         # parses transaction rows
│   ├── financial_rules.py         # credit/debit logic + mapping
│
├── validators/
│   └── financial_validator.py     # validates parsed fields
│
├── output/
│   └── writer.py                  # generates output PDF report
│
└── main.py                        # orchestrator
```

---

## 7) Data Contracts (Standard Structures)

### Transaction Record (Canonical)
All extracted transactions must be normalized into one consistent schema.

**This object represents one logical transaction**, regardless of how many lines it occupied in the PDF:

```python
{
  "date": "2025-01-21",            # ISO format
  "description": "Chips Credit Via: Bank of America ... Trn: 0136838021",
  "amount": 1600.00,               # stored as positive for credit, negative for debit
  "amount_display": "+1600.00",   # display format with explicit sign
  "type": "credit",                # "credit" or "debit"
  "category": "Deposits and other credits"
}
```

### Filter Request (User Query)
```python
{
  "keyword": "Bank of America",
  "start_month": "2025-01",
  "end_month": "2025-03"
}
```

### Month Grouped Output
```python
{
  "2025-01": [transaction, ...],
  "2025-02": [transaction, ...],
  "2025-03": [transaction, ...]
}
```

---

## 7) Detailed Module Responsibilities

---

### 7.1 loaders/pdf_loader.py

**Purpose**
- Extract text from every page of the PDF efficiently.
- Maintain correct reading order.

**Recommended library**
- **PyMuPDF (fitz)**

**Expected output**
- A single combined string OR list of page strings.

**Pseudo**
```python
open pdf
for each page:
  extract text
return all text
```

---

### 7.2 extractors/financial_rules.py

**Purpose**
- Define and detect category headings.
- Maintain current parsing mode:
  - CREDIT
  - DEBIT
  - UNKNOWN

**Category sets**
```python
CREDIT_HEADERS = {
  "Deposits and additions",
  "Deposits and other credits"
}

DEBIT_HEADERS = {
  "Electronic Withdrawals",
  "Withdrawals and other debits"
}
```

**Output**
- A function that maps the current category → transaction sign logic.

---

### 7.3 extractors/regex_extractor.py

**Purpose**
- Parse statement lines into structured transactions.

**Key tasks**
1. Convert text → lines
2. Track current category while scanning (line-by-line)
3. Detect transaction anchor lines
4. Handle multi-line descriptions
5. Extract:
   - Date
   - Amount
   - Description (merged if multi-line)

**Transaction anchor detection**
A line is considered a **transaction anchor** if:
- Current category state is CREDIT or DEBIT (not UNKNOWN)
- Line starts with a date pattern (e.g., `MM/DD/YYYY`)
- Line contains a numeric amount

**Multi-line description handling**
Lines following an anchor line that:
- Do not start with a date
- Do not represent a new category header
- Are appended to the previous transaction's description

**Recommended regex patterns**
- Date:
  - `r"^\d{2}/\d{2}/\d{4}"`
- Amount:
  - `r"\d+(?:,\d{3})*(?:\.\d{2})"`

**Parsing strategy**
1. Scan lines sequentially
2. When a category header is detected, update state
3. When a transaction anchor is found:
   - Extract date (first token)
   - Extract amount (last numeric value)
   - Extract description (middle tokens)
4. For subsequent non-anchor lines under same category:
   - Append text to current transaction description
5. Finalize transaction when next anchor or category change occurs

---

### 7.4 validators/financial_validator.py

**Purpose**
- Ensure extracted data is valid and safe.

**Validations**
- Date can be parsed to a real date
- Amount is numeric
- Description not empty
- Category is known OR default handled safely

**Behavior**
- If a transaction is invalid:
  - either skip it
  - or log it for review (recommended)

---

### 7.5 output/writer.py

**Purpose**
- Generate a new PDF report containing:
  - Query summary
  - Month-wise groups
  - Tables: Date | Description | Amount (with explicit +/- signs)
  - Totals (with explicit signs)

**Recommended library**
- **reportlab** (best for PDF writing)

**Amount Formatting**
- Credit transactions: Display with + prefix (e.g., +1600.00)
- Debit transactions: Display with - prefix (e.g., -250.00)

---

### 7.6 main.py

**Purpose**
- Orchestrate the full pipeline:
  - Load
  - Extract
  - Validate
  - Filter
  - Group
  - Write PDF

---

## 8) Filtering Logic (Keyword + Time Window)

### Keyword filtering
- Case-insensitive substring match:
  - `"bank of america"` in description.lower()

### Time window filtering
- Convert transaction date → `YYYY-MM`
- Keep only those months within:
  - start_month ≤ txn_month ≤ end_month

---

## 9) Month Grouping Logic

**Grouping key**
- `YYYY-MM`

Example:
- 2025-01
- 2025-02
- 2025-03

**Output**
A dictionary where each month maps to a list of transactions.

---

## 10) Output PDF Format (Recommended)

### Title Page / Header
- Report Title
- Keyword used
- Date range used
- Total matched transactions
- Generation timestamp

### For each month
- Month name heading (e.g., January 2025)
- Table:
  - Date
  - Description
  - Amount (with explicit signs: +1600.00 for credits, -250.00 for debits)

### Optional summary
- Monthly totals (with explicit signs)
- Grand total

---

## 11) Handling Multiple PDFs (Optional but Supported)

### Strategy
- Extract transactions from each PDF independently
- Merge into one transaction list
- Then apply filtering + grouping

### Output options
- Single combined report PDF  
OR  
- One report per bank/query

---

## 12) Edge Cases & How We Handle Them

### 12.1 Amount sign missing
Handled via category headers (credit/debit).
Amount sign is **never trusted from the raw PDF**.

### 12.2 Category header not detected
- Mark type as `"unknown"`
- Skip the transaction (do not extract)
- Log for review

### 12.3 Multi-line descriptions
**This is a core feature in v1, not v1.1.**

Some statements wrap descriptions into the next line.
Strategy:
- Detect lines without date but continuing text
- Lines that don't start with a date and aren't category headers
- Append to previous transaction description
- Transaction is finalized when next anchor line or category change occurs

### 12.4 Page breaks
No special logic needed if we parse all pages as one stream.

### 12.5 Different date formats
Support can be extended later:
- MM/DD/YYYY
- DD/MM/YYYY
- YYYY-MM-DD

---

## 13) Logging & Observability (Recommended)

For production readiness:
- Add `logging` module
- Log:
  - number of pages read
  - number of transaction candidates found
  - number of valid transactions
  - number filtered by keyword
  - number filtered by date window
  - number written to output

---

## 14) Security & Privacy Considerations

Bank statements contain sensitive data.

Recommended:
- Do not store raw PDFs permanently
- Delete temp files after processing
- Do not log raw statement content
- Only log counts/metadata

---

## 15) Performance Notes

### Why PyMuPDF
- Very fast for multi-page PDFs
- Works well for text-based statements
- Layout features available later if needed

### Complexity
- Parsing is O(N) over lines
- Very efficient even for 100+ pages

---

## 16) Future Upgrade Path (ML-ready)

This rule-based system is intentionally modular so we can later add:

### ML extractor
- Layout-based extraction
- Model learns transaction row patterns

### LLM fallback
- Only used when parsing confidence is low

### OCR
- For scanned statements (image PDFs)

---

## 17) Non-Goals for v1 (Explicit Boundaries)

The following are **intentionally excluded** from v1 to maintain focus:

* **No balance reconciliation** - We extract transactions only, not verify account balances
* **No OCR** - v1 assumes text-based PDFs (scanned PDFs not supported)
* **No ML/AI** - Pure rule-based extraction
* **No semantic parsing** of reference fields - We capture them as-is in descriptions
* **No transaction categorization** - Beyond credit/debit, no spending categories
* **No multi-currency handling** - Assume single currency per statement
* **No duplicate detection** - User responsible for not uploading same statement twice

These can be added in future versions based on user needs.

---

## 18) v1 Success Criteria

The system is correct and successful if:

* **Only transactions under valid categories are extracted** - No balance lines, no summaries
* **Amount signs are always correct** - Credits positive, debits negative
* **Multi-line transactions are merged properly** - Full description captured
* **Output PDF is clean and human-readable** - Proper formatting and grouping
* **Keyword filtering works case-insensitively** - Matches partial strings
* **Month filtering is accurate** - Only transactions within date range
* **No false positives** - Better to miss a transaction than extract non-transaction data

---

## 19) Implementation Checklist (What we will code in v1)

### Must-have
- [ ] Multi-page PDF loader (PyMuPDF)
- [ ] Category detection (credit/debit state tracking)
- [ ] Transaction anchor detection (date + amount pattern)
- [ ] Multi-line description merging
- [ ] Transaction parsing (date, description, amount)
- [ ] Sign application (credit positive, debit negative)
- [ ] Transaction validation
- [ ] Keyword filtering (case-insensitive)
- [ ] Month range filtering
- [ ] Month grouping
- [ ] Output PDF report (reportlab)

### Nice-to-have (v1.1)
- [ ] Better table formatting in PDF
- [ ] Monthly and grand totals
- [ ] CLI interface with arguments
- [ ] Support for multiple date formats
- [ ] Summary statistics in report

---

## 20) Example User Scenario

### User input
- PDF: `statement.pdf`
- Keyword: `"Bank of America"`
- Range: `"2025-01"` → `"2025-03"`

### Processing
The system will:
1. Extract all text from the PDF
2. Track category state as it scans lines
3. Identify transaction anchors under valid categories
4. Merge multi-line descriptions
5. Apply correct sign based on category
6. Filter by keyword (case-insensitive match)
7. Filter by month range
8. Group by month

### Output
A new PDF:
- Header with keyword, date range, and generation timestamp
- **January 2025** section with matching transactions
- **February 2025** section with matching transactions
- **March 2025** section with matching transactions

Each transaction row:
- Date | Description | Amount  
- Debit transactions display with negative sign: **-250.00**
- Credit transactions display with positive sign: **+1600.00**
- Descriptions are complete (multi-line merged)

---

## 21) Final Notes

This v1 design is:
- **Focused and clear** - Explicit boundaries (Non-Goals)
- **Efficient** - O(N) line scanning
- **Cleanly modular** - Each component has single responsibility
- **Production-aligned** - Handles real-world edge cases
- **Testable** - Clear success criteria
- **Ready for ML upgrade later** - Modular architecture allows easy enhancement

**Key implementation priorities:**
1. Multi-line description handling is **core to v1**, not optional
2. Category state tracking is essential for correct sign application
3. Transaction anchor detection prevents false positives
4. Validation ensures data quality

Once v1 is implemented and tested on real PDFs, the next evolution includes:
- Support for scanned PDFs (OCR)
- ML-based transaction detection
- Template variance handling
- Enhanced transaction categorization

---

**This document is the single source of truth for v1 implementation.**

**End of Document**
