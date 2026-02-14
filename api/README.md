# Bank Statement Extractor API

FastAPI backend for processing bank statement PDFs and generating consolidated reports.

## Installation

```bash
# Install API dependencies
pip install -r api/requirements.txt
```

## Running the API

```bash
# From the project root directory
cd api
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T12:00:00"
}
```

### 2. Process Statements
```http
POST /process
Content-Type: multipart/form-data
```

**Parameters:**
- `files`: One or more PDF files (multipart/form-data)
- `keywords`: Comma-separated bank keywords (e.g., "Bank of America,Wells Fargo,Chase")
- `start_month`: Start month in YYYY-MM format
- `end_month`: End month in YYYY-MM format

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/process" \
  -F "files=@statement1.pdf" \
  -F "files=@statement2.pdf" \
  -F "files=@statement3.pdf" \
  -F "keywords=Bank of America,Wells Fargo,JPMorgan Chase" \
  -F "start_month=2026-01" \
  -F "end_month=2026-12"
```

**Response:**
```json
{
  "status": "success",
  "message": "Report generated successfully",
  "report": {
    "filename": "report_20260210_120000.pdf",
    "download_url": "/reports/report_20260210_120000.pdf",
    "generated_at": "2026-02-10T12:00:00"
  },
  "summary": {
    "total_pdfs_processed": 3,
    "total_transactions_extracted": 531,
    "total_valid_transactions": 530,
    "total_matched_transactions": 450,
    "keywords_used": ["Bank of America", "Wells Fargo", "JPMorgan Chase"],
    "date_range": "2026-01 to 2026-12",
    "banks_found": 3
  },
  "bank_summary": {
    "Bank of America": {
      "transaction_count": 150,
      "total_deposits": 25000.00,
      "total_withdrawals": -15000.00,
      "net_amount": 10000.00
    },
    "Wells Fargo": {
      "transaction_count": 120,
      "total_deposits": 30000.00,
      "total_withdrawals": -20000.00,
      "net_amount": 10000.00
    }
  },
  "pdf_info": [
    {
      "filename": "statement1.pdf",
      "transactions_extracted": 150
    },
    {
      "filename": "statement2.pdf",
      "transactions_extracted": 200
    }
  ]
}
```

### 3. Download Report
```http
GET /reports/{filename}
```

Downloads the generated PDF report.

**Example:**
```bash
curl -O "http://localhost:8000/reports/report_20260210_120000.pdf"
```

### 4. List Reports
```http
GET /reports
```

Lists all available reports.

**Response:**
```json
{
  "total_reports": 5,
  "reports": [
    {
      "filename": "report_20260210_120000.pdf",
      "created_at": "2026-02-10T12:00:00",
      "size_bytes": 245678,
      "download_url": "/reports/report_20260210_120000.pdf"
    }
  ]
}
```

### 5. Delete Report
```http
DELETE /reports/{filename}
```

Deletes a report file.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/reports/report_20260210_120000.pdf"
```

## Testing with Python

```python
import requests

# Upload and process PDFs
with open('statement1.pdf', 'rb') as f1, \
     open('statement2.pdf', 'rb') as f2:
    
    files = [
        ('files', ('statement1.pdf', f1, 'application/pdf')),
        ('files', ('statement2.pdf', f2, 'application/pdf'))
    ]
    
    data = {
        'keywords': 'Bank of America,Wells Fargo,Chase',
        'start_month': '2026-01',
        'end_month': '2026-12'
    }
    
    response = requests.post('http://localhost:8000/process', files=files, data=data)
    result = response.json()
    
    print(f"Status: {result['status']}")
    print(f"Report: {result['report']['download_url']}")

# Download the report
if result['status'] == 'success':
    report_url = f"http://localhost:8000{result['report']['download_url']}"
    report = requests.get(report_url)
    
    with open('downloaded_report.pdf', 'wb') as f:
        f.write(report.content)
```

## Features

- ✅ RESTful API with FastAPI
- ✅ Multi-PDF upload support
- ✅ Automatic transaction extraction and validation
- ✅ Keyword-based bank matching
- ✅ Date range filtering
- ✅ PDF report generation
- ✅ Report download and management
- ✅ Comprehensive error handling
- ✅ Auto-generated API documentation (Swagger/ReDoc)
- ✅ CORS support for frontend integration

## Notes

- The Streamlit frontend (`frontend/app.py`) remains unchanged and continues to work independently
- Both systems use the same backend processing logic
- API reports are stored in `output/api_reports/` directory
- Frontend reports are stored in `output/` directory
