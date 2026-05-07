# ═════════════════════════════════════════════════════════════════════════════
# FREE CREDIT REPORT HOOK — AnnualCreditReport.com Integration
# ═════════════════════════════════════════════════════════════════════════════

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ANNUAL_CREDIT_REPORT_URL = 'https://www.annualcreditreport.com'
CREDIT_BUREAUS = ['Equifax', 'TransUnion', 'Experian']

# Dispute categories (aligned with FCRA § 611)
class DisputeCategory(Enum):
    COLLECTIONS = 'collections'
    LATE_PAYMENTS = 'late_payments'
    CHARGE_OFFS = 'charge_offs'
    INQUIRIES = 'inquiries'
    IDENTITY_FRAUD = 'identity_fraud'
    MIXED_FILES = 'mixed_files'
    OUTDATED_INFO = 'outdated_info'
    INCORRECT_ADDRESS = 'incorrect_address'
    UNAUTHORIZED_ACCOUNTS = 'unauthorized_accounts'
    PAID_ACCOUNTS = 'paid_accounts'
    OTHER = 'other'


# ─────────────────────────────────────────────────────────────────────────────
# CREDIT REPORT PARSER
# ─────────────────────────────────────────────────────────────────────────────

class CreditReportParser:
    """
    Parse credit reports (PDF, CSV, TXT) to extract disputable accounts.
    
    SUPPORTED FORMATS:
    - PDF: Extracted via pdfplumber + OCR
    - CSV: Direct parsing
    - TXT: Regex-based extraction
    """
    
    # Regex patterns for common account identifiers
    PATTERNS = {
        'account_number': r'Account\s*(?:Number|#|No\.?)[\s:]*([A-Za-z0-9\-\*]+)',
        'creditor_name': r'(?:Creditor|Company|Lender)[\s:]*([A-Za-z0-9\s\&\.]+)',
        'balance': r'(?:Balance|Amount|Outstanding)[\s:]*\$?([\d,\.]+)',
        'status': r'(?:Status|Account Status)[\s:]*([A-Za-z\s]+)',
        'date_opened': r'(?:Opened|Date Opened)[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        'date_reported': r'(?:Reported|Date Reported|Last Reported)[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        'payment_history': r'(?:Payment History|Status History)[\s:]*([A-Za-z0-9\s\-]+)',
        'late_payment': r'(\d+)\s*(?:days?|mos?)\s*(?:late|past due)',
        'charge_off': r'(?:Charged Off|Charge Off|Charged-off)',
        'collection': r'(?:Collection|Collections|Sent to Collection)',
        'inquiry': r'(?:Inquiry|Inquiries|Hard Inquiry)',
    }
    
    def __init__(self):
        self.raw_text = ''
        self.extracted_accounts = []
        self.disputes = []
    
    def parse_text(self, text: str) -> Dict:
        """Parse raw credit report text."""
        self.raw_text = text
        self.extracted_accounts = []
        self.disputes = []
        
        # Split into account sections
        account_sections = self._split_into_accounts(text)
        
        for section in account_sections:
            account = self._extract_account_info(section)
            if account:
                self.extracted_accounts.append(account)
        
        # Classify disputes
        self.disputes = self._classify_disputes(self.extracted_accounts)
        
        return {
            'accounts_found': len(self.extracted_accounts),
            'disputes_found': len(self.disputes),
            'accounts': self.extracted_accounts,
            'disputes': self.disputes,
        }
    
    def _split_into_accounts(self, text: str) -> List[str]:
        """Split credit report into individual account sections."""
        # Common delimiters between accounts
        delimiters = [
            r'(?:^|\n)(?:ACCOUNT|Account)\s+\d+',
            r'(?:^|\n)(?:TRADELINE|Tradeline)',
            r'(?:^|\n)(?:INQUIRY|Inquiry)',
        ]
        
        sections = [text]
        for delimiter in delimiters:
            new_sections = []
            for section in sections:
                parts = re.split(delimiter, section, flags=re.MULTILINE | re.IGNORECASE)
                new_sections.extend([p for p in parts if p.strip()])
            sections = new_sections
        
        return sections
    
    def _extract_account_info(self, section: str) -> Optional[Dict]:
        """Extract structured account information from a section."""
        if not section.strip():
            return None
        
        account = {
            'raw_text': section[:200],  # Store snippet for reference
            'extracted_at': datetime.utcnow().isoformat(),
        }
        
        # Extract each field
        for field, pattern in self.PATTERNS.items():
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                account[field] = match.group(1).strip()
        
        # Determine account type
        account['type'] = self._determine_account_type(section)
        
        return account if account.get('creditor_name') else None
    
    def _determine_account_type(self, section: str) -> str:
        """Determine account type (tradeline, inquiry, collection, etc.)."""
        section_lower = section.lower()
        
        if re.search(r'inquiry|inquiries', section_lower):
            return 'inquiry'
        elif re.search(r'collection|collections|sent to collection', section_lower):
            return 'collection'
        elif re.search(r'charge.?off|charged.?off', section_lower):
            return 'charge_off'
        elif re.search(r'late|delinquent|past due', section_lower):
            return 'late_payment'
        elif re.search(r'paid|closed|satisfied', section_lower):
            return 'paid_account'
        else:
            return 'tradeline'
    
    def _classify_disputes(self, accounts: List[Dict]) -> List[Dict]:
        """Classify accounts into disputable categories."""
        disputes = []
        
        for account in accounts:
            dispute_categories = []
            dispute_reasons = []
            
            # Check for common dispute triggers
            if account.get('type') == 'collection':
                dispute_categories.append(DisputeCategory.COLLECTIONS.value)
                dispute_reasons.append('Account sent to collections')
            
            if account.get('type') == 'charge_off':
                dispute_categories.append(DisputeCategory.CHARGE_OFFS.value)
                dispute_reasons.append('Account charged off')
            
            if account.get('type') == 'late_payment':
                dispute_categories.append(DisputeCategory.LATE_PAYMENTS.value)
                dispute_reasons.append('Late payment reported')
            
            if account.get('type') == 'inquiry':
                dispute_categories.append(DisputeCategory.INQUIRIES.value)
                dispute_reasons.append('Hard inquiry on credit report')
            
            if account.get('type') == 'paid_account' and account.get('status'):
                if 'paid' in account['status'].lower() or 'closed' in account['status'].lower():
                    dispute_categories.append(DisputeCategory.PAID_ACCOUNTS.value)
                    dispute_reasons.append('Account marked paid but still reporting negatively')
            
            # Check for potential fraud indicators
            if 'unauthorized' in account.get('raw_text', '').lower():
                dispute_categories.append(DisputeCategory.UNAUTHORIZED_ACCOUNTS.value)
                dispute_reasons.append('Unauthorized account')
            
            # Check for outdated information (7-year rule)
            if account.get('date_reported'):
                try:
                    reported_date = datetime.strptime(account['date_reported'], '%m/%d/%Y')
                    if (datetime.utcnow() - reported_date).days > 2555:  # ~7 years
                        dispute_categories.append(DisputeCategory.OUTDATED_INFO.value)
                        dispute_reasons.append('Information older than 7 years (should be removed)')
                except ValueError:
                    pass
            
            if dispute_categories:
                disputes.append({
                    'creditor': account.get('creditor_name', 'Unknown'),
                    'account_number': account.get('account_number', 'Not provided'),
                    'balance': account.get('balance', 'Unknown'),
                    'status': account.get('status', 'Unknown'),
                    'type': account.get('type', 'unknown'),
                    'dispute_categories': dispute_categories,
                    'dispute_reasons': dispute_reasons,
                    'confidence': len(dispute_categories) / len(DisputeCategory),  # Rough confidence score
                    'requires_verification': True,
                })
        
        return disputes


# ─────────────────────────────────────────────────────────────────────────────
# ANNUAL CREDIT REPORT GUIDE
# ─────────────────────────────────────────────────────────────────────────────

class AnnualCreditReportGuide:
    """
    Guide users through obtaining their free annual credit report.
    
    Per FCRA § 612, consumers are entitled to one free report per bureau per year.
    """
    
    @staticmethod
    def get_guide() -> Dict:
        """Return step-by-step guide for obtaining free credit report."""
        return {
            'title': 'Get Your Free Annual Credit Report',
            'description': 'Under the Fair Credit Reporting Act, you are entitled to one free credit report per bureau per year.',
            'bureaus': CREDIT_BUREAUS,
            'steps': [
                {
                    'number': 1,
                    'title': 'Visit AnnualCreditReport.com',
                    'description': 'Go to the official government-authorized website: https://www.annualcreditreport.com',
                    'action': 'open_link',
                    'link': ANNUAL_CREDIT_REPORT_URL,
                },
                {
                    'number': 2,
                    'title': 'Select Your State',
                    'description': 'Choose your state of residence.',
                },
                {
                    'number': 3,
                    'title': 'Provide Personal Information',
                    'description': 'Enter your name, address, Social Security number, and date of birth.',
                    'warning': 'Only provide this info on the official AnnualCreditReport.com website.',
                },
                {
                    'number': 4,
                    'title': 'Choose Bureaus',
                    'description': 'Select which credit bureaus you want reports from (Equifax, TransUnion, Experian).',
                    'tip': 'You can get all three reports at once or stagger them throughout the year.',
                },
                {
                    'number': 5,
                    'title': 'Verify Your Identity',
                    'description': 'Complete identity verification (security questions or other methods).',
                },
                {
                    'number': 6,
                    'title': 'Download Your Reports',
                    'description': 'Download reports as PDF. Save them for your records.',
                    'tip': 'You can also request reports by mail or phone if you prefer.',
                },
                {
                    'number': 7,
                    'title': 'Upload to BitmojiGuy',
                    'description': 'Upload your credit report(s) to the Dojo to identify disputable accounts.',
                    'action': 'upload_report',
                },
            ],
            'phone_number': '1-877-322-8228',
            'mail_address': 'Annual Credit Report Request Service, P.O. Box 105281, Atlanta, GA 30348',
            'faq': [
                {
                    'question': 'Is this really free?',
                    'answer': 'Yes. The federal government requires credit bureaus to provide one free report per year per consumer.',
                },
                {
                    'question': 'Why should I get my credit report?',
                    'answer': 'To identify errors, fraud, or negative items that can be disputed under the FCRA.',
                },
                {
                    'question': 'How long does it take?',
                    'answer': 'Usually 5-10 minutes online. You can get reports immediately or by mail in 15 days.',
                },
                {
                    'question': 'What if I find errors?',
                    'answer': 'That\'s where BitmojiGuy comes in. We help you dispute errors with the credit bureaus.',
                },
            ],
        }
    
    @staticmethod
    def get_bureau_contact_info() -> Dict:
        """Return contact information for credit bureaus."""
        return {
            'Equifax': {
                'phone': '1-800-685-1111',
                'website': 'https://www.equifax.com',
                'dispute_url': 'https://www.equifax.com/personal/credit-report-services/',
            },
            'TransUnion': {
                'phone': '1-800-916-8800',
                'website': 'https://www.transunion.com',
                'dispute_url': 'https://www.transunion.com/credit-disputes/dispute-your-credit',
            },
            'Experian': {
                'phone': '1-888-397-3742',
                'website': 'https://www.experian.com',
                'dispute_url': 'https://www.experian.com/help/disputes/',
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# CREDIT REPORT WORKFLOW MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class CreditReportWorkflow:
    """
    Manage the complete credit report workflow:
    1. Guide user to AnnualCreditReport.com
    2. User obtains and downloads reports
    3. User uploads reports to BitmojiGuy
    4. Parse and extract disputes
    5. Generate dispute letters
    """
    
    def __init__(self):
        self.parser = CreditReportParser()
        self.guide = AnnualCreditReportGuide()
    
    def get_initial_guide(self) -> Dict:
        """Return guide for obtaining credit report."""
        return self.guide.get_guide()
    
    def process_uploaded_report(self, text: str) -> Dict:
        """Process uploaded credit report and extract disputes."""
        result = self.parser.parse_text(text)
        
        return {
            'status': 'processed',
            'summary': {
                'accounts_found': result['accounts_found'],
                'disputes_found': result['disputes_found'],
            },
            'disputes': result['disputes'],
            'next_step': 'Review disputes and generate letters',
        }
    
    def get_dispute_summary(self, disputes: List[Dict]) -> Dict:
        """Generate summary of disputes by category."""
        summary = {}
        
        for dispute in disputes:
            for category in dispute['dispute_categories']:
                if category not in summary:
                    summary[category] = {
                        'count': 0,
                        'items': [],
                    }
                summary[category]['count'] += 1
                summary[category]['items'].append({
                    'creditor': dispute['creditor'],
                    'account': dispute['account_number'],
                    'reasons': dispute['dispute_reasons'],
                })
        
        return summary
    
    def get_bureau_contact_info(self) -> Dict:
        """Return contact info for all bureaus."""
        return self.guide.get_bureau_contact_info()


# ─────────────────────────────────────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

credit_report_workflow = CreditReportWorkflow()
