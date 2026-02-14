"""
FastAPI Backend for Bank Statement Transaction Extractor
RESTful API endpoints for processing bank statements
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import tempfile
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import backend modules
from loaders.pdf_loader import load_pdf
from extractors.regex_extractor import extract_transactions_from_text
from validators.financial_validator import validate_transactions
from main import TransactionFilter, TransactionGrouper
from output.writer import generate_pdf_report

# Initialize FastAPI app
app = FastAPI(
    title="Bank Statement Extractor API",
    description="Extract and analyze transactions from bank statement PDFs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "api_reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Bank Statement Transaction Extractor API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process": "Process PDF statements and generate report",
            "GET /health": "Health check",
            "GET /reports/{filename}": "Download generated report"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/process")
async def process_statements(
    files: List[UploadFile] = File(..., description="One or more PDF files"),
    keywords: str = Form(..., description="Comma-separated bank keywords"),
    start_month: str = Form(..., description="Start month (YYYY-MM)"),
    end_month: str = Form(..., description="End month (YYYY-MM)")
):
    """
    Process bank statement PDFs and generate a consolidated report.
    
    - **files**: List of PDF files to process
    - **keywords**: Comma-separated list of bank keywords (e.g., "Bank of America,Wells Fargo,Chase")
    - **start_month**: Start month in YYYY-MM format
    - **end_month**: End month in YYYY-MM format
    
    Returns a JSON response with report details and download link.
    """
    try:
        logger.info(f"Processing {len(files)} PDF file(s)")
        
        # Parse keywords
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        
        if not keyword_list:
            raise HTTPException(status_code=400, detail="At least one keyword is required")
        
        if not files:
            raise HTTPException(status_code=400, detail="At least one PDF file is required")
        
        # Validate date format
        try:
            datetime.strptime(start_month, "%Y-%m")
            datetime.strptime(end_month, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM")
        
        # Step 1: Extract transactions from all PDFs
        all_transactions = []
        temp_files = []
        pdf_info = []
        
        for uploaded_file in files:
            # Validate file type
            if not uploaded_file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type: {uploaded_file.filename}. Only PDF files are allowed"
                )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await uploaded_file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
                temp_files.append(tmp_path)
            
            # Extract transactions
            try:
                text = load_pdf(tmp_path)
                transactions = extract_transactions_from_text(text)
                all_transactions.extend(transactions)
                
                pdf_info.append({
                    "filename": uploaded_file.filename,
                    "transactions_extracted": len(transactions)
                })
                
                logger.info(f"Extracted {len(transactions)} transactions from {uploaded_file.filename}")
                
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.filename}: {str(e)}")
                pdf_info.append({
                    "filename": uploaded_file.filename,
                    "error": str(e)
                })
        
        # Cleanup temp files
        for tmp_path in temp_files:
            try:
                Path(tmp_path).unlink()
            except:
                pass
        
        # Step 2: Validate transactions
        valid_transactions = validate_transactions(all_transactions)
        logger.info(f"Total valid transactions: {len(valid_transactions)}")
        
        if not valid_transactions:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_transactions",
                    "message": "No valid transactions found in the uploaded PDFs",
                    "pdf_info": pdf_info
                }
            )
        
        # Step 3: Filter by keywords
        filtered_by_bank = TransactionFilter.filter_by_keywords(valid_transactions, keyword_list)
        
        # Step 4: Apply date range filter
        filtered_by_date = {}
        for bank, txns in filtered_by_bank.items():
            filtered_txns = TransactionFilter.filter_by_date_range(txns, start_month, end_month)
            if filtered_txns:
                filtered_by_date[bank] = filtered_txns
        
        if not filtered_by_date:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_matches",
                    "message": "No transactions match the specified keywords and date range",
                    "total_transactions": len(valid_transactions),
                    "keywords": keyword_list,
                    "date_range": f"{start_month} to {end_month}",
                    "pdf_info": pdf_info
                }
            )
        
        # Step 5: Group by bank, month, type
        grouped = TransactionGrouper.group_by_bank_month_type(filtered_by_date)
        
        # Step 6: Generate PDF report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{timestamp}.pdf"
        report_path = OUTPUT_DIR / report_filename
        
        # Calculate total transactions
        total_txns = sum(
            len(month_data.get('deposits', [])) + len(month_data.get('withdrawals', []))
            for bank_months in grouped.values()
            for month_data in bank_months.values()
        )
        
        generate_pdf_report(
            output_path=str(report_path),
            grouped_data=grouped,
            keywords=keyword_list,
            start_month=start_month,
            end_month=end_month,
            total_transactions=total_txns
        )
        
        logger.info(f"Report generated: {report_filename}")
        
        # Prepare bank summary
        bank_summary = {}
        for bank, bank_data in grouped.items():
            total_deposits = 0.0
            total_withdrawals = 0.0
            transaction_count = 0
            
            for month_data in bank_data.values():
                deposits = month_data.get('deposits', [])
                withdrawals = month_data.get('withdrawals', [])
                
                total_deposits += sum(t.amount for t in deposits)
                total_withdrawals += sum(t.amount for t in withdrawals)
                transaction_count += len(deposits) + len(withdrawals)
            
            bank_summary[bank] = {
                "transaction_count": transaction_count,
                "total_deposits": round(total_deposits, 2),
                "total_withdrawals": round(total_withdrawals, 2),
                "net_amount": round(total_deposits + total_withdrawals, 2)
            }
        
        # Return success response
        return {
            "status": "success",
            "message": "Report generated successfully",
            "report": {
                "filename": report_filename,
                "download_url": f"/reports/{report_filename}",
                "generated_at": datetime.now().isoformat()
            },
            "summary": {
                "total_pdfs_processed": len(files),
                "total_transactions_extracted": len(all_transactions),
                "total_valid_transactions": len(valid_transactions),
                "total_matched_transactions": total_txns,
                "keywords_used": keyword_list,
                "date_range": f"{start_month} to {end_month}",
                "banks_found": len([k for k in grouped.keys() if k != 'Unmatched'])
            },
            "bank_summary": bank_summary,
            "pdf_info": pdf_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing statements: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/reports/{filename}")
async def download_report(filename: str):
    """
    Download a generated PDF report.
    
    - **filename**: Name of the report file to download
    """
    report_path = OUTPUT_DIR / filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=filename
    )


@app.get("/reports")
async def list_reports():
    """List all available reports"""
    reports = []
    
    for report_file in OUTPUT_DIR.glob("*.pdf"):
        reports.append({
            "filename": report_file.name,
            "created_at": datetime.fromtimestamp(report_file.stat().st_ctime).isoformat(),
            "size_bytes": report_file.stat().st_size,
            "download_url": f"/reports/{report_file.name}"
        })
    
    # Sort by creation time (newest first)
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        "total_reports": len(reports),
        "reports": reports
    }


@app.delete("/reports/{filename}")
async def delete_report(filename: str):
    """
    Delete a report file.
    
    - **filename**: Name of the report file to delete
    """
    report_path = OUTPUT_DIR / filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        report_path.unlink()
        return {
            "status": "success",
            "message": f"Report {filename} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
