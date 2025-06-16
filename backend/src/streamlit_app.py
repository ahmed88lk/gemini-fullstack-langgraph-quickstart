import streamlit as st
import json
import os
from typing import Dict, List, Any, Optional
import time
from agent import graph
from dotenv import load_dotenv

# Load environment variables
load_dotenv("src/agent/.env")

# Page configuration
st.set_page_config(
    page_title="Deep Deal Research",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #121212;
        color: #fff;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stTextInput > div > div > input, .stSelectbox > div > div > input {
        background-color: #2b2b2b;
        color: white;
    }
    .stSlider > div > div > div > div {
        background-color: #4285F4;
    }
    .stButton > button {
        background-color: #4285F4;
        color: white;
    }
    .deal-card {
        border: 1px solid #555555;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #1e1e1e;
    }
    .report-section {
        border-left: 2px solid #4285F4;
        padding-left: 20px;
        margin: 20px 0;
    }
    .source-link {
        color: #4285F4;
        text-decoration: underline;
    }
    .source-item {
        margin-bottom: 10px;
        padding-left: 20px;
        border-left: 2px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# Load deal data from JSON with improved path handling
@st.cache_data
def load_deal_data():
    try:
        # Try multiple possible locations for the JSON file
        possible_paths = [
            "src/scraped_companies_final.json",  # When run from backend directory
            "../src/scraped_companies_final.json",  # When run from src directory
            "backend/src/scraped_companies_final.json",  # When run from project root
            os.path.join(os.path.dirname(__file__), "scraped_companies_final.json")  # Same directory as script
        ]
        
        # Try to find the file
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        
        # If we reach here, try the absolute path as a last resort
        absolute_path = "/home/walker/Desktop/deepsearch_gemini/gemini-fullstack-langgraph-quickstart/backend/src/scraped_companies_final.json"
        with open(absolute_path, "r") as f:
            return json.load(f)
            
    except Exception as e:
        st.error(f"Error loading deal data: {e}")
        # Add debugging information
        st.error(f"Current directory: {os.getcwd()}")
        st.error("Please make sure the JSON file is at the correct location")
        
        # Empty portfolio as fallback
        return {"portfolios": []}

deal_data = load_deal_data()

# File upload fallback
if len(deal_data.get("portfolios", [])) == 0:
    st.warning("Could not load deal data automatically. Please upload the JSON file manually.")
    uploaded_file = st.file_uploader("Upload scraped_companies_final.json", type="json")
    if uploaded_file is not None:
        try:
            deal_data = json.load(uploaded_file)
            st.success("Deal data loaded successfully!")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")

# Title and description
st.title("🔍 Deep Deal Research")
st.markdown("Generate comprehensive research reports on deals, target companies, and investment strategies")

# Sidebar configuration
st.sidebar.title("Research Settings")

# Report type selection
report_type = st.sidebar.selectbox(
    "Report Type",
    [
        "Deal Summary Report",
        "Target Company Analysis",
        "PortCo Company Analysis",
        "Investment Thesis & Value Creation Strategy"
    ],
    index=0
)

# Model selection
model_option = st.sidebar.selectbox(
    "Select Gemini Model",
    ["gemini-2.5-flash-preview-04-17", "gemini-2.0-flash", "gemini-2.5-pro-preview-05-06"],
    index=0
)

# Research depth
research_effort = st.sidebar.radio(
    "Research Depth",
    ["Basic", "Standard", "Comprehensive"],
    index=1
)

# Source citation options
include_sources = st.sidebar.checkbox("Include Source Citations", value=True)
detailed_sources = st.sidebar.checkbox("Detailed Source Information", value=False)

# Convert research effort to parameters
if research_effort == "Basic":
    initial_queries = 2
    max_loops = 2
elif research_effort == "Comprehensive":
    initial_queries = 6
    max_loops = 10
else:  # Standard
    initial_queries = 4
    max_loops = 5

# Filter for investors/portfolios
investors = [p["Investor"] for p in deal_data.get("portfolios", [])]
selected_investor = st.sidebar.selectbox(
    "Select Investor Portfolio",
    investors if investors else ["No investors found"]
)

# Find the selected portfolio
selected_portfolio = next((p for p in deal_data.get("portfolios", []) if p["Investor"] == selected_investor), None)

# Select a deal
if selected_portfolio and "Deals" in selected_portfolio:
    deals = selected_portfolio["Deals"]
    deal_names = [deal["target_company_name"] for deal in deals]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Select Deal to Research")
        selected_deal_name = st.selectbox("Target Company", deal_names)
        selected_deal = next((deal for deal in deals if deal["target_company_name"] == selected_deal_name), None)
        
        if selected_deal:
            st.write(f"**Sectors:** {', '.join(selected_deal.get('target_sectors', ['Unknown']))}")
            st.write(f"**Location:** {selected_deal.get('target_location', 'Unknown')}")
            
            st.markdown("### Report Configuration")
            include_sections = {}
            
            if report_type == "Deal Summary Report":
                include_sections["deal_overview"] = st.checkbox("Deal Overview", value=True)
                include_sections["transaction_details"] = st.checkbox("Transaction Details", value=True)
                include_sections["market_analysis"] = st.checkbox("Market Analysis", value=True)
                include_sections["competitors"] = st.checkbox("Competitor Analysis", value=True)
            
            elif report_type == "Target Company Analysis":
                include_sections["company_profile"] = st.checkbox("Company Profile", value=True) 
                include_sections["products_services"] = st.checkbox("Products & Services", value=True)
                include_sections["management_team"] = st.checkbox("Management Team", value=True)
                include_sections["financial_performance"] = st.checkbox("Financial Performance", value=True)
                include_sections["competitors"] = st.checkbox("Competitor Analysis", value=True)
            
            elif report_type == "PortCo Company Analysis":
                include_sections["portco_profile"] = st.checkbox("PortCo Profile", value=True)
                include_sections["acquisition_strategy"] = st.checkbox("Acquisition Strategy", value=True)
                include_sections["integration_synergies"] = st.checkbox("Integration & Synergies", value=True)
                include_sections["competitors"] = st.checkbox("Competitor Analysis", value=True)
                
            elif report_type == "Investment Thesis & Value Creation Strategy":
                include_sections["investment_rationale"] = st.checkbox("Investment Rationale", value=True)
                include_sections["value_creation_plan"] = st.checkbox("Value Creation Plan", value=True)
                include_sections["exit_strategy"] = st.checkbox("Exit Strategy", value=True)
                include_sections["competitors"] = st.checkbox("Competitor Analysis", value=True)
                
            # Always include sources section if sources are enabled
            if include_sources:
                include_sections["sources"] = True
    
    with col2:
        st.subheader(f"Deal Details: {selected_deal_name}")
        
        if selected_deal:
            st.markdown(f"""
            **Company:** {selected_deal_name}  
            **Country:** {', '.join(selected_deal.get('target_country', ['Unknown'])) if isinstance(selected_deal.get('target_country'), list) else selected_deal.get('target_country', 'Unknown')}  
            **Business Description:** {selected_deal.get('target_business_description', 'No description available')}
            """)
            
            if "investment_date" in selected_deal and selected_deal["investment_date"]:
                st.write(f"**Investment Date:** {selected_deal['investment_date']}")
                
            if "investment_type" in selected_deal and selected_deal["investment_type"]:
                st.write(f"**Deal Type:** {selected_deal['investment_type']}")
                
            if "investment_amount" in selected_deal and selected_deal["investment_amount"]:
                st.write(f"**Deal Size:** {selected_deal['investment_amount']}")
                
            if "target_turnover" in selected_deal and selected_deal["target_turnover"]:
                st.write(f"**Turnover:** {selected_deal['target_turnover']}")
                
            if "target_employee_no" in selected_deal and selected_deal["target_employee_no"]:
                st.write(f"**Employees:** {selected_deal['target_employee_no']}")
                
            # Show any available URLs
            if selected_portfolio.get("Investor_portfolio_url"):
                st.write(f"**Investor Portfolio URL:** [{selected_portfolio['Investor']}]({selected_portfolio['Investor_portfolio_url']})")
                
            if selected_deal.get("deal_url"):
                st.write(f"**Deal URL:** [{selected_deal_name} Deal]({selected_deal['deal_url']})")

        # Generate report button
        if st.button("Generate Research Report"):
            if not any(include_sections.values()):
                st.error("Please select at least one section to include in the report")
            else:
                with st.spinner(f"Generating {report_type} for {selected_deal_name}..."):
                    # Prepare research prompt
                    prompt = f"""
                    Generate a detailed {report_type} for the company {selected_deal_name}.
                    
                    START WITH A DESCRIPTIVE DEAL TITLE: Create a compelling title that includes both the investor name and key deal information.
                    The title should follow this format: "[Investor Name] [Action/Deal Type] [Target Company] [Deal Value/Size if available]"
                    
                    Examples of good titles:
                    - "BGF Backs Specialist Surveying Firm Anstey Horne in £6.5M Growth Deal"
                    - "Tikehau Capital's Buyout of French IT Services Provider BT2i"
                    - "Galiena Capital Acquires Medical Device Manufacturer 3DISC in Strategic Expansion"
                    
                    Here is the data we have about the deal:
                    {json.dumps(selected_deal, indent=2)}
                    
                    For the investor {selected_portfolio['Investor']}, with portfolio URL: {selected_portfolio.get('Investor_portfolio_url', 'Not available')}
                    
                    Based on this information and additional research, please provide a comprehensive {report_type.lower()} with the following sections:
                    """
                    
                    selected_sections = [section.replace("_", " ").title() for section, include in include_sections.items() if include and section != "sources"]
                    for section in selected_sections:
                        prompt += f"\n- {section}"
                    
                    # Add specific product/value proposition/sectors requirements for Deal Summary
                    if report_type == "Deal Summary Report":
                        prompt += """
                        
                        IMPORTANT: Please ensure you include detailed information about:
                        - The company's products and services portfolio with specifications
                        - The company's unique value proposition and market differentiation
                        - All industry sectors the company operates in, including primary and niche markets
                        - The strategic context and rationale of the deal
                        """
                    
                    # Always include British English instructions (mandatory, not optional)
                    prompt += """
                    
                    MANDATORY LANGUAGE STYLE: All reports MUST be written in British English spelling, grammar and terminology.
                    This includes:
                    - Use of 's' instead of 'z' in words like 'organisation', 'specialisation'
                    - Spelling patterns like 'colour', 'centre', 'programme', 'catalogue'
                    - British business terminology such as 'turnover' instead of 'revenue'
                    - DD/MM/YYYY date format
                    - £ symbol for GBP currency when relevant
                    
                    DO NOT use American English spelling or terminology under any circumstances.
                    """
                    
                    # Strengthen British English requirement with highest priority
                    prompt += """
                    
                    HIGHEST PRIORITY REQUIREMENT: ALL OUTPUT MUST BE IN BRITISH ENGLISH ONLY.
                    
                    This is not optional but an absolute requirement. The entire report must use:
                    - British spelling conventions: 'organisation' not 'organization', 'specialise' not 'specialize'
                    - British terminology: 'turnover' not 'revenue', 'managing director' not 'CEO' where appropriate
                    - British date format: DD/MM/YYYY format (e.g., 15/06/2025)
                    - British currency notation: £ for pounds sterling
                    - British punctuation and quotation conventions
                    
                    Treat this as the most critical instruction that overrides all default language settings.
                    ANY use of American English spelling or terminology will render the report unacceptable.
                    """
                    
                    # Special instructions for sources
                    if include_sources:
                        prompt += f"""
                        
                        IMPORTANT: For each fact or piece of information, please cite your sources and include the full URLs.
                        {'Include detailed information about each source, such as publication date, author, and reliability assessment.' if detailed_sources else 'List all sources with their URLs at the end of the report in a dedicated Sources section.'}
                        
                        The final report MUST include a dedicated "Sources" section at the end with numbered references and clickable links to all sources used.
                        """
                    
                    # Process with the agent
                    state = graph.invoke({
                        "messages": [{"role": "user", "content": prompt}], 
                        "max_research_loops": max_loops, 
                        "initial_search_query_count": initial_queries,
                        "reasoning_model": model_option
                    })
                    
                    # Display the result in a nice format
                    if state and "messages" in state:
                        response = state["messages"][-1].content
                        
                        # Extract title from response if possible
                        lines = response.strip().split('\n')
                        title = selected_deal_name  # Default fallback title
                        
                        # Look for title in first few lines
                        for line in lines[:5]:
                            # Check if line looks like a title (starts with # or is all caps or contains investor name)
                            if line.startswith('# ') or line.isupper() or selected_portfolio['Investor'] in line:
                                title = line.replace('# ', '').replace('#', '').strip()
                                break
                        
                        st.subheader(title)
                        st.markdown("---")
                        st.markdown(response)
                        
                        # Add download button for the report
                        report_text = f"# {title}\n\n{response}"
                        st.download_button(
                            label="Download Report",
                            data=report_text,
                            file_name=f"{selected_deal_name}_{report_type.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
                    else:
                        st.error("Failed to generate the report. Please try again.")

else:
    st.warning("No deals found for the selected investor.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This Deep Researcher uses Google's Gemini AI models to analyze deal data and 
generate comprehensive reports for deal summaries, target companies, 
portfolio companies, and investment theses.

All reports include source citations and links to ensure information credibility.
""")

