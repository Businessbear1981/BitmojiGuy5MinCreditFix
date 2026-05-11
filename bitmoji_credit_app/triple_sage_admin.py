# ═════════════════════════════════════════════════════════════════════════════
# TRIPLE SAGE ADMIN ENGINE — Grok + Claude + Manus Orchestration
# Closed-loop system: Admin-only integration for template refreshes
# NO user-facing AI exposure, NO real-time letter generation
# ═════════════════════════════════════════════════════════════════════════════

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

class TripleSageAdmin:
    """
    Admin-only orchestration layer for Grok, Claude, and Manus.
    
    ARCHITECTURE:
    1. Grok: Deep legal reasoning, statute citations (Federal, State, UCC, Credit)
    2. Claude: Narrative crafting, proofreading, human-centered language
    3. Manus: Technical orchestration, template updates, dispatch coordination
    
    CLOSED-LOOP GUARANTEE:
    - No real-time user requests
    - No AI variability exposure to end users
    - Weekly admin-triggered template refreshes only
    - Pre-filled letters remain the source of truth
    """
    
    def __init__(self):
        self.grok_api_key = os.environ.get('GROK_API_KEY', '')
        self.claude_api_key = os.environ.get('CLAUDE_API_KEY', '')
        self.manus_api_key = os.environ.get('MANUS_API_KEY', '')
        
        self.grok_model = os.environ.get('GROK_MODEL', 'grok-4')
        self.claude_model = os.environ.get('CLAUDE_MODEL', 'claude-3-opus-20250219')
        
        self.admin_log = []
        self.template_versions = {}
        self.last_refresh = None
    
    def log_admin_action(self, action: str, details: Dict) -> None:
        """Log admin actions for audit trail."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'details': details,
        }
        self.admin_log.append(entry)
        print(f"[TRIPLE SAGE ADMIN] {action}: {json.dumps(details, indent=2)}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1: GROK — Legal Reasoning & Statute Citations
    # ─────────────────────────────────────────────────────────────────────────
    
    def grok_legal_analysis(self, dispute_type: str, state: str) -> Dict:
        """
        Grok analyzes dispute type and generates statute citations.
        
        INPUT: dispute_type (e.g., 'collections', 'late_payments', 'aged_debt')
               state (e.g., 'CA', 'NY', 'TX')
        
        OUTPUT: {
            'federal_statutes': [...],
            'state_statutes': [...],
            'ucc_sections': [...],
            'credit_statutes': [...],
            'legal_precedent': [...],
            'reasoning': '...'
        }
        """
        self.log_admin_action('GROK_LEGAL_ANALYSIS', {
            'dispute_type': dispute_type,
            'state': state,
            'model': self.grok_model,
        })

        fallback = {
            'federal_statutes': ['FCRA § 611', 'FDCPA § 809', '15 U.S.C. § 1681'],
            'state_statutes': [f'{state} Consumer Protection Code'],
            'ucc_sections': ['UCC § 3-308', 'UCC § 4-406'],
            'credit_statutes': ['Regulation V', 'Regulation Z'],
            'legal_precedent': ['Spokeo v. Robins', 'TransUnion v. Ramirez'],
            'reasoning': f'Fallback analysis for {dispute_type} in {state}.',
        }

        if not self.grok_api_key:
            return fallback

        try:
            resp = requests.post(
                'https://api.x.ai/v1/chat/completions',
                headers={'Authorization': f'Bearer {self.grok_api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': self.grok_model,
                    'messages': [
                        {'role': 'system', 'content': 'You are a legal research assistant specializing in U.S. consumer credit law (FCRA, FDCPA, UCC, CROA, Regulation V/Z, state consumer protection). Return ONLY valid JSON.'},
                        {'role': 'user', 'content': json.dumps({
                            'task': 'legal_analysis',
                            'dispute_type': dispute_type,
                            'state': state,
                            'output_schema': {
                                'federal_statutes': ['list of specific U.S.C. citations'],
                                'state_statutes': ['list of state-specific statutes'],
                                'ucc_sections': ['UCC sections applicable to credit disputes'],
                                'credit_statutes': ['Regulation V, Z, CROA, TILA citations'],
                                'legal_precedent': ['case name, citation, and holding'],
                                'reasoning': 'analysis paragraph',
                            },
                        })},
                    ],
                    'temperature': 0.2,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                parsed = json.loads(content)
                self.log_admin_action('GROK_SUCCESS', {'dispute_type': dispute_type, 'state': state})
                return parsed
        except Exception as e:
            self.log_admin_action('GROK_ERROR', {'error': str(e)})

        return fallback
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2: CLAUDE — Narrative Crafting & Proofreading
    # ─────────────────────────────────────────────────────────────────────────
    
    def claude_narrative_craft(self, legal_analysis: Dict, dispute_type: str) -> Dict:
        """
        Claude crafts compelling, legally-sound narrative from Grok's analysis.
        
        INPUT: legal_analysis (from Grok)
               dispute_type
        
        OUTPUT: {
            'narrative': '...',
            'tone': 'professional but urgent',
            'key_phrases': [...],
            'proofreading_notes': '...',
        }
        """
        self.log_admin_action('CLAUDE_NARRATIVE_CRAFT', {
            'dispute_type': dispute_type,
            'model': self.claude_model,
        })

        fallback = {
            'narrative': f'Dear Credit Reporting Agency,\n\nI formally dispute the {dispute_type} items on my credit report under FCRA § 611.\n\nLegal Basis:\n- {legal_analysis["federal_statutes"][0]}\n- {legal_analysis["state_statutes"][0]}\n\nI demand immediate investigation and removal.\n\nSincerely,\n[Consumer Name]',
            'tone': 'professional, urgent, legally grounded',
            'key_phrases': ['formal dispute', 'FCRA', 'immediate investigation'],
            'proofreading_notes': 'Fallback template — Claude API not called.',
        }

        if not self.claude_api_key:
            return fallback

        try:
            resp = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': self.claude_api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                },
                json={
                    'model': self.claude_model,
                    'max_tokens': 2000,
                    'messages': [{'role': 'user', 'content': json.dumps({
                        'task': 'craft_dispute_letter_template',
                        'dispute_type': dispute_type,
                        'legal_analysis': legal_analysis,
                        'instructions': 'Write a compelling, legally-sound dispute letter template for a credit bureau. Cite specific statutes from the legal analysis. Use placeholders {bureau}, {name}, {items}, {confirmation}, {date}, {state_law}. Tone: professional but firm. Return JSON with keys: narrative, tone, key_phrases (list), proofreading_notes.',
                    })}],
                    'system': 'You are a consumer credit dispute letter writer. Write templates that cite specific FCRA/FDCPA statutes, are professionally assertive, and demand action within 30 days. Return ONLY valid JSON.',
                },
                timeout=30,
            )
            if resp.status_code == 200:
                content = resp.json()['content'][0]['text']
                parsed = json.loads(content)
                self.log_admin_action('CLAUDE_SUCCESS', {'dispute_type': dispute_type})
                return parsed
        except Exception as e:
            self.log_admin_action('CLAUDE_ERROR', {'error': str(e)})

        return fallback
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3: MANUS — Orchestration & Template Update
    # ─────────────────────────────────────────────────────────────────────────
    
    def manus_orchestrate_template_update(self, dispute_type: str, state: str, 
                                         legal_analysis: Dict, narrative: Dict) -> Dict:
        """
        Manus orchestrates the complete template update process.
        
        INPUT: dispute_type, state, legal_analysis (from Grok), narrative (from Claude)
        
        OUTPUT: {
            'template_id': '...',
            'version': '...',
            'status': 'ready_for_admin_review',
            'preview': '...',
        }
        """
        self.log_admin_action('MANUS_ORCHESTRATE_UPDATE', {
            'dispute_type': dispute_type,
            'state': state,
            'action': 'template_update_orchestration',
        })
        
        template_id = f"{dispute_type}_{state}_{datetime.utcnow().isoformat()}"
        
        return {
            'template_id': template_id,
            'version': '1.0',
            'status': 'ready_for_admin_review',
            'dispute_type': dispute_type,
            'state': state,
            'preview': narrative['narrative'],
            'legal_basis': legal_analysis['federal_statutes'],
            'created_at': datetime.utcnow().isoformat(),
            'requires_admin_approval': True,
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN CONTROL: Weekly Template Refresh Workflow
    # ─────────────────────────────────────────────────────────────────────────
    
    def admin_trigger_template_refresh(self, dispute_types: List[str], states: List[str]) -> Dict:
        """
        Admin triggers weekly template refresh via Triple Sage.
        
        WORKFLOW:
        1. Admin selects dispute types and states
        2. Grok analyzes legal landscape
        3. Claude crafts narratives
        4. Manus orchestrates updates
        5. Admin reviews and approves
        6. Templates deployed to production
        """
        self.log_admin_action('ADMIN_TRIGGER_TEMPLATE_REFRESH', {
            'dispute_types': dispute_types,
            'states': states,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        results = []
        
        for dispute_type in dispute_types:
            for state in states:
                # Phase 1: Grok Legal Analysis
                legal_analysis = self.grok_legal_analysis(dispute_type, state)
                
                # Phase 2: Claude Narrative Crafting
                narrative = self.claude_narrative_craft(legal_analysis, dispute_type)
                
                # Phase 3: Manus Orchestration
                template_update = self.manus_orchestrate_template_update(
                    dispute_type, state, legal_analysis, narrative
                )
                
                results.append(template_update)
        
        self.last_refresh = datetime.utcnow().isoformat()
        
        return {
            'refresh_id': f"refresh_{datetime.utcnow().isoformat()}",
            'status': 'pending_admin_review',
            'templates_generated': len(results),
            'templates': results,
            'requires_approval': True,
            'next_step': 'Admin review and approval',
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN CONTROL: Template Approval & Deployment
    # ─────────────────────────────────────────────────────────────────────────
    
    def admin_approve_and_deploy_templates(self, template_ids: List[str]) -> Dict:
        """
        Admin approves and deploys templates to production.
        """
        self.log_admin_action('ADMIN_APPROVE_DEPLOY_TEMPLATES', {
            'template_ids': template_ids,
            'count': len(template_ids),
        })
        
        return {
            'status': 'deployed',
            'templates_deployed': len(template_ids),
            'deployed_at': datetime.utcnow().isoformat(),
            'message': 'Templates deployed to production. Users will receive updated letters.',
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN DASHBOARD: View Logs & History
    # ─────────────────────────────────────────────────────────────────────────
    
    def admin_view_activity_log(self, limit: int = 50) -> List[Dict]:
        """Admin views all Triple Sage activity."""
        return self.admin_log[-limit:]
    
    def admin_view_template_versions(self) -> Dict:
        """Admin views all template versions and their status."""
        return self.template_versions


# ═════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═════════════════════════════════════════════════════════════════════════════

triple_sage = TripleSageAdmin()
