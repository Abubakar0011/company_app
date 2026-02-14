"""
PDF Report Writer Module
Generates formatted PDF reports from filtered and grouped transactions.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from extractors.regex_extractor import Transaction

logger = logging.getLogger(__name__)


class PDFReportWriter:
    """Generates PDF reports from transaction data."""
    
    def __init__(self, output_path: str, page_size=letter):
        """
        Initialize PDF writer.
        
        Args:
            output_path: Path where PDF will be saved
            page_size: Page size (default: letter)
        """
        self.output_path = output_path
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#444444'),
            spaceAfter=6
        ))
    
    def generate_report(
        self,
        grouped_transactions: dict[str, list[Transaction]],
        keyword: str,
        start_month: str,
        end_month: str,
        total_transactions: int
    ):
        """
        Generate PDF report from grouped transactions.
        
        Args:
            grouped_transactions: Dict mapping month (YYYY-MM) to list of transactions
            keyword: Search keyword used
            start_month: Start month of filter range
            end_month: End month of filter range
            total_transactions: Total number of transactions before filtering
            
        Raises:
            Exception: If PDF generation fails
        """
        # Input validation
        if grouped_transactions is None:
            logger.error("grouped_transactions cannot be None")
            raise ValueError("grouped_transactions cannot be None")
        
        if not isinstance(grouped_transactions, dict):
            logger.error("grouped_transactions must be a dictionary")
            raise ValueError("grouped_transactions must be a dictionary")
        
        logger.info(f"Generating PDF report: {self.output_path}")
        logger.info(f"Report contains {len(grouped_transactions)} months, {total_transactions} total transactions")
        
        try:
            # Ensure output directory exists
            output_path = Path(self.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            
            try:
                # Add header
                story.extend(self._create_header(keyword, start_month, end_month, total_transactions))
                
                # Add transactions by month
                if not grouped_transactions:
                    logger.warning("No transactions to include in report")
                    story.append(Paragraph("No transactions found matching the criteria.", self.styles['InfoText']))
                else:
                    for month in sorted(grouped_transactions.keys()):
                        transactions = grouped_transactions[month]
                        if transactions:
                            logger.debug(f"Adding section for {month} with {len(transactions)} transactions")
                            story.extend(self._create_month_section(month, transactions))
                
                # Build PDF
                logger.info("Building PDF document...")
                doc.build(story)
                logger.info(f"PDF report generated successfully: {self.output_path}")
                
            except Exception as e:
                logger.error(f"Error building PDF content: {e}", exc_info=True)
                raise
                
        except PermissionError as e:
            logger.error(f"Permission denied writing to {self.output_path}: {e}")
            raise Exception(f"Cannot write to {self.output_path}. File may be open or directory is read-only.") from e
            
        except OSError as e:
            logger.error(f"OS error writing PDF: {e}", exc_info=True)
            raise Exception(f"Failed to write PDF file: {e}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error generating PDF report: {e}", exc_info=True)
            raise
    
    def generate_multi_bank_report(
        self,
        grouped_data: dict[str, dict[str, dict[str, list[Transaction]]]],
        keywords: list[str],
        start_month: str,
        end_month: str,
        total_transactions: int
    ):
        """
        Generate PDF report with multiple banks, each with deposits/withdrawals separated.
        
        Args:
            grouped_data: {bank: {month: {'deposits': [...], 'withdrawals': [...]}}}
            keywords: List of keywords/banks
            start_month: Start month filter
            end_month: End month filter
            total_transactions: Total transaction count
        """
        if grouped_data is None or not isinstance(grouped_data, dict):
            raise ValueError("grouped_data must be a dictionary")
        
        logger.info(f"Generating multi-bank PDF report: {self.output_path}")
        logger.info(f"Report contains {len(grouped_data)} banks, {total_transactions} total transactions")
        
        try:
            # Ensure output directory exists
            output_path = Path(self.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            try:
                # Add header
                story.extend(self._create_multi_bank_header(
                    keywords, start_month, end_month, total_transactions
                ))
                
                # Add each bank's section
                if not grouped_data:
                    story.append(Paragraph(
                        "No transactions found matching the criteria.",
                        self.styles['InfoText']
                    ))
                else:
                    # Process regular banks first, then Unmatched
                    banks_to_process = sorted([b for b in grouped_data.keys() if b != 'Unmatched'])
                    if 'Unmatched' in grouped_data:
                        banks_to_process.append('Unmatched')
                    
                    for bank in banks_to_process:
                        bank_data = grouped_data[bank]
                        if bank_data:
                            logger.debug(f"Adding section for bank '{bank}'")
                            story.extend(self._create_bank_section(bank, bank_data))
                
                # Build PDF
                logger.info("Building PDF document...")
                doc.build(story)
                logger.info(f"PDF report generated successfully: {self.output_path}")
                
            except Exception as e:
                logger.error(f"Error building PDF content: {e}", exc_info=True)
                raise
                
        except PermissionError as e:
            logger.error(f"Permission denied writing to {self.output_path}: {e}")
            raise Exception(
                f"Cannot write to {self.output_path}. File may be open or directory is read-only."
            ) from e
            
        except OSError as e:
            logger.error(f"OS error writing PDF: {e}", exc_info=True)
            raise Exception(f"Failed to write PDF file: {e}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error generating PDF report: {e}", exc_info=True)
            raise
    
    def _create_header(
        self,
        keyword: str,
        start_month: str,
        end_month: str,
        total_transactions: int
    ) -> list:
        """Create report header section."""
        elements = []
        
        # Title
        title = Paragraph("Bank Statement Transaction Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Report info
        info_lines = [
            f"<b>Keyword:</b> {keyword}",
            f"<b>Date Range:</b> {start_month} to {end_month}",
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"<b>Total Matched Transactions:</b> {total_transactions}"
        ]
        
        for line in info_lines:
            elements.append(Paragraph(line, self.styles['InfoText']))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_month_section(self, month: str, transactions: list[Transaction]) -> list:
        """
        Create a section for one month's transactions.
        
        Args:
            month: Month string (YYYY-MM)
            transactions: List of transactions for this month
            
        Returns:
            List of reportlab elements
        """
        elements = []
        
        # Month heading
        month_name = self._format_month_heading(month)
        elements.append(Paragraph(month_name, self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Create transaction table
        table = self._create_transaction_table(transactions)
        elements.append(table)
        
        # Add monthly total
        total = sum(txn.amount for txn in transactions)
        total_display = f"+{total:.2f}" if total >= 0 else f"{total:.2f}"
        total_para = Paragraph(
            f"<b>Month Total: {total_display}</b>",
            self.styles['InfoText']
        )
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(total_para)
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_transaction_table(
        self,
        transactions: list[Transaction],
        month: str = '',
        bank_name: str = '',
        transaction_type: str = ''
    ) -> Table:
        """
        Create table of transactions with context header.
        
        Args:
            transactions: List of Transaction objects
            month: Month string (e.g., "January 2026")
            bank_name: Bank name
            transaction_type: "Deposits" or "Withdrawals"
            
        Returns:
            reportlab Table object
        """
        if not transactions:
            logger.warning("Creating table with no transactions")
            return Table([['Date', 'Description', 'Amount'], ['No transactions', '', '']])
        
        try:
            # Table data with context header and column header
            data = [
                [month or '', bank_name or '', transaction_type or ''],  # Context header
                ['Date', 'Description', 'Amount']  # Column header
            ]
            
            for txn in transactions:
                try:
                    data.append([
                        txn.date or '[No date]',
                        self._truncate_description(txn.description or '[No description]', max_length=60),
                        txn.amount_display or '0.00'
                    ])
                except Exception as e:
                    logger.warning(f"Error formatting transaction {txn}: {e}")
                    continue
            
            # Calculate total
            total = sum(t.amount for t in transactions)
            total_display = f"+{total:.2f}" if total >= 0 else f"{total:.2f}"
            
            # Add total row
            data.append(['', 'TOTAL', total_display])
            
            # Create table
            table = Table(data, colWidths=[1.2 * inch, 4.5 * inch, 1.2 * inch])
            
            # Style table
            table.setStyle(TableStyle([
                # Context header row (row 0) - Orange background, white text
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),     # Month - left aligned
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),   # Bank name - center
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),    # Transaction type - right
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Column header row (row 1) - Orange background, white text
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 12),
                ('TOPPADDING', (0, 1), (-1, 1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
                
                # Data rows base style - white background, black text
                ('BACKGROUND', (0, 2), (-1, -2), colors.HexColor('#ffffff')),
                ('TEXTCOLOR', (0, 2), (-1, -2), colors.HexColor('#000000')),
                ('ALIGN', (0, 2), (0, -2), 'CENTER'),  # Date column
                ('ALIGN', (1, 2), (1, -2), 'LEFT'),    # Description column
                ('ALIGN', (2, 2), (2, -2), 'RIGHT'),   # Amount column
                ('FONTNAME', (0, 2), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 2), (-1, -2), 10),
                ('TOPPADDING', (0, 2), (-1, -2), 6),
                ('BOTTOMPADDING', (0, 2), (-1, -2), 6),
                
                # Total row styling - Light orange background, black text
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#000000')),
                ('ALIGN', (1, -1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, -1), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('TOPPADDING', (0, -1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#808183')),
                
                # Alternating row colors - beige for even rows
                *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e8e0dc')) 
                  for i in range(3, len(data) - 1, 2)]  # Start from row 3 (first data row after two headers)
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Error creating transaction table: {e}", exc_info=True)
            # Return minimal table on error
            return Table([['Date', 'Description', 'Amount'], ['Error creating table', '', '']])
    
    def _create_bank_totals_table(
        self,
        bank_name: str,
        total_deposits: float,
        total_withdrawals: float
    ) -> Table:
        """
        Create bank totals summary table.
        
        Args:
            bank_name: Bank name
            total_deposits: Total deposits amount
            total_withdrawals: Total withdrawals amount
            
        Returns:
            reportlab Table object
        """
        try:
            # Calculate net
            net_total = total_deposits + total_withdrawals
            
            # Format displays
            deposits_display = f"+{total_deposits:.2f}"
            withdrawals_display = f"{total_withdrawals:.2f}"
            net_display = f"+{net_total:.2f}" if net_total >= 0 else f"{net_total:.2f}"
            
            # Table data
            data = [
                [bank_name, '', ''],  # Context header - bank name spans conceptually
                ['Total Deposits', 'Total Withdrawals', 'Net Amount'],  # Column headers
                [deposits_display, withdrawals_display, net_display]  # Data row
            ]
            
            # Create table with equal column widths
            table = Table(data, colWidths=[2.3 * inch, 2.3 * inch, 2.3 * inch])
            
            # Style table
            table.setStyle(TableStyle([
                # Context header row (row 0) - bank name - Orange background, white text
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('SPAN', (0, 0), (-1, 0)),  # Span bank name across all columns
                
                # Column header row (row 1) - Orange background, white text
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 12),
                ('TOPPADDING', (0, 1), (-1, 1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
                
                # Data row (row 2) - Light orange background, black text (summary row)
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#ef8145')),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#000000')),
                ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 2), (-1, 2), 11),
                ('TOPPADDING', (0, 2), (-1, 2), 10),
                ('BOTTOMPADDING', (0, 2), (-1, 2), 10),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#808183'))
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Error creating bank totals table: {e}", exc_info=True)
            return Table([['Bank Totals', '', ''], ['Error creating table', '', '']])
    
    def _create_multi_bank_header(
        self,
        keywords: list[str],
        start_month: str,
        end_month: str,
        total_transactions: int
    ) -> list:
        """Create header for multi-bank report."""
        elements = []
        
        # Title
        title = Paragraph("Bank Statement Transaction Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_bank_section(
        self,
        bank: str,
        bank_data: dict[str, dict[str, list[Transaction]]]
    ) -> list:
        """
        Create section for one bank with all its months.
        
        Args:
            bank: Bank name/keyword
            bank_data: {month: {'deposits': [...], 'withdrawals': [...]}}
        """
        elements = []
        
        # Add small spacer before bank section (bank name now in table headers)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Calculate bank totals across all months
        total_deposits = 0.0
        total_withdrawals = 0.0
        
        for month_data in bank_data.values():
            if 'deposits' in month_data:
                total_deposits += sum(t.amount for t in month_data['deposits'])
            if 'withdrawals' in month_data:
                total_withdrawals += sum(t.amount for t in month_data['withdrawals'])
        
        # Add each month
        for month in sorted(bank_data.keys()):
            month_data = bank_data[month]
            elements.extend(self._create_month_section_multi(month, month_data, bank_name=bank))
        
        # Add bank totals table (right after last month, before page break)
        # Remove the last PageBreak from the last month to place totals on same page
        if elements and isinstance(elements[-1], PageBreak):
            elements.pop()  # Remove the page break from last month
        
        elements.append(Spacer(1, 0.2 * inch))
        bank_totals_table = self._create_bank_totals_table(bank, total_deposits, total_withdrawals)
        elements.append(bank_totals_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Add page break after bank totals so next bank starts on new page
        elements.append(PageBreak())
        
        return elements
    
    def _create_month_section_multi(
        self,
        month: str,
        month_data: dict[str, list[Transaction]],
        bank_name: str = ''
    ) -> list:
        """
        Create month section with deposits and withdrawals separated.
        
        Args:
            month: Month string (YYYY-MM)
            month_data: {'deposits': [...], 'withdrawals': [...]}
            bank_name: Bank name to include in table header
        """
        elements = []
        
        # Format month name
        month_name = self._format_month_heading(month)
        
        # Deposits section (no separate heading - info in table header)
        if 'deposits' in month_data and month_data['deposits']:
            deposits = month_data['deposits']
            table = self._create_transaction_table(
                deposits,
                month=month_name,
                bank_name=bank_name,
                transaction_type='Deposits'
            )
            elements.append(table)
            elements.append(Spacer(1, 0.15 * inch))
        
        # Withdrawals section (no separate heading - info in table header)
        if 'withdrawals' in month_data and month_data['withdrawals']:
            withdrawals = month_data['withdrawals']
            table = self._create_transaction_table(
                withdrawals,
                month=month_name,
                bank_name=bank_name,
                transaction_type='Withdrawals'
            )
            elements.append(table)
            elements.append(Spacer(1, 0.15 * inch))
        
        # Add page break so next month starts on fresh page
        elements.append(PageBreak())
        
        return elements
    
    @staticmethod
    def _format_month_heading(month: str) -> str:
        """
        Format month string for display.
        
        Args:
            month: Month string (YYYY-MM)
            
        Returns:
            Formatted month name (e.g., "January 2025")
        """
        try:
            date_obj = datetime.strptime(month, '%Y-%m')
            return date_obj.strftime('%B %Y')
        except ValueError:
            return month
    
    @staticmethod
    def _truncate_description(description: str, max_length: int = 60) -> str:
        """
        Truncate description if too long.
        
        Args:
            description: Transaction description
            max_length: Maximum length
            
        Returns:
            Truncated description with ellipsis if needed
        """
        if len(description) <= max_length:
            return description
        return description[:max_length - 3] + "..."


def generate_pdf_report(
    output_path: str,
    grouped_data: dict[str, dict[str, dict[str, list[Transaction]]]],
    keywords: list[str],
    start_month: str,
    end_month: str,
    total_transactions: int
):
    """
    Convenience function to generate multi-bank PDF report.
    
    Args:
        output_path: Path where PDF will be saved
        grouped_data: Nested dict {bank: {month: {'deposits': [...], 'withdrawals': [...]}}}
        keywords: List of keywords/bank names
        start_month: Start month filter
        end_month: End month filter
        total_transactions: Total transaction count
    """
    writer = PDFReportWriter(output_path)
    writer.generate_multi_bank_report(
        grouped_data,
        keywords,
        start_month,
        end_month,
        total_transactions
    )
