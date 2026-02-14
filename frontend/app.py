"""
Bank Statement Transaction Extractor - Streamlit Frontend
Multi-bank transaction extraction and PDF report generation
"""

import streamlit as st
import sys
import logging
from pathlib import Path
from datetime import datetime
import tempfile

# Setup logging with DEBUG level to see extraction details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import backend modules
from loaders.pdf_loader import load_pdf
from extractors.regex_extractor import extract_transactions_from_text
from validators.financial_validator import validate_transactions
from main import TransactionFilter, TransactionGrouper
from output.writer import generate_pdf_report

# Page configuration
st.set_page_config(
    page_title="Bank Statement Extractor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ef8145;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #808183;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #e8e0dc;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #e8e0dc;
        border: 1px solid #ef8145;
        color: #ef8145;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #e8e0dc;
        border: 1px solid #ef8145;
        color: #000000;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'results' not in st.session_state:
    st.session_state.results = None


def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">🏦 Bank Statement Transaction Extractor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Extract and analyze transactions from multiple bank statement PDFs</div>', unsafe_allow_html=True)
    
    # Sidebar - Input Configuration
    with st.sidebar:
        st.header("📋 Configuration")
        
        # File upload
        st.subheader("1. Upload PDFs")
        uploaded_files = st.file_uploader(
            "Choose bank statement PDF(s)",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDFs containing bank transactions"
        )
        
        st.divider()
        
        # Keywords input
        st.subheader("2. Bank Keywords")
        st.caption("Enter keywords to identify transactions for each bank")
        
        keywords_input = st.text_area(
            "Keywords (one per line)",
            value="Bank of America\nWells Fargo\nJPMorgan Chase",
            height=120,
            help="Enter one keyword per line. Transactions matching each keyword will be grouped separately."
        )
        
        st.divider()
        
        # Date range
        st.subheader("3. Date Range")
        col1, col2 = st.columns(2)
        
        with col1:
            start_month = st.date_input(
                "Start Month",
                value=datetime(2026, 1, 1),
                help="First month to include in the report"
            )
        
        with col2:
            end_month = st.date_input(
                "End Month",
                value=datetime(2026, 12, 31),
                help="Last month to include in the report"
            )
        
        st.divider()
        
        # Process button
        process_btn = st.button(
            "🚀 Process Statements",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_files
        )
    
    # Main content area
    if not uploaded_files:
        # Welcome screen
        st.info("👈 Upload one or more PDF files from the sidebar to get started")
        
        st.subheader("How it works:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📤 Step 1")
            st.write("Upload one or more bank statement PDFs containing transactions")
        
        with col2:
            st.markdown("### 🔍 Step 2")
            st.write("Enter keywords to identify each bank's transactions")
        
        with col3:
            st.markdown("### 📊 Step 3")
            st.write("Get a detailed PDF report with transactions grouped by bank and month")
        
        st.divider()
        
        st.subheader("Features:")
        features = [
            "✅ Process multiple PDF files at once",
            "✅ Extract transactions from mixed multi-bank statements",
            "✅ Automatically categorize deposits and withdrawals",
            "✅ Group transactions by bank, month, and type",
            "✅ Calculate totals and subtotals",
            "✅ Generate professional PDF reports",
            "✅ Handle unmatched transactions separately"
        ]
        
        for feature in features:
            st.markdown(feature)
    
    # Process the statements
    if process_btn and uploaded_files:
        process_statements(uploaded_files, keywords_input, start_month, end_month)
    
    # Display results if available
    if st.session_state.processed and st.session_state.results:
        display_results()


def process_statements(uploaded_files, keywords_input, start_month, end_month):
    """Process multiple uploaded statements and generate report."""
    
    try:
        with st.spinner(f"Processing {len(uploaded_files)} PDF file(s)..."):
            # Parse keywords
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            
            if not keywords:
                st.error("❌ Please enter at least one keyword")
                return
            
            st.write(f"### 🔍 Keywords to search ({len(keywords)} total):")
            for i, keyword in enumerate(keywords, 1):
                st.write(f"{i}. {keyword}")
            
            # Format dates
            start_month_str = start_month.strftime("%Y-%m")
            end_month_str = end_month.strftime("%Y-%m")
            
            # Step 1: Load all PDFs and extract transactions
            progress_bar = st.progress(0, text="Loading PDFs...")
            
            all_transactions = []
            pdf_names = []
            temp_files = []  # Keep track of temp files
            
            for idx, uploaded_file in enumerate(uploaded_files):
                pdf_name = uploaded_file.name
                pdf_names.append(pdf_name)
                progress = int(20 * (idx + 1) / len(uploaded_files))
                progress_bar.progress(progress, text=f"Loading {pdf_name}...")
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                    temp_files.append(tmp_path)
                
                # Extract text and transactions from this PDF
                try:
                    text = load_pdf(tmp_path)
                    transactions_from_pdf = extract_transactions_from_text(text)
                    
                    # Log progress
                    st.write(f"✓ {pdf_name}: Extracted {len(transactions_from_pdf)} transactions")
                    
                    all_transactions.extend(transactions_from_pdf)
                    
                except Exception as e:
                    st.warning(f"⚠️ Error processing {pdf_name}: {str(e)}")
                    continue
            
            # Cleanup temp files
            for tmp_path in temp_files:
                try:
                    Path(tmp_path).unlink()
                except:
                    pass
            
            st.info(f"📄 **Processed {len(uploaded_files)} PDF(s)**: {', '.join(pdf_names)}")
            st.info(f"📊 **Total transactions extracted**: {len(all_transactions)}")
            progress_bar.progress(20, text="Extracting transactions...")
            progress_bar.progress(40, text="Validating transactions...")
            
            # Step 2: Validate all transactions from all PDFs
            valid_transactions = validate_transactions(all_transactions)
            
            # Show date range found in PDF
            if valid_transactions:
                dates = [t.date for t in valid_transactions]
                min_date = min(dates)
                max_date = max(dates)
                st.info(f"📅 **Transactions found**: {min_date} to {max_date} ({len(valid_transactions)} total)")
            
            progress_bar.progress(60, text="Filtering by keywords...")
            
            # Step 4: Filter by keywords
            filtered_by_bank = TransactionFilter.filter_by_keywords(valid_transactions, keywords)
            
            # Show which banks were found
            st.write("### 🏦 Banks Found:")
            for bank, txns in filtered_by_bank.items():
                st.write(f"- **{bank}**: {len(txns)} transactions")
            
            progress_bar.progress(70, text="Grouping by bank and month...")
            
            # Step 5: Apply date range filter
            filtered_by_date = {}
            total_before_date_filter = sum(len(txns) for txns in filtered_by_bank.values())
            
            for bank, txns in filtered_by_bank.items():
                filtered_txns = TransactionFilter.filter_by_date_range(
                    txns, start_month_str, end_month_str
                )
                if filtered_txns:
                    filtered_by_date[bank] = filtered_txns
            
            total_after_date_filter = sum(len(txns) for txns in filtered_by_date.values())
            
            # Warn if date filter removed all transactions
            if total_before_date_filter > 0 and total_after_date_filter == 0:
                st.error(f"⚠️ **Date range mismatch**: {total_before_date_filter} transactions found, but 0 match your date range ({start_month_str} to {end_month_str}). Please adjust the date range to match the transactions in your PDFs.")
                progress_bar.empty()
                return
            
            progress_bar.progress(80, text="Generating PDF report...")
            
            # Step 6: Group by bank, month, type
            grouped = TransactionGrouper.group_by_bank_month_type(filtered_by_date)
            
            # Step 7: Generate PDF
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"report_{timestamp}.pdf"
            
            # Calculate total transactions
            total_txns = sum(
                len(month_data.get('deposits', [])) + len(month_data.get('withdrawals', []))
                for bank_months in grouped.values()
                for month_data in bank_months.values()
            )
            
            generate_pdf_report(
                output_path=str(output_path),
                grouped_data=grouped,
                keywords=keywords,
                start_month=start_month_str,
                end_month=end_month_str,
                total_transactions=total_txns
            )
            
            progress_bar.progress(100, text="Complete!")
            
            # Store results
            st.session_state.processed = True
            st.session_state.pdf_path = output_path
            st.session_state.results = {
                'total_transactions': len(valid_transactions),
                'filtered_transactions': total_txns,
                'grouped': grouped,
                'keywords': keywords,
                'banks_found': len([k for k in grouped.keys() if k != 'Unmatched'])
            }
            
            st.success("✅ Processing complete!")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error processing statements: {str(e)}")
        st.exception(e)


def display_results():
    """Display processing results and download button."""
    
    results = st.session_state.results
    
    # Success message
    st.markdown(
        f'<div class="success-box">✅ Successfully processed statement with {results["total_transactions"]} transactions</div>',
        unsafe_allow_html=True
    )
    
    # Metrics
    st.subheader("📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", results['total_transactions'])
    
    with col2:
        st.metric("Filtered Transactions", results['filtered_transactions'])
    
    with col3:
        st.metric("Banks Identified", results['banks_found'])
    
    with col4:
        st.metric("Keywords Used", len(results['keywords']))
    
    st.divider()
    
    # Bank breakdown
    st.subheader("🏦 Transaction Breakdown by Bank")
    
    grouped = results['grouped']
    
    for bank in sorted(grouped.keys()):
        if bank == 'Unmatched':
            continue
            
        months = grouped[bank]
        
        # Calculate bank totals
        total_deposits = sum(
            t.amount for month_data in months.values()
            for t in month_data.get('deposits', [])
        )
        total_withdrawals = sum(
            t.amount for month_data in months.values()
            for t in month_data.get('withdrawals', [])
        )
        net = total_deposits + total_withdrawals
        
        total_txns = sum(
            len(month_data.get('deposits', [])) + len(month_data.get('withdrawals', []))
            for month_data in months.values()
        )
        
        with st.expander(f"**{bank}** - {total_txns} transactions, Net: ${net:+,.2f}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Deposits", f"${total_deposits:,.2f}")
            
            with col2:
                st.metric("Total Withdrawals", f"${total_withdrawals:,.2f}")
            
            with col3:
                st.metric("Net Amount", f"${net:+,.2f}", delta=f"{net:+,.2f}")
            
            # Month breakdown
            st.markdown("**Monthly Breakdown:**")
            for month in sorted(months.keys()):
                month_data = months[month]
                deposits_count = len(month_data.get('deposits', []))
                withdrawals_count = len(month_data.get('withdrawals', []))
                
                st.markdown(f"- **{month}**: {deposits_count} deposits, {withdrawals_count} withdrawals")
    
    # Unmatched transactions
    if 'Unmatched' in grouped:
        unmatched_count = sum(
            len(month_data.get('deposits', [])) + len(month_data.get('withdrawals', []))
            for month_data in grouped['Unmatched'].values()
        )
        
        if unmatched_count > 0:
            st.warning(f"⚠️ {unmatched_count} transactions did not match any keyword and are grouped as 'Unmatched'")
    
    st.divider()
    
    # Download section
    st.subheader("📥 Download Report")
    
    if st.session_state.pdf_path and st.session_state.pdf_path.exists():
        with open(st.session_state.pdf_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name=f"bank_statement_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            st.info(f"📄 Report saved: {st.session_state.pdf_path.name}")
    
    st.divider()
    
    # Reset button
    if st.button("🔄 Process Another Statement", use_container_width=True):
        st.session_state.processed = False
        st.session_state.pdf_path = None
        st.session_state.results = None
        st.rerun()


if __name__ == "__main__":
    main()
