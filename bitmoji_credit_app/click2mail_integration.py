# ═════════════════════════════════════════════════════════════════════════════
# CLICK2MAIL INTEGRATION — Certified Mail Dispatch with Admin Release
# ═════════════════════════════════════════════════════════════════════════════

import os
import json
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError:
    print("WARNING: reportlab not installed. PDF generation will fail.")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

CLICK2MAIL_API_URL = 'https://rest.click2mail.com/molpro'
CLICK2MAIL_USERNAME = os.environ.get('CLICK2MAIL_USERNAME', os.environ.get('CLICK2MAIL_API_KEY', ''))
CLICK2MAIL_PASSWORD = os.environ.get('CLICK2MAIL_PASSWORD', os.environ.get('CLICK2MAIL_API_SECRET', ''))

# Credit bureau mailing addresses (USPS verified)
BUREAU_ADDRESSES = {
    'Equifax': {
        'name': 'Equifax Information Services',
        'address': 'PO Box 740256',
        'city': 'Atlanta',
        'state': 'GA',
        'zip': '30374',
    },
    'TransUnion': {
        'name': 'TransUnion Consumer Solutions',
        'address': 'PO Box 2000',
        'city': 'Chester',
        'state': 'PA',
        'zip': '19016',
    },
    'Experian': {
        'name': 'Experian Disputes',
        'address': 'PO Box 4500',
        'city': 'Allen',
        'state': 'TX',
        'zip': '75013',
    },
}

# CFPB and regulatory addresses for escalation
REGULATORY_ADDRESSES = {
    'CFPB': {
        'name': 'Consumer Financial Protection Bureau',
        'address': '1700 G Street NW',
        'city': 'Washington',
        'state': 'DC',
        'zip': '20552',
    },
    'FTC': {
        'name': 'Federal Trade Commission',
        'address': '600 Pennsylvania Avenue NW',
        'city': 'Washington',
        'state': 'DC',
        'zip': '20580',
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_dispute_letter_pdf(
    sender_name: str,
    sender_address: str,
    sender_city: str,
    sender_state: str,
    sender_zip: str,
    recipient_name: str,
    recipient_address: str,
    recipient_city: str,
    recipient_state: str,
    recipient_zip: str,
    letter_body: str,
    include_cfpb_notice: bool = False,
) -> bytes:
    """
    Generate a professional dispute letter PDF using ReportLab.
    
    Returns: PDF as bytes (ready for base64 encoding)
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Sender address (top left)
    sender_block = f"{sender_name}<br/>{sender_address}<br/>{sender_city}, {sender_state} {sender_zip}"
    story.append(Paragraph(sender_block, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Date
    today = datetime.utcnow().strftime('%B %d, %Y')
    story.append(Paragraph(f"<b>{today}</b>", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Recipient address
    recipient_block = f"{recipient_name}<br/>{recipient_address}<br/>{recipient_city}, {recipient_state} {recipient_zip}"
    story.append(Paragraph(recipient_block, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Salutation
    story.append(Paragraph("To Whom It May Concern:", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Letter body
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontSize=11,
        leading=14,
    )
    for paragraph in letter_body.split('\n\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
            story.append(Spacer(1, 0.15*inch))
    
    # CFPB notice if escalation
    if include_cfpb_notice:
        story.append(Spacer(1, 0.2*inch))
        notice = """
        <b>NOTICE OF REGULATORY COMPLAINT:</b><br/>
        This letter is being sent simultaneously with formal complaints to the Consumer Financial Protection Bureau (CFPB),
        the Federal Trade Commission (FTC), and the state Attorney General regarding non-compliance with the Fair Credit Reporting Act.
        """
        story.append(Paragraph(notice, body_style))
    
    # Signature block
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("Sincerely,", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(sender_name, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.read()


# ─────────────────────────────────────────────────────────────────────────────
# CLICK2MAIL API CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class Click2MailClient:
    """
    Click2Mail REST API v1 client with proper authentication and error handling.
    
    Docs: https://www.click2mail.com/api/documentation
    """
    
    def __init__(self, username: str = '', password: str = ''):
        self.username = username or CLICK2MAIL_USERNAME
        self.password = password or CLICK2MAIL_PASSWORD
        self.base_url = CLICK2MAIL_API_URL
        self.session = requests.Session()

        # Click2Mail uses HTTP Basic Auth (username + password)
        if self.username:
            self.session.auth = (self.username, self.password)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Click2Mail API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp.json() if resp.text else {'status': 'ok'}
        except requests.exceptions.HTTPError as e:
            return {
                'error': True,
                'status_code': e.response.status_code,
                'message': e.response.text[:500],
            }
        except Exception as e:
            return {'error': True, 'message': str(e)}
    
    def create_job(
        self,
        pdf_base64: str,
        sender_name: str,
        sender_address: str,
        sender_city: str,
        sender_state: str,
        sender_zip: str,
        recipient_name: str,
        recipient_address: str,
        recipient_city: str,
        recipient_state: str,
        recipient_zip: str,
        mail_class: str = 'First Class',
        return_receipt: bool = False,
    ) -> Dict:
        """
        Create a Click2Mail job for certified mail dispatch.
        
        mail_class: 'First Class', 'Certified Mail', 'Priority Mail'
        """
        payload = {
            'document': {
                'file': pdf_base64,
                'fileType': 'pdf',
            },
            'from': {
                'name': sender_name,
                'address': sender_address,
                'city': sender_city,
                'state': sender_state,
                'zip': sender_zip,
            },
            'to': {
                'name': recipient_name,
                'address': recipient_address,
                'city': recipient_city,
                'state': recipient_state,
                'zip': recipient_zip,
            },
            'mailClass': mail_class,
            'returnReceipt': return_receipt,
            'color': True,
            'doubleSided': False,
        }
        
        return self._make_request('POST', '/jobs', json=payload)
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get status of a Click2Mail job."""
        return self._make_request('GET', f'/jobs/{job_id}')
    
    def list_jobs(self, limit: int = 50) -> Dict:
        """List recent Click2Mail jobs."""
        return self._make_request('GET', f'/jobs?limit={limit}')


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN RELEASE WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────

class AdminReleaseManager:
    """
    Manages admin approval and release of certified mail dispatch.
    
    WORKFLOW:
    1. User completes payment → letters generated (not sent)
    2. Admin reviews submission in dashboard
    3. Admin clicks "Release for Mailing"
    4. Click2Mail jobs created and dispatched
    5. Watcher tracking begins
    """
    
    def __init__(self):
        self.pending_releases = {}  # session_id -> submission data
        self.release_log = []
    
    def queue_for_release(self, session_id: str, submission: Dict) -> Dict:
        """Queue a submission for admin review before mailing."""
        self.pending_releases[session_id] = {
            'submission': submission,
            'queued_at': datetime.utcnow().isoformat(),
            'status': 'pending_admin_review',
        }
        
        self.release_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'queued_for_release',
            'session_id': session_id,
            'user_name': submission.get('name', 'unknown'),
        })
        
        return {'ok': True, 'status': 'queued_for_admin_review'}
    
    def admin_approve_and_release(self, session_id: str, admin_id: str) -> Dict:
        """Admin approves and releases submission for mailing."""
        if session_id not in self.pending_releases:
            return {'error': True, 'message': 'Submission not found in queue'}
        
        queue_entry = self.pending_releases[session_id]
        submission = queue_entry['submission']
        
        self.release_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'admin_approved_release',
            'session_id': session_id,
            'admin_id': admin_id,
            'user_name': submission.get('name', 'unknown'),
        })
        
        # Mark as released (actual mailing happens in dispatch_certified_mail)
        submission['admin_released'] = True
        submission['released_at'] = datetime.utcnow().isoformat()
        submission['released_by'] = admin_id
        
        del self.pending_releases[session_id]
        
        return {'ok': True, 'status': 'released_for_mailing'}
    
    def admin_reject_release(self, session_id: str, admin_id: str, reason: str = '') -> Dict:
        """Admin rejects release (e.g., for review or corrections)."""
        if session_id not in self.pending_releases:
            return {'error': True, 'message': 'Submission not found in queue'}
        
        queue_entry = self.pending_releases[session_id]
        submission = queue_entry['submission']
        
        self.release_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'admin_rejected_release',
            'session_id': session_id,
            'admin_id': admin_id,
            'user_name': submission.get('name', 'unknown'),
            'reason': reason,
        })
        
        submission['admin_rejected'] = True
        submission['rejection_reason'] = reason
        
        del self.pending_releases[session_id]
        
        return {'ok': True, 'status': 'rejected', 'reason': reason}
    
    def get_pending_queue(self) -> List[Dict]:
        """Admin views all pending releases."""
        return [
            {
                'session_id': sid,
                'user_name': data['submission'].get('name', 'unknown'),
                'queued_at': data['queued_at'],
                'letter_count': len(data['submission'].get('letters', [])),
            }
            for sid, data in self.pending_releases.items()
        ]
    
    def get_release_log(self, limit: int = 100) -> List[Dict]:
        """Admin views release activity log."""
        return self.release_log[-limit:]


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCH ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────

def dispatch_certified_mail(
    submission: Dict,
    day_number: int = 0,
    manual_mail_class: str = '',
) -> Dict:
    """
    Dispatch letters via Click2Mail (only if admin released).
    
    ESCALATION STRATEGY:
    - Day 0-29: First Class (no tracking)
    - Day 30-59: Certified Mail (tracking only)
    - Day 60-89: Certified Mail + Return Receipt
    - Day 90+: Certified Mail + Return Receipt + CFPB Notice
    """
    
    # Check admin release
    if not submission.get('admin_released'):
        return {
            'error': True,
            'message': 'Submission not approved for mailing. Awaiting admin release.',
            'sent': 0,
        }
    
    # Determine mail class based on follow-up day
    if manual_mail_class in ('First Class', 'Certified Mail', 'Priority Mail'):
        mail_class = manual_mail_class
        return_receipt = manual_mail_class == 'Certified Mail'
        include_cfpb_notice = False
    elif day_number >= 90:
        mail_class = 'Certified Mail'
        return_receipt = True
        include_cfpb_notice = True
    elif day_number >= 60:
        mail_class = 'Certified Mail'
        return_receipt = True
        include_cfpb_notice = False
    elif day_number >= 30:
        mail_class = 'Certified Mail'
        return_receipt = False
        include_cfpb_notice = False
    else:
        mail_class = 'First Class'
        return_receipt = False
        include_cfpb_notice = False
    
    # Extract sender info
    sender_name = submission.get('name', '')
    sender_address = submission.get('address', '')
    sender_city = submission.get('city', '')
    sender_state = submission.get('state', '')
    sender_zip = submission.get('zip', '')
    
    if not all([sender_name, sender_address, sender_state]):
        return {
            'error': True,
            'message': 'Incomplete sender information',
            'sent': 0,
        }
    
    # Initialize Click2Mail client
    client = Click2MailClient()
    if not client.api_key:
        return {
            'error': True,
            'message': 'Click2Mail not configured',
            'sent': 0,
        }
    
    letters = submission.get('letters', [])
    if not letters:
        return {
            'error': True,
            'message': 'No letters to send',
            'sent': 0,
        }
    
    sent = 0
    job_ids = []
    errors = []
    
    for letter in letters:
        bureau = letter.get('bureau', '')
        bureau_addr = BUREAU_ADDRESSES.get(bureau)
        
        if not bureau_addr:
            errors.append({'bureau': bureau, 'error': 'Bureau address not found'})
            continue
        
        try:
            # Generate PDF
            letter_body = letter.get('body', '')
            if include_cfpb_notice:
                letter_body += '\n\n--- CFPB COMPLAINT NOTICE ---\n'
                letter_body += 'This letter is being sent simultaneously with formal complaints to the CFPB, FTC, and state Attorney General.'
            
            pdf_bytes = generate_dispute_letter_pdf(
                sender_name=sender_name,
                sender_address=sender_address,
                sender_city=sender_city,
                sender_state=sender_state,
                sender_zip=sender_zip,
                recipient_name=bureau_addr['name'],
                recipient_address=bureau_addr['address'],
                recipient_city=bureau_addr['city'],
                recipient_state=bureau_addr['state'],
                recipient_zip=bureau_addr['zip'],
                letter_body=letter_body,
                include_cfpb_notice=include_cfpb_notice,
            )
            
            # Encode as base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Create Click2Mail job
            result = client.create_job(
                pdf_base64=pdf_base64,
                sender_name=sender_name,
                sender_address=sender_address,
                sender_city=sender_city,
                sender_state=sender_state,
                sender_zip=sender_zip,
                recipient_name=bureau_addr['name'],
                recipient_address=bureau_addr['address'],
                recipient_city=bureau_addr['city'],
                recipient_state=bureau_addr['state'],
                recipient_zip=bureau_addr['zip'],
                mail_class=mail_class,
                return_receipt=return_receipt,
            )
            
            if result.get('error'):
                errors.append({'bureau': bureau, 'error': result.get('message', 'Unknown error')})
            else:
                job_id = result.get('id') or result.get('jobId')
                job_ids.append({
                    'bureau': bureau,
                    'job_id': str(job_id),
                    'title': letter.get('title', ''),
                    'mail_class': mail_class,
                })
                sent += 1
        
        except Exception as e:
            errors.append({'bureau': bureau, 'error': str(e)})
    
    # Record dispatch metadata
    now = datetime.utcnow()
    submission['dispatched_at'] = now.isoformat()
    submission['status'] = 'dispatched'
    submission['follow_up_dates'] = {
        'day_30': (now + timedelta(days=30)).isoformat(),
        'day_60': (now + timedelta(days=60)).isoformat(),
        'day_90': (now + timedelta(days=90)).isoformat(),
    }
    submission['job_ids'] = job_ids
    
    return {
        'ok': True,
        'sent': sent,
        'job_ids': job_ids,
        'errors': errors if errors else None,
        'mail_class': mail_class,
        'return_receipt': return_receipt,
    }


# ─────────────────────────────────────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

admin_release_manager = AdminReleaseManager()
click2mail_client = Click2MailClient()
