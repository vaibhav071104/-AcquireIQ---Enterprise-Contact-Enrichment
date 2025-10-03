"""
Lead scraping functionality with advanced features
"""
import requests
from typing import List, Dict
from models import Lead
import random
import pandas as pd
import io


class LeadScraper:
    """
    Enhanced lead scraping functionality
    """
    
    @staticmethod
    def generate_sample_leads(count: int = 20) -> List[Lead]:
        """Generate sample leads for testing"""
        sample_companies = [
            {"name": "TechFlow Solutions", "domain": "techflow.com", "industry": "SaaS", "employees": 45, "revenue": 5000000},
            {"name": "DataSync Inc", "domain": "datasync.io", "industry": "Data Analytics", "employees": 32, "revenue": 3500000},
            {"name": "CloudBridge Systems", "domain": "cloudbridge.com", "industry": "Cloud Services", "employees": 78, "revenue": 12000000},
            {"name": "SecureNet Corp", "domain": "securenet.com", "industry": "Cybersecurity", "employees": 55, "revenue": 8000000},
            {"name": "FinTrack Software", "domain": "fintrack.io", "industry": "FinTech", "employees": 28, "revenue": 2800000},
            {"name": "HealthHub Technologies", "domain": "healthhub.com", "industry": "HealthTech", "employees": 41, "revenue": 4500000},
            {"name": "EduLearn Platform", "domain": "edulearn.com", "industry": "EdTech", "employees": 35, "revenue": 3200000},
            {"name": "LogiChain Solutions", "domain": "logichain.com", "industry": "Logistics", "employees": 62, "revenue": 9000000},
            {"name": "MarketPulse Analytics", "domain": "marketpulse.io", "industry": "Marketing", "employees": 38, "revenue": 4000000},
            {"name": "GreenEnergy Systems", "domain": "greenenergy.com", "industry": "CleanTech", "employees": 52, "revenue": 7500000},
        ]
        
        first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jennifer", "Robert", "Lisa", "James", "Mary"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        titles = ["CEO", "Founder", "President", "Managing Director", "VP Operations", "Chief Executive"]
        cities = ["Austin", "Denver", "Seattle", "Portland", "Nashville", "Charlotte", "San Diego", "Boston"]
        states = ["TX", "CO", "WA", "OR", "TN", "NC", "CA", "MA"]
        
        leads = []
        
        for i in range(min(count, len(sample_companies))):
            company = sample_companies[i]
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            lead = Lead(
                id=f"lead_{i+1}",
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                title=random.choice(titles),
                company_name=company["name"],
                company_domain=company["domain"],
                company_website=f"https://{company['domain']}",
                industry=company["industry"],
                employee_count=company["employees"],
                revenue_estimate=company["revenue"],
                email=f"{first_name.lower()}.{last_name.lower()}@{company['domain']}",
                city=random.choice(cities),
                state=random.choice(states),
                country="USA",
                data_source="Sample Data"
            )
            leads.append(lead)
        
        return leads


    @staticmethod
    def scrape_hunter_domain(domain: str, api_key: str, max_results: int = 20) -> List[Lead]:
        """
        Scrape leads from a company domain using Hunter.io Domain Search API
        """
        if not api_key:
            raise ValueError("Hunter.io API key is required for domain search.")
        
        url = "https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "limit": max_results,
            "api_key": api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            leads = []
            company_data = data.get("data", {})
            
            for email_data in company_data.get("emails", []):
                lead = Lead(
                    first_name=email_data.get("first_name"),
                    last_name=email_data.get("last_name"),
                    full_name=f'{email_data.get("first_name", "")} {email_data.get("last_name", "")}'.strip(),
                    title=email_data.get("position"),
                    company_name=company_data.get("organization"),
                    company_domain=domain,
                    company_website=f"https://{domain}",
                    email=email_data.get("value"),
                    data_source="Hunter.io Domain Search"
                )
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            print(f"[Hunter Domain Search] Error: {e}")
            raise


    @staticmethod
    def bulk_domain_search(domains: List[str], api_key: str, max_results_per_domain: int = 20) -> List[Lead]:
        """
        Search multiple domains in bulk
        """
        all_leads = []
        
        for domain in domains:
            try:
                leads = LeadScraper.scrape_hunter_domain(domain.strip(), api_key, max_results_per_domain)
                all_leads.extend(leads)
                print(f"✅ Retrieved {len(leads)} leads from {domain}")
            except Exception as e:
                print(f"❌ Error with domain {domain}: {e}")
                continue
        
        return all_leads


    @staticmethod
    def parse_csv_upload(uploaded_file) -> List[Lead]:
        """
        Parse uploaded CSV file and convert to Lead objects
        Expected columns: first_name, last_name, email, company_name, company_domain, title
        """
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Normalize column names (lowercase, strip spaces)
            df.columns = df.columns.str.lower().str.strip()
            
            leads = []
            for idx, row in df.iterrows():
                lead = Lead(
                    id=f"csv_lead_{idx+1}",
                    first_name=row.get('first_name', row.get('firstname', '')),
                    last_name=row.get('last_name', row.get('lastname', '')),
                    full_name=row.get('full_name', f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()),
                    email=row.get('email', ''),
                    title=row.get('title', row.get('position', '')),
                    company_name=row.get('company_name', row.get('company', '')),
                    company_domain=row.get('company_domain', row.get('domain', '')),
                    company_website=row.get('company_website', row.get('website', '')),
                    industry=row.get('industry', ''),
                    phone=row.get('phone', ''),
                    city=row.get('city', ''),
                    state=row.get('state', ''),
                    country=row.get('country', ''),
                    data_source="CSV Upload"
                )
                leads.append(lead)
            
            print(f"✅ Parsed {len(leads)} leads from CSV")
            return leads
            
        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")


    @staticmethod
    def deduplicate_leads(leads: List[Lead]) -> List[Lead]:
        """
        Remove duplicate leads based on email address
        Keeps the lead with highest quality score
        """
        seen_emails = {}
        
        for lead in leads:
            if not lead.email:
                continue
                
            email_lower = lead.email.lower()
            
            if email_lower not in seen_emails:
                seen_emails[email_lower] = lead
            else:
                # Keep lead with higher quality score
                existing_lead = seen_emails[email_lower]
                if lead.data_quality_score > existing_lead.data_quality_score:
                    seen_emails[email_lower] = lead
        
        deduplicated = list(seen_emails.values())
        duplicates_removed = len(leads) - len(deduplicated)
        
        print(f"🔄 Deduplication: {len(leads)} → {len(deduplicated)} leads ({duplicates_removed} duplicates removed)")
        
        return deduplicated
