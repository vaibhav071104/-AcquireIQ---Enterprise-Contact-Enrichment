"""
Email validation utilities
"""
import re
import dns.resolver
from email_validator import validate_email as validate_email_format, EmailNotValidError
from typing import Dict, Tuple, List


class EmailValidator:
    """Advanced email validation"""
    
    # Comprehensive email regex pattern
    EMAIL_REGEX = r'^(?!\.)[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    # Disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'throwaway.email', 'maildrop.cc', 'mailinator.com',
        'trashmail.com', 'yopmail.com', 'temp-mail.org'
    }
    
    # Common webmail providers
    WEBMAIL_PROVIDERS = {
        'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
        'icloud.com', 'aol.com', 'protonmail.com', 'mail.com'
    }
    
    @classmethod
    def validate_format(cls, email: str) -> Tuple[bool, str]:
        """
        Validate email format using regex
        Returns: (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is empty or invalid type"
        
        email = email.strip().lower()
        
        # Basic regex check
        if not re.match(cls.EMAIL_REGEX, email):
            return False, "Invalid email format"
        
        # Check for common mistakes
        if email.count('@') != 1:
            return False, "Email must contain exactly one @ symbol"
        
        local, domain = email.split('@')
        
        # Local part checks
        if len(local) == 0 or len(local) > 64:
            return False, "Local part length must be 1-64 characters"
        
        if local.startswith('.') or local.endswith('.'):
            return False, "Local part cannot start or end with a dot"
        
        if '..' in local:
            return False, "Local part cannot contain consecutive dots"
        
        # Domain checks
        if len(domain) == 0 or len(domain) > 255:
            return False, "Domain length must be 1-255 characters"
        
        if not re.match(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$', domain):
            return False, "Invalid domain format"
        
        return True, "Valid format"
    
    @classmethod
    def validate_with_library(cls, email: str) -> Dict:
        """
        Validate using email-validator library
        Returns detailed validation info
        """
        try:
            validation = validate_email_format(email, check_deliverability=False)
            return {
                'valid': True,
                'normalized_email': validation.normalized,
                'local_part': validation.local_part,
                'domain': validation.domain,
                'error': None
            }
        except EmailNotValidError as e:
            return {
                'valid': False,
                'normalized_email': None,
                'local_part': None,
                'domain': None,
                'error': str(e)
            }
    
    @classmethod
    def check_mx_records(cls, domain: str) -> Tuple[bool, List[str]]:
        """
        Check if domain has valid MX records
        Returns: (has_mx, mx_records)
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(r.exchange) for r in mx_records]
            return True, mx_list
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return False, []
        except Exception as e:
            return False, []
    
    @classmethod
    def is_disposable(cls, email: str) -> bool:
        """Check if email is from disposable provider"""
        try:
            domain = email.split('@')[1].lower()
            return domain in cls.DISPOSABLE_DOMAINS
        except:
            return False
    
    @classmethod
    def is_webmail(cls, email: str) -> bool:
        """Check if email is from webmail provider"""
        try:
            domain = email.split('@')[1].lower()
            return domain in cls.WEBMAIL_PROVIDERS
        except:
            return False
    
    @classmethod
    def detect_gibberish(cls, email: str) -> bool:
        """
        Detect if email looks like gibberish
        Simple heuristic: check for excessive consonants
        """
        try:
            local_part = email.split('@')[0].lower()
            
            # Remove numbers and special chars
            letters_only = re.sub(r'[^a-z]', '', local_part)
            
            if len(letters_only) < 3:
                return False
            
            # Count consonants
            vowels = set('aeiou')
            consonants = sum(1 for c in letters_only if c not in vowels)
            
            # If more than 70% consonants, likely gibberish
            consonant_ratio = consonants / len(letters_only)
            
            return consonant_ratio > 0.7
        except:
            return False
    
    @classmethod
    def comprehensive_validation(cls, email: str) -> Dict:
        """
        Run all validation checks
        Returns comprehensive validation report
        """
        result = {
            'email': email,
            'is_valid': False,
            'format_valid': False,
            'mx_records': False,
            'is_disposable': False,
            'is_webmail': False,
            'is_gibberish': False,
            'domain': None,
            'errors': []
        }
        
        # Format validation
        format_valid, error_msg = cls.validate_format(email)
        result['format_valid'] = format_valid
        
        if not format_valid:
            result['errors'].append(error_msg)
            return result
        
        # Extract domain
        try:
            result['domain'] = email.split('@')[1].lower()
        except:
            result['errors'].append("Cannot extract domain")
            return result
        
        # MX records check
        has_mx, mx_list = cls.check_mx_records(result['domain'])
        result['mx_records'] = has_mx
        if not has_mx:
            result['errors'].append("No MX records found")
        
        # Disposable check
        result['is_disposable'] = cls.is_disposable(email)
        if result['is_disposable']:
            result['errors'].append("Disposable email detected")
        
        # Webmail check
        result['is_webmail'] = cls.is_webmail(email)
        
        # Gibberish check
        result['is_gibberish'] = cls.detect_gibberish(email)
        if result['is_gibberish']:
            result['errors'].append("Email appears to be gibberish")
        
        # Overall validity
        result['is_valid'] = (
            format_valid and 
            has_mx and 
            not result['is_disposable'] and 
            not result['is_gibberish']
        )
        
        return result
