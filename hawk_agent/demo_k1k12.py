#!/usr/bin/env python3
"""
Demo of Hawk Agent analyzing K1-K12 project with mock email data
"""
from hawk_agent import HawkAgent
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_mock_emails_for_prospects(prospects):
    """Generate realistic mock emails for K1-K12 prospects"""
    mock_emails = []
    
    # Common email patterns for K1-K12 education sector
    email_templates = [
        "Follow-up on {prospect} implementation timeline",
        "Re: {prospect} - Budget approval status",
        "{prospect} - Technical requirements discussion",
        "Meeting recap: {prospect} K-12 solution",
        "Action items from {prospect} demo session",
        "{prospect} - Contract negotiation update",
        "Urgent: {prospect} decision deadline approaching",
        "{prospect} - Reference customer introduction",
        "Re: {prospect} pilot program proposal"
    ]
    
    for prospect in prospects[:5]:  # Focus on top 5 prospects
        num_emails = random.randint(2, 8)
        for i in range(num_emails):
            subject = random.choice(email_templates).format(prospect=prospect)
            mock_emails.append({
                'subject': subject,
                'from': f'sales.team@company.com',
                'date': (datetime.now() - timedelta(days=random.randint(1, 45))).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': f"Mock email content regarding {prospect} K1-K12 education solution. Discussion about implementation, pricing, and next steps..."
            })
    
    # Sort by date (newest first)
    mock_emails.sort(key=lambda x: datetime.strptime(x['date'], "%a, %d %b %Y %H:%M:%S"), reverse=True)
    return mock_emails

def main():
    print("🦅 Hawk Agent Demo - K1-K12 Project Analysis")
    print("=" * 50)
    
    # Initialize agent
    agent = HawkAgent()
    
    if not agent.connected:
        print("❌ Cannot connect to Google Sheets")
        return
    
    # Get K1-K12 project data
    project_data = agent.get_project_data(1)  # K1-K12 is project #1
    
    if not project_data:
        print("❌ Could not fetch K1-K12 project data")
        return
    
    print(f"📊 Analyzing project: {project_data['name']}")
    print(f"📋 Found {len(project_data['data'])} records in spreadsheet")
    
    # Display spreadsheet columns
    print(f"\n📊 Spreadsheet Columns:")
    for i, col in enumerate(project_data['data'].columns, 1):
        print(f"  {i}. {col}")
    
    # Extract prospect names from likely columns
    prospect_columns = [col for col in project_data['data'].columns 
                       if any(keyword in col.lower() for keyword in 
                             ['company', 'prospect', 'client', 'customer', 'name', 'school', 'district'])]
    
    print(f"\n🎯 Identified prospect columns: {prospect_columns}")
    
    # Get unique prospects
    all_prospects = []
    for col in prospect_columns:
        prospects = project_data['data'][col].dropna().unique()
        all_prospects.extend([str(p).strip() for p in prospects if str(p).lower() not in ['nan', 'none', '']])
    
    unique_prospects = list(set(all_prospects))[:10]  # Top 10 prospects
    print(f"\n🏢 Found {len(unique_prospects)} unique prospects:")
    for i, prospect in enumerate(unique_prospects, 1):
        print(f"  {i}. {prospect}")
    
    # Generate mock emails
    print(f"\n📧 Generating mock email data for analysis...")
    mock_emails = generate_mock_emails_for_prospects(unique_prospects)
    print(f"📧 Generated {len(mock_emails)} mock emails")
    
    # Run analysis
    print(f"\n🔍 Performing deep prospect analysis...")
    analysis = agent.analyze_project_status(project_data, mock_emails)
    
    # Display results
    agent.display_analysis(analysis)
    
    print(f"\n🔗 Spreadsheet URL: {agent.spreadsheet_url}")
    print(f"💾 Analysis saved to memory for future reference")

if __name__ == "__main__":
    main()