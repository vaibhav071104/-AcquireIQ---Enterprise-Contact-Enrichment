"""
Contact enrichment using Hunter.io API
"""
import requests
import time
from typing import Optional, Dict, List
from config import settings
from models import EmailVerificationResult, EmailStatus, ConfidenceLevel, Lead
from validator import EmailValidator


class ContactEnricher:
    """Enterprise-grade contact enrichment"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.hunter_api_key
        self.base_url = settings.hunter_base_url
        self.validator = EmailValidator()
        
        if not self.api_key:
            print(" Warning: No Hunter.io API key found. Get free 50 credits/month at https://hunter.io")
    
    def verify_email(self, email: str) -> Optional[EmailVerificationResult]:
        """
        Verify email using Hunter.io Email Verifier API
        Docs: https://hunter.io/api/email-verifier
        """
        if not self.api_key:
            return self._fallback_verification(email)
        
        endpoint = f"{self.base_url}/email-verifier"
        params = {
            'email': email,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                return EmailVerificationResult(
                    email=data.get('email', email),
                    status=self._map_status(data.get('status')),
                    score=data.get('score', 0),
                    confidence_level=ConfidenceLevel.MEDIUM,  # Will be auto-calculated
                    regexp=data.get('regexp', False),
                    gibberish=data.get('gibberish', False),
                    disposable=data.get('disposable', False),
                    webmail=data.get('webmail', False),
                    mx_records=data.get('mx_records', False),
                    smtp_server=data.get('smtp_server', False),
                    smtp_check=data.get('smtp_check', False),
                    accept_all=data.get('accept_all', False),
                    block=data.get('block', False),
                    sources=data.get('sources', [])
                )
            
            elif response.status_code == 429:
                print(f" Rate limit exceeded. Falling back to local validation.")
                return self._fallback_verification(email)
            
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return self._fallback_verification(email)
                
        except Exception as e:
            print(f" Error verifying {email}: {str(e)}")
            return self._fallback_verification(email)
    
    def _fallback_verification(self, email: str) -> EmailVerificationResult:
        """
        Fallback verification using local validation
        """
        validation = self.validator.comprehensive_validation(email)
        
        # Determine status
        if validation['is_disposable']:
            status = EmailStatus.DISPOSABLE
            score = 0
        elif not validation['format_valid']:
            status = EmailStatus.INVALID
            score = 0
        elif not validation['mx_records']:
            status = EmailStatus.INVALID
            score = 20
        elif validation['is_webmail']:
            status = EmailStatus.WEBMAIL
            score = 70
        elif validation['is_valid']:
            status = EmailStatus.VALID
            score = 75
        else:
            status = EmailStatus.UNKNOWN
            score = 50
        
        return EmailVerificationResult(
            email=email,
            status=status,
            score=score,
            confidence_level=ConfidenceLevel.MEDIUM,
            regexp=validation['format_valid'],
            gibberish=validation['is_gibberish'],
            disposable=validation['is_disposable'],
            webmail=validation['is_webmail'],
            mx_records=validation['mx_records'],
            smtp_server=validation['mx_records'],
            smtp_check=False,
            accept_all=False,
            block=False,
            sources=[]
        )
    
    def find_email(self, first_name: str, last_name: str, domain: str) -> Optional[str]:
        """
        Find email using Hunter.io Email Finder API
        Docs: https://hunter.io/api/email-finder
        """
        if not self.api_key:
            return self._guess_email(first_name, last_name, domain)
        
        endpoint = f"{self.base_url}/email-finder"
        params = {
            'domain': domain,
            'first_name': first_name,
            'last_name': last_name,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                email = data.get('email')
                score = data.get('score', 0)
                
                if email and score > 50:
                    return email
            
            return self._guess_email(first_name, last_name, domain)
            
        except Exception as e:
            print(f" Error finding email: {str(e)}")
            return self._guess_email(first_name, last_name, domain)
    
    def _guess_email(self, first_name: str, last_name: str, domain: str) -> str:
        """
        Guess email format (most common pattern)
        """
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        
        # Most common format: first.last@domain.com
        return f"{first}.{last}@{domain}"
    
    def enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich a lead with verified contact information
        """
        enriched_lead = lead.copy()
        enrichment_sources = []
        
        # Verify email if exists
        if lead.email:
            verification = self.verify_email(lead.email)
            if verification:
                enriched_lead.email_status = verification.status
                enriched_lead.email_confidence = verification.score
                enriched_lead.email_sources = verification.sources
                enrichment_sources.append("email_verification")
        
        # Find email if missing
        elif lead.first_name and lead.last_name and lead.company_domain:
            found_email = self.find_email(
                lead.first_name,
                lead.last_name,
                lead.company_domain
            )
            if found_email:
                enriched_lead.email = found_email
                # Verify the found email
                verification = self.verify_email(found_email)
                if verification:
                    enriched_lead.email_status = verification.status
                    enriched_lead.email_confidence = verification.score
                enrichment_sources.append("email_finder")
        
        # Calculate data quality score
        enriched_lead.data_quality_score = self._calculate_quality_score(enriched_lead)
        enriched_lead.is_enriched = True
        enriched_lead.verification_sources = enrichment_sources
        
        return enriched_lead
    
    def bulk_enrich(self, leads: List[Lead], max_requests: int = 50) -> List[Lead]:
        """
        Enrich multiple leads with rate limiting
        """
        enriched_leads = []
        
        for i, lead in enumerate(leads[:max_requests]):
            if i > 0 and i % 10 == 0:
                time.sleep(1)  # Rate limiting
            
            enriched = self.enrich_lead(lead)
            enriched_leads.append(enriched)
            
            print(f"✅ Enriched {i+1}/{min(len(leads), max_requests)}: {lead.company_name or 'Unknown'}")
        
        return enriched_leads
    
    @staticmethod
    def _map_status(status_str: str) -> EmailStatus:
        """Map Hunter.io status to EmailStatus enum"""
        status_map = {
            'valid': EmailStatus.VALID,
            'invalid': EmailStatus.INVALID,
            'accept_all': EmailStatus.ACCEPT_ALL,
            'webmail': EmailStatus.WEBMAIL,
            'disposable': EmailStatus.DISPOSABLE,
            'unknown': EmailStatus.UNKNOWN,
            'blocked': EmailStatus.BLOCKED
        }
        return status_map.get(status_str.lower(), EmailStatus.UNKNOWN)
    
    @staticmethod
    def _calculate_quality_score(lead: Lead) -> int:
        """
        Calculate overall data quality score (0-100)
        """
        score = 0
        
        # Email quality (40 points)
        if lead.email:
            score += 10
            if lead.email_confidence:
                score += min(30, int(lead.email_confidence * 0.3))
        
        # Contact info completeness (20 points)
        if lead.first_name:
            score += 5
        if lead.last_name:
            score += 5
        if lead.phone:
            score += 5
        if lead.linkedin_url:
            score += 5
        
        # Company info completeness (20 points)
        if lead.company_name:
            score += 5
        if lead.company_domain:
            score += 5
        if lead.company_website:
            score += 5
        if lead.industry:
            score += 5
        
        # Additional data (20 points)
        if lead.title:
            score += 5
        if lead.revenue_estimate:
            score += 5
        if lead.employee_count:
            score += 5
        if lead.city and lead.state:
            score += 5
        
        return min(score, 100)
