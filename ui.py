"""
AcquireIQ - Streamlit Dashboard
Enterprise Contact Enrichment for M&A Searchers
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from config import settings
from models import Lead, EmailStatus, ConfidenceLevel, EnrichmentReport
from enrichment import ContactEnricher
from scraper import LeadScraper
from validator import EmailValidator
from crm_integration import CRMIntegration


# Page configuration
st.set_page_config(
    page_title="AcquireIQ - Contact Enrichment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .status-valid {
        color: #28a745;
        font-weight: bold;
    }
    .status-invalid {
        color: #dc3545;
        font-weight: bold;
    }
    .status-medium {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'leads' not in st.session_state:
        st.session_state.leads = []
    if 'enriched_leads' not in st.session_state:
        st.session_state.enriched_leads = []
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'show_tutorial' not in st.session_state:
        st.session_state.show_tutorial = True


def render_header():
    """Render application header"""
    st.markdown('<h1 class="main-header">🎯 AcquireIQ</h1>', unsafe_allow_html=True)
    st.markdown("**Enterprise Contact Enrichment for M&A Searchers**")
    st.markdown("---")


def render_tutorial():
    """Render onboarding tutorial"""
    if st.session_state.show_tutorial:
        with st.expander("👋 First Time Here? Quick Tutorial", expanded=True):
            st.markdown("""
            ### Welcome to AcquireIQ! 🎯
            
            **Get started in 3 easy steps:**
            
            1. **Configure API Key** (Sidebar) - Your Hunter.io key is pre-filled
            2. **Choose Data Source** (Sidebar):
               - 🎲 Sample Data - Try it instantly with 10 demo leads
               - 🔍 Domain Search - Find contacts at any company (e.g., stripe.com)
               - 📦 Bulk Domain Search - Process multiple companies at once
               - 📄 Upload CSV - Enrich your existing lead lists
            3. **Click "Start Enrichment"** - Watch your leads get verified and scored!
            
            **What You'll Get:**
            - ✅ Email verification (80%+ accuracy)
            - 📊 Quality scores (0-100 for prioritization)
            - 🎯 Confidence ratings (High/Medium/Low)
            - 📈 Visual analytics
            - 📥 CRM-ready exports (Salesforce, HubSpot, Pipedrive)
            
            **Pro Tips:**
            - Enable "Remove Duplicates" to clean your data automatically
            - Use search/filter to find specific leads quickly
            - Try bulk domain search to process 3+ companies at once
            """)
            
            if st.button("Got it! Don't show again"):
                st.session_state.show_tutorial = False
                st.rerun()


def render_sidebar():
    """Render sidebar with configuration"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Hunter.io API Key input
        api_key = st.text_input(
            "Hunter.io API Key",
            value="00d17a35bfef2423200768ddecf7d27fc9dc9ca6",
            type="password",
            help="Get free 50 credits/month at https://hunter.io"
        )
        
        if api_key:
            settings.hunter_api_key = api_key
            st.success("✅ Hunter.io API Key configured")
        else:
            st.warning("⚠️ No API key. Using local validation only.")
        
        st.markdown("---")
        
        # Deduplication toggle
        deduplicate = st.checkbox(
            "🔄 Remove Duplicates", 
            value=True, 
            help="Automatically remove duplicate emails, keeping highest quality lead"
        )
        
        st.markdown("---")
        
        # Lead generation options
        st.header("📊 Data Source")
        
        data_source = st.radio(
            "Choose data source:",
            ["Sample Data (Demo)", "Domain Search (Hunter.io)", "Bulk Domain Search", "Upload CSV"],
            help="Select your lead source"
        )
        
        if data_source == "Sample Data (Demo)":
            num_leads = st.slider("Number of sample leads", 5, 20, 10)
            return {"source": "sample", "count": num_leads, "api_key": api_key, "deduplicate": deduplicate}
        
        elif data_source == "Domain Search (Hunter.io)":
            domain = st.text_input("Enter company domain", value="stripe.com", placeholder="example.com")
            max_results = st.slider("Max Results", 5, 50, 20)
            return {"source": "domain_search", "domain": domain, "max_results": max_results, "api_key": api_key, "deduplicate": deduplicate}
        
        elif data_source == "Bulk Domain Search":
            domains_text = st.text_area(
                "Enter domains (one per line)",
                value="stripe.com\nairbnb.com\nslack.com",
                height=150,
                help="Enter multiple domains to search in bulk"
            )
            max_per_domain = st.slider("Max results per domain", 5, 20, 10)
            domains_list = [d.strip() for d in domains_text.split("\n") if d.strip()]
            return {
                "source": "bulk_domain", 
                "domains": domains_list, 
                "max_per_domain": max_per_domain, 
                "api_key": api_key, 
                "deduplicate": deduplicate
            }
        
        elif data_source == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload CSV file",
                type=['csv'],
                help="Upload CSV with columns: first_name, last_name, email, company_name, title"
            )
            if uploaded_file:
                return {"source": "upload", "file": uploaded_file, "api_key": api_key, "deduplicate": deduplicate}
        
        return {"source": "none", "api_key": api_key, "deduplicate": deduplicate}


def render_metrics(enriched_leads: list):
    """Render key metrics"""
    if not enriched_leads:
        return
    
    # Calculate metrics
    total = len(enriched_leads)
    verified = sum(1 for lead in enriched_leads if lead.email_status == EmailStatus.VALID)
    high_conf = sum(1 for lead in enriched_leads if lead.email_confidence and lead.email_confidence >= 90)
    avg_quality = sum(lead.data_quality_score for lead in enriched_leads) / total if total > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", total)
    
    with col2:
        st.metric("Verified Emails", verified, delta=f"{verified/total*100:.1f}%" if total > 0 else "0%")
    
    with col3:
        st.metric("High Confidence", high_conf, delta=f"{high_conf/total*100:.1f}%" if total > 0 else "0%")
    
    with col4:
        st.metric("Avg Quality Score", f"{avg_quality:.1f}/100")


def render_charts(enriched_leads: list):
    """Render visualization charts"""
    if not enriched_leads:
        return
    
    # Prepare data
    df = pd.DataFrame([lead.dict() for lead in enriched_leads])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Email Status Distribution
        st.subheader("📊 Email Verification Status")
        status_counts = df['email_status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Email Status Distribution",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Data Quality Distribution
        st.subheader("📈 Data Quality Scores")
        fig_quality = px.histogram(
            df,
            x='data_quality_score',
            nbins=20,
            title="Data Quality Score Distribution",
            labels={'data_quality_score': 'Quality Score', 'count': 'Number of Leads'},
            color_discrete_sequence=['#667eea']
        )
        st.plotly_chart(fig_quality, use_container_width=True)


def render_leads_table(enriched_leads: list):
    """Render enriched leads table with filtering and CRM export"""
    if not enriched_leads:
        st.info("No leads to display. Generate or upload leads to get started.")
        return
    
    st.subheader("📋 Enriched Leads")
    
    # Search and Filter Row
    col_search, col_filter, col_quality = st.columns([2, 1, 1])
    
    with col_search:
        search_term = st.text_input("🔍 Search", placeholder="Search by name, company, email...", key="search")
    
    with col_filter:
        status_filter = st.selectbox(
            "Filter by Status", 
            ["All", "VALID", "INVALID", "UNKNOWN", "WEBMAIL", "DISPOSABLE"],
            key="status_filter"
        )
    
    with col_quality:
        quality_filter = st.selectbox(
            "Filter by Quality",
            ["All", "Excellent (80-100)", "Good (60-79)", "Fair (0-59)"],
            key="quality_filter"
        )
    
    # Apply filters
    filtered_leads = enriched_leads
    
    if search_term:
        search_lower = search_term.lower()
        filtered_leads = [
            lead for lead in filtered_leads 
            if search_lower in (lead.full_name or "").lower() 
            or search_lower in (lead.company_name or "").lower()
            or search_lower in (lead.email or "").lower()
        ]
    
    # FIXED: Handle EmailStatus enum properly
    if status_filter != "All":
        filtered_leads = [
            lead for lead in filtered_leads 
            if (hasattr(lead.email_status, 'value') and lead.email_status.value == status_filter) or
               (isinstance(lead.email_status, str) and lead.email_status.upper() == status_filter)
        ]
    
    if quality_filter != "All":
        if quality_filter == "Excellent (80-100)":
            filtered_leads = [lead for lead in filtered_leads if lead.data_quality_score >= 80]
        elif quality_filter == "Good (60-79)":
            filtered_leads = [lead for lead in filtered_leads if 60 <= lead.data_quality_score < 80]
        elif quality_filter == "Fair (0-59)":
            filtered_leads = [lead for lead in filtered_leads if lead.data_quality_score < 60]
    
    st.write(f"Showing **{len(filtered_leads)}** of **{len(enriched_leads)}** leads")
    
    # Table display
    display_data = []
    for lead in filtered_leads:
        # FIXED: Display only the enum value, not the full enum name
        email_status_display = lead.email_status.value if hasattr(lead.email_status, 'value') else str(lead.email_status)
        
        display_data.append({
            "Name": lead.full_name or "",
            "Title": lead.title or "",
            "Company": lead.company_name or "",
            "Email": lead.email or "",
            "Status": email_status_display,  # Fixed display
            "Confidence": f"{lead.email_confidence}%" if lead.email_confidence else "N/A",
            "Quality Score": f"{lead.data_quality_score}/100",
            "Location": f"{lead.city}, {lead.state}" if lead.city and lead.state else "N/A"
        })
    
    df_display = pd.DataFrame(display_data)
    
    # Apply styling
    def color_status(val):
        val_str = str(val).upper()
        if "VALID" in val_str and "INVALID" not in val_str:
            return 'color: green'
        elif "INVALID" in val_str:
            return 'color: red'
        else:
            return 'color: orange'
    
    if len(df_display) > 0 and 'Status' in df_display.columns:
        styled_df = df_display.style.apply(lambda col: [color_status(val) for val in col], subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.dataframe(df_display, use_container_width=True, height=400)
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export Options")
    
    export_col1, export_col2, export_col3, export_col4 = st.columns(4)
    
    crm = CRMIntegration()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with export_col1:
        generic_csv = crm.export_generic_crm_format(filtered_leads).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Generic CSV",
            data=generic_csv,
            file_name=f"acquireiq_leads_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col2:
        sf_csv = crm.export_salesforce_format(filtered_leads).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="☁️ Salesforce",
            data=sf_csv,
            file_name=f"salesforce_import_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col3:
        hs_csv = crm.export_hubspot_format(filtered_leads).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="🟠 HubSpot",
            data=hs_csv,
            file_name=f"hubspot_import_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col4:
        pd_csv = crm.export_pipedrive_format(filtered_leads).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="🟢 Pipedrive",
            data=pd_csv,
            file_name=f"pipedrive_import_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )


def main():
    """Main application logic"""
    init_session_state()
    render_header()
    render_tutorial()
    
    # Sidebar configuration
    config = render_sidebar()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🚀 Enrichment", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        st.header("Contact Enrichment Pipeline")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **Enhancement Features:**
            - ✅ **Email Verification**: Verify email deliverability and validity
            - ✅ **Contact Finding**: Find missing email addresses
            - ✅ **Quality Scoring**: Rate data quality 0-100
            - ✅ **Confidence Levels**: High/Medium/Low confidence ratings
            - ✅ **Multi-source Validation**: Cross-reference multiple data sources
            - ✅ **Bulk Processing**: Search multiple domains simultaneously
            - ✅ **Smart Deduplication**: Remove duplicate contacts automatically
            - ✅ **CRM Integration**: Export to Salesforce, HubSpot, Pipedrive
            """)
        
        with col2:
            if st.button("🚀 Start Enrichment", type="primary", use_container_width=True):
                with st.spinner("Fetching leads and enriching contacts... This may take a moment."):
                    scraper = LeadScraper()
                    leads = []
                    source = config.get("source")
                    
                    # Sample Data
                    if source == 'sample':
                        leads = scraper.generate_sample_leads(config['count'])
                        st.success(f"✅ Generated {len(leads)} sample leads")
                    
                    # Single Domain Search
                    elif source == 'domain_search':
                        domain = config.get("domain")
                        if not domain:
                            st.error("❌ Please enter a company domain")
                            return
                        if not config.get("api_key"):
                            st.error("❌ Hunter.io API Key is required for Domain Search")
                            return
                        try:
                            leads = scraper.scrape_hunter_domain(
                                domain, 
                                config.get('api_key') or "", 
                                config.get('max_results', 20)
                            )
                            st.success(f"✅ Retrieved {len(leads)} leads from {domain}")
                        except Exception as e:
                            st.error(f"❌ Failed to retrieve data: {str(e)}")
                            return
                    
                    # Bulk Domain Search
                    elif source == 'bulk_domain':
                        domains = config.get("domains", [])
                        if not domains:
                            st.error("❌ Please enter at least one domain")
                            return
                        if not config.get("api_key"):
                            st.error("❌ Hunter.io API Key is required for Bulk Domain Search")
                            return
                        try:
                            with st.spinner(f"Searching {len(domains)} domains..."):
                                leads = scraper.bulk_domain_search(
                                    domains, 
                                    config.get('api_key') or "", 
                                    config.get('max_per_domain', 10)
                                )
                            st.success(f"✅ Retrieved {len(leads)} total leads from {len(domains)} domains")
                        except Exception as e:
                            st.error(f"❌ Failed to retrieve data: {str(e)}")
                            return
                    
                    # CSV Upload
                    elif source == 'upload':
                        file = config.get("file")
                        if not file:
                            st.error("❌ Please upload a CSV file")
                            return
                        try:
                            leads = scraper.parse_csv_upload(file)
                            st.success(f"✅ Parsed {len(leads)} leads from CSV")
                        except Exception as e:
                            st.error(f"❌ Failed to parse CSV: {str(e)}")
                            return
                    
                    if not leads:
                        st.error("No leads retrieved.")
                        return
                    
                    # Deduplication
                    if config.get('deduplicate', True):
                        original_count = len(leads)
                        leads = scraper.deduplicate_leads(leads)
                        if len(leads) < original_count:
                            st.info(f"🔄 Removed {original_count - len(leads)} duplicate(s)")
                    
                    st.session_state.leads = leads
                    
                    # Enrichment
                    enricher = ContactEnricher(api_key=config['api_key'])
                    enriched = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, lead in enumerate(leads):
                        status_text.text(f"Enriching {i+1}/{len(leads)}: {lead.company_name or 'Unknown'}...")
                        enriched_lead = enricher.enrich_lead(lead)
                        enriched.append(enriched_lead)
                        progress_bar.progress((i + 1) / len(leads))
                        time.sleep(0.05)  # Faster processing
                    
                    status_text.empty()
                    st.session_state.enriched_leads = enriched
                    st.success(f"✅ Successfully enriched {len(enriched)} leads!")
                    st.balloons()
        
        st.markdown("---")
        
        # Display results
        if st.session_state.enriched_leads:
            render_metrics(st.session_state.enriched_leads)
            st.markdown("---")
            render_leads_table(st.session_state.enriched_leads)
    
    with tab2:
        st.header("Enrichment Analytics")
        
        if st.session_state.enriched_leads:
            render_charts(st.session_state.enriched_leads)
            
            # Detailed statistics
            st.subheader("📈 Detailed Statistics")
            
            enriched = st.session_state.enriched_leads
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Email Status Breakdown**")
                for status in EmailStatus:
                    count = sum(1 for lead in enriched if lead.email_status == status)
                    if count > 0:
                        percentage = (count / len(enriched)) * 100
                        st.write(f"- {status.value}: {count} ({percentage:.1f}%)")
            
            with col2:
                st.markdown("**Confidence Levels**")
                high = sum(1 for lead in enriched if lead.email_confidence and lead.email_confidence >= 90)
                medium = sum(1 for lead in enriched if lead.email_confidence and 70 <= lead.email_confidence < 90)
                low = sum(1 for lead in enriched if lead.email_confidence and lead.email_confidence < 70)
                total_with_conf = high + medium + low
                if total_with_conf > 0:
                    st.write(f"- High (90-100%): {high} ({high/total_with_conf*100:.1f}%)")
                    st.write(f"- Medium (70-89%): {medium} ({medium/total_with_conf*100:.1f}%)")
                    st.write(f"- Low (<70%): {low} ({low/total_with_conf*100:.1f}%)")
            
            with col3:
                st.markdown("**Quality Scores**")
                excellent = sum(1 for lead in enriched if lead.data_quality_score >= 80)
                good = sum(1 for lead in enriched if 60 <= lead.data_quality_score < 80)
                fair = sum(1 for lead in enriched if lead.data_quality_score < 60)
                st.write(f"- Excellent (80-100): {excellent} ({excellent/len(enriched)*100:.1f}%)")
                st.write(f"- Good (60-79): {good} ({good/len(enriched)*100:.1f}%)")
                st.write(f"- Fair (<60): {fair} ({fair/len(enriched)*100:.1f}%)")
        
        else:
            st.info("Run enrichment first to see analytics")
    
    with tab3:
        st.header("About AcquireIQ")
        
        st.markdown("""
        ### 🎯 What is AcquireIQ?
        
        AcquireIQ is an **enterprise-grade contact enrichment tool** specifically designed for 
        acquisition entrepreneurs and M&A searchers. It enhances the basic contact information 
        from lead generation tools like SaaSQuatch Leads.
        
        ### ✨ Key Enhancements
        
        **1. Email Verification & Validation**
        - Verify email deliverability using Hunter.io API
        - Validate email format, MX records, SMTP servers
        - Detect disposable and webmail addresses
        
        **2. Contact Finding**
        - Find missing email addresses using name + company domain
        - Leverage Hunter.io's 200M+ email database
        
        **3. Data Quality Scoring**
        - Calculate comprehensive quality scores (0-100)
        - Rate confidence levels: High/Medium/Low
        
        **4. Multi-source Validation**
        - Cross-reference multiple data sources
        - Show where emails were found publicly
        
        **5. Advanced Features**
        - Bulk domain processing
        - Smart deduplication
        - CSV upload and parsing
        - Search and filtering
        - CRM-ready exports (Salesforce, HubSpot, Pipedrive)
        
        ### 🔧 Technology Stack
        
        - **Backend**: Python, Pydantic, Pandas
        - **Enrichment**: Hunter.io API (50 free credits/month)
        - **Validation**: email-validator, dnspython, regex
        - **Frontend**: Streamlit
        - **Visualization**: Plotly
        
        ### 📊 vs. SaaSQuatch Leads
        
        | Feature | SaaSQuatch | AcquireIQ |
        |---------|------------|-----------|
        | Email Verification | ❌ | ✅ 80%+ accuracy |
        | Quality Scoring | ❌ | ✅ 0-100 algorithm |
        | Bulk Processing | ❌ | ✅ Multiple domains |
        | Deduplication | ❌ | ✅ Smart matching |
        | CRM Integration | ❌ | ✅ 4 formats |
        | Analytics Dashboard | ❌ | ✅ Full insights |
        
        ---
        
        **⚡ Built in 5 hours** | **🎯 Quality-First Approach** | **🚀 Production-Ready**
        """)


if __name__ == "__main__":
    main()
