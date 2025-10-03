"""
CRM Integration and Export Utilities
"""
import pandas as pd
from typing import List
from models import Lead
from datetime import datetime


class CRMIntegration:
    """
    Export enriched leads in CRM-ready formats
    """
    
    @staticmethod
    def export_salesforce_format(leads: List[Lead]) -> pd.DataFrame:
        """
        Export in Salesforce import format
        """
        data = []
        for lead in leads:
            data.append({
                "First Name": lead.first_name or "",
                "Last Name": lead.last_name or "",
                "Email": lead.email or "",
                "Title": lead.title or "",
                "Company": lead.company_name or "",
                "Website": lead.company_website or "",
                "Industry": lead.industry or "",
                "Phone": lead.phone or "",
                "Street": "",
                "City": lead.city or "",
                "State": lead.state or "",
                "Postal Code": "",
                "Country": lead.country or "",
                "Lead Source": lead.data_source or "AcquireIQ",
                "Lead Status": "New",
                "Rating": "Hot" if lead.data_quality_score >= 80 else "Warm" if lead.data_quality_score >= 60 else "Cold",
                "Email Opt Out": "",
                "Description": f"Quality Score: {lead.data_quality_score}/100, Email Confidence: {lead.email_confidence}%",
            })
        
        return pd.DataFrame(data)
    
    
    @staticmethod
    def export_hubspot_format(leads: List[Lead]) -> pd.DataFrame:
        """
        Export in HubSpot import format
        """
        data = []
        for lead in leads:
            data.append({
                "First Name": lead.first_name or "",
                "Last Name": lead.last_name or "",
                "Email": lead.email or "",
                "Job Title": lead.title or "",
                "Company Name": lead.company_name or "",
                "Company Domain Name": lead.company_domain or "",
                "Website URL": lead.company_website or "",
                "Industry": lead.industry or "",
                "Phone Number": lead.phone or "",
                "City": lead.city or "",
                "State/Region": lead.state or "",
                "Country/Region": lead.country or "",
                "Lead Status": "NEW",
                "Lifecycle Stage": "lead",
                "Lead Source": lead.data_source or "AcquireIQ",
                "AcquireIQ Quality Score": lead.data_quality_score,
                "AcquireIQ Email Confidence": lead.email_confidence or 0,
                "AcquireIQ Email Status": lead.email_status or "",
            })
        
        return pd.DataFrame(data)
    
    
    @staticmethod
    def export_pipedrive_format(leads: List[Lead]) -> pd.DataFrame:
        """
        Export in Pipedrive import format
        """
        data = []
        for lead in leads:
            data.append({
                "Person": lead.full_name or f"{lead.first_name} {lead.last_name}",
                "Email": lead.email or "",
                "Phone": lead.phone or "",
                "Organization": lead.company_name or "",
                "Job Title": lead.title or "",
                "Website": lead.company_website or "",
                "Address": f"{lead.city}, {lead.state}, {lead.country}".strip(", "),
                "Owner": "",
                "Visible To": "3",  # Everyone
                "Label": "Hot" if lead.data_quality_score >= 80 else "Warm" if lead.data_quality_score >= 60 else "Cold",
                "AcquireIQ Quality Score": lead.data_quality_score,
                "AcquireIQ Email Confidence": lead.email_confidence or 0,
            })
        
        return pd.DataFrame(data)
    
    
    @staticmethod
    def export_generic_crm_format(leads: List[Lead]) -> pd.DataFrame:
        """
        Generic CRM format with all available fields
        """
        data = []
        for lead in leads:
            data.append({
                "ID": lead.id or "",
                "First Name": lead.first_name or "",
                "Last Name": lead.last_name or "",
                "Full Name": lead.full_name or "",
                "Email": lead.email or "",
                "Email Status": lead.email_status or "",
                "Email Confidence": f"{lead.email_confidence}%" if lead.email_confidence else "",
                "Title": lead.title or "",
                "Company": lead.company_name or "",
                "Domain": lead.company_domain or "",
                "Website": lead.company_website or "",
                "Industry": lead.industry or "",
                "Employees": lead.employee_count or "",
                "Revenue": lead.revenue_estimate or "",
                "Phone": lead.phone or "",
                "LinkedIn": lead.linkedin_url or "",
                "City": lead.city or "",
                "State": lead.state or "",
                "Country": lead.country or "",
                "Quality Score": f"{lead.data_quality_score}/100",
                "Data Source": lead.data_source or "",
                "Enriched": "Yes" if lead.is_enriched else "No",
                "Export Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        
        return pd.DataFrame(data)
