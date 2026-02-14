"""
Simple test script for Bank Statement Extractor API
"""

import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_process_statements(pdf_files, keywords, start_month, end_month):
    """Test process statements endpoint"""
    print(f"\n2. Processing {len(pdf_files)} PDF file(s)...")
    
    # Prepare files
    files = []
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return False
        files.append(('files', (Path(pdf_path).name, open(pdf_path, 'rb'), 'application/pdf')))
    
    # Prepare data
    data = {
        'keywords': keywords,
        'start_month': start_month,
        'end_month': end_month
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", files=files, data=data)
        print(f"Status Code: {response.status_code}")
        
        result = response.json()
        print(f"\n✅ Response:")
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success':
            print(f"\n📄 Report generated: {result['report']['filename']}")
            print(f"📊 Total transactions: {result['summary']['total_matched_transactions']}")
            print(f"🏦 Banks found: {result['summary']['banks_found']}")
            
            # Show bank summary
            print(f"\n💰 Bank Summary:")
            for bank, summary in result.get('bank_summary', {}).items():
                print(f"  {bank}:")
                print(f"    - Transactions: {summary['transaction_count']}")
                print(f"    - Deposits: +{summary['total_deposits']:.2f}")
                print(f"    - Withdrawals: {summary['total_withdrawals']:.2f}")
                print(f"    - Net: {summary['net_amount']:.2f}")
            
            return result['report']['download_url']
        else:
            print(f"⚠️ Status: {result.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None
    finally:
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()

def test_list_reports():
    """Test list reports endpoint"""
    print("\n3. Listing available reports...")
    response = requests.get(f"{BASE_URL}/reports")
    print(f"Status Code: {response.status_code}")
    
    result = response.json()
    print(f"Total reports: {result['total_reports']}")
    
    if result['reports']:
        print("\nAvailable reports:")
        for i, report in enumerate(result['reports'][:5], 1):  # Show first 5
            print(f"  {i}. {report['filename']} ({report['size_bytes']} bytes)")
    
    return response.status_code == 200

def test_download_report(download_url):
    """Test download report endpoint"""
    print(f"\n4. Downloading report...")
    
    response = requests.get(f"{BASE_URL}{download_url}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        # Save to current directory
        filename = download_url.split('/')[-1]
        output_path = Path(f"test_download_{filename}")
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Report downloaded: {output_path}")
        print(f"📦 Size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Download failed")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Bank Statement Extractor API - Test Script")
    print("=" * 60)
    
    # Configuration
    PDF_FILES = [
        # Add your PDF file paths here
        # "path/to/statement1.pdf",
        # "path/to/statement2.pdf",
    ]
    
    KEYWORDS = "Bank of America,Wells Fargo,JPMorgan Chase"
    START_MONTH = "2026-01"
    END_MONTH = "2026-12"
    
    # Check if PDF files are provided
    if not PDF_FILES:
        print("\n⚠️  No PDF files configured!")
        print("Please edit this script and add PDF file paths to the PDF_FILES list")
        print("\nExample:")
        print('PDF_FILES = ["statement1.pdf", "statement2.pdf"]')
        return
    
    # Run tests
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health check
    tests_total += 1
    if test_health_check():
        tests_passed += 1
    
    # Test 2: Process statements
    tests_total += 1
    download_url = test_process_statements(PDF_FILES, KEYWORDS, START_MONTH, END_MONTH)
    if download_url:
        tests_passed += 1
        
        # Test 4: Download report
        tests_total += 1
        if test_download_report(download_url):
            tests_passed += 1
    
    # Test 3: List reports
    tests_total += 1
    if test_list_reports():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests completed: {tests_passed}/{tests_total} passed")
    print("=" * 60)

if __name__ == "__main__":
    main()
