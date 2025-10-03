"""
Data models for AcquireIQ
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    """Email verification status"""
    VALID = "valid"
    INVALID = "invalid"
    ACCEPT_ALL = "accept_all"
    WEBMAIL = "webmail"
    DISPOSABLE = "disposable"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


class ConfidenceLevel(str, Enum):
    """Confidence level for data quality"""
    HIGH = "high"      # 90-100%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    VERY_LOW = "very_low"  # <50%


class EmailVerificationResult(BaseModel):
    """Email verification result from Hunter.io"""
    email: str
    status: EmailStatus
    score: int = Field(ge=0, le=100, description="Confidence score 0-100")
    confidence_level: ConfidenceLevel
    regexp: bool = Field(description="Email format is valid")
    gibberish: bool = Field(description="Email looks fake")
    disposable: bool = Field(description="Disposable email service")
    webmail: bool = Field(description="Webmail provider like Gmail")
    mx_records: bool = Field(description="Domain has MX records")
    smtp_server: bool = Field(description="SMTP server exists")
    smtp_check: bool = Field(description="Mailbox exists")
    accept_all: bool = Field(description="Server accepts all emails")
    block: bool = Field(description="Email is blocked")
    sources: List[Dict] = Field(default_factory=list, description="Where email was found")
    
    @validator('confidence_level', pre=True, always=True)
    def determine_confidence(cls, v, values):
        """Determine confidence level from score"""
        if 'score' in values:
            score = values['score']
            if score >= 90:
                return ConfidenceLevel.HIGH
            elif score >= 70:
                return ConfidenceLevel.MEDIUM
            elif score >= 50:
                return ConfidenceLevel.LOW
            else:
                return ConfidenceLevel.VERY_LOW
        return v


class PhoneNumber(BaseModel):
    """Phone number information"""
    number: str
    country_code: Optional[str] = None
    is_valid: bool = False
    type: Optional[str] = None  # mobile, fixed_line, etc.


class Lead(BaseModel):
    """Enhanced lead with enriched contact information"""
    
    # Basic Info
    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    title: Optional[str] = None
    
    # Company Info
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_estimate: Optional[float] = None
    founded_year: Optional[int] = None
    
    # Contact Info (Enhanced)
    email: Optional[str] = None
    email_status: Optional[EmailStatus] = None
    email_confidence: Optional[int] = None
    email_sources: List[Dict] = Field(default_factory=list)
    
    phone: Optional[str] = None
    phone_valid: bool = False
    
    # Social Profiles
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    
    # Location
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    # Quality Metrics
    data_quality_score: int = Field(default=0, ge=0, le=100)
    is_enriched: bool = False
    enrichment_date: Optional[datetime] = None
    
    # Sources
    data_source: Optional[str] = None
    verification_sources: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class EnrichmentReport(BaseModel):
    """Report of enrichment results"""
    total_leads: int
    enriched_count: int
    verified_emails: int
    invalid_emails: int
    high_confidence: int
    medium_confidence: int
    low_confidence: int
    avg_quality_score: float
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
