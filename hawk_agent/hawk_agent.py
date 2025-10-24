import gspread
import imaplib
import email
from email.header import decode_header
import pandas as pd
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import json
import boto3
import pickle
from typing import Dict, List, Any
import logging
import time
import uuid

class HawkAgent:
    def __init__(self):
        load_dotenv()
        self.spreadsheet_url = "https://docs.google.com/spreadsheets/d/1siruqibPS8fXtGiCvdhrSlcgsJPo4V5un2f-HpWt31M/edit?gid=0#gid=0"
        self.spreadsheet_id = "1siruqibPS8fXtGiCvdhrSlcgsJPo4V5un2f-HpWt31M"
        self.projects = {}
        self.sheet = None
        self.gc = None
        self.connected = self.setup_google_sheets()
        
        # AWS Bedrock setup
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Memory management
        self.memory_file = 'hawk_memory.pkl'
        self.conversation_memory = self.load_memory()
        self.prospect_insights = {}
        
        print("🧠 Hawk Agent initialized with Claude 4 and memory capabilities")
        
    def setup_google_sheets(self):
        """Setup Google Sheets connection"""
        try:
            # Check if credentials file exists
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json not found")
                print("Run: python setup_credentials.py")
                return False
            
            # Use service account credentials
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # Try to load and validate credentials
            try:
                with open('credentials.json', 'r') as f:
                    cred_data = json.load(f)
                    if 'private_key' not in cred_data or 'client_email' not in cred_data:
                        print("❌ Invalid credentials.json format")
                        return False
            except json.JSONDecodeError:
                print("❌ credentials.json is not valid JSON")
                return False
            
            creds = Credentials.from_service_account_file(
                'credentials.json', scopes=scope)
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.spreadsheet_id)
            print("✅ Connected to Google Sheets")
            return True
        except Exception as e:
            print(f"❌ Google Sheets connection failed: {e}")
            print("Please check your credentials.json file")
            return False
    
    def get_project_tabs(self):
        """Get all project tabs from the spreadsheet"""
        try:
            if not hasattr(self, 'sheet') or self.sheet is None:
                print("❌ Google Sheets not connected")
                return {}
                
            worksheets = self.sheet.worksheets()
            projects = {}
            for i, ws in enumerate(worksheets, 1):
                projects[i] = {
                    'name': ws.title,
                    'worksheet': ws
                }
            return projects
        except Exception as e:
            print(f"Error fetching project tabs: {e}")
            return {}
    
    def display_projects(self):
        """Display available projects"""
        projects = self.get_project_tabs()
        print("\n🦅 Available Projects:")
        print("=" * 30)
        for num, project in projects.items():
            print(f"{num}. {project['name']}")
        return projects
    
    def get_project_data(self, project_num):
        """Get data from selected project tab"""
        projects = self.get_project_tabs()
        if project_num not in projects:
            return None
            
        try:
            worksheet = projects[project_num]['worksheet']
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            return {
                'name': projects[project_num]['name'],
                'data': df,
                'worksheet': worksheet
            }
        except Exception as e:
            print(f"Error fetching project data: {e}")
            return None
    
    def setup_email_connection(self, email_address, password):
        """Setup email connection"""
        try:
            # Connect to Gmail IMAP
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(email_address, password)
            print("✅ Connected to Gmail")
            return True
        except Exception as e:
            print(f"❌ Email connection failed: {e}")
            return False
    
    def search_project_emails(self, project_name, days_back=90, batch_size=100):
        """Search for emails related to the project in batches"""
        try:
            self.mail.select("inbox")
            
            print(f"📧 Searching emails for '{project_name}' (last {days_back} days, batch size: {batch_size})")
            
            # Search for recent emails (broader search)
            date_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Multiple search criteria to catch project-related emails
            search_terms = [
                f'(SUBJECT "{project_name}" SINCE "{date_since}")',
                f'(BODY "{project_name}" SINCE "{date_since}")',
                f'(SUBJECT "K12" SINCE "{date_since}")',
                f'(SUBJECT "school" SINCE "{date_since}")',
                f'(SUBJECT "district" SINCE "{date_since}")',
                f'(SUBJECT "education" SINCE "{date_since}")',
            ]
            
            all_email_ids = set()
            
            for search_term in search_terms:
                try:
                    status, messages = self.mail.search(None, search_term)
                    if messages[0]:
                        email_ids = messages[0].split()
                        all_email_ids.update(email_ids)
                        print(f"  Found {len(email_ids)} emails for: {search_term}")
                except:
                    continue
            
            # Convert to list and get most recent emails
            email_ids = list(all_email_ids)
            email_ids.sort(key=int, reverse=True)  # Most recent first
            
            # Process in batches
            emails_to_process = email_ids[:batch_size]
            print(f"📬 Processing {len(emails_to_process)} most recent emails...")
            
            emails = []
            for i, email_id in enumerate(emails_to_process):
                try:
                    if i % 10 == 0:  # Progress update every 10 emails
                        print(f"  Processing email {i+1}/{len(emails_to_process)}")
                    
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    # Get email body
                    body = self.get_email_body(msg)
                    
                    emails.append({
                        'subject': subject,
                        'from': msg.get("From"),
                        'date': msg.get("Date"),
                        'body': body[:500]  # First 500 chars
                    })
                    
                except Exception as e:
                    print(f"  Error processing email {email_id}: {e}")
                    continue
            
            print(f"✅ Successfully processed {len(emails)} emails")
            return emails
            
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def get_email_body(self, msg):
        """Extract email body"""
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except Exception as e:
            body = f"Error decoding email: {e}"
        return body
    
    def load_memory(self) -> Dict[str, Any]:
        """Load conversation and analysis memory"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'rb') as f:
                    memory = pickle.load(f)
                print(f"🧠 Loaded memory with {len(memory.get('conversations', []))} conversations")
                return memory
        except Exception as e:
            print(f"Error loading memory: {e}")
        return {'conversations': [], 'prospect_analysis': {}, 'insights': []}
    
    def save_memory(self):
        """Save conversation and analysis memory"""
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(self.conversation_memory, f)
            print("💾 Memory saved successfully")
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def ask_claude(self, prompt: str, context: str = "") -> str:
        """Ask Claude 4 for analysis with context"""
        try:
            full_prompt = f"""
You are Hawk Agent, an AI assistant specialized in project management and prospect communication analysis.

Context from previous conversations and analysis:
{context}

Current request:
{prompt}

Provide detailed, actionable insights focusing on:
1. Communication gaps and opportunities
2. Prospect engagement patterns
3. Next steps and recommendations
4. Risk assessment

Be specific and data-driven in your analysis.
"""
            
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": full_prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            claude_response = result['content'][0]['text']
            
            # Save to memory
            self.conversation_memory['conversations'].append({
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': claude_response
            })
            
            return claude_response
            
        except Exception as e:
            return f"Claude analysis failed: {e}"
    
    def analyze_prospects_deep_dive(self, project_data, emails):
        """Deep dive analysis of prospects with Claude 4"""
        df = project_data['data']
        project_name = project_data['name']
        
        print(f"🔍 Analyzing {len(df)} rows in {project_name}")
        print(f"📊 Available columns: {list(df.columns)}")
        
        # Identify prospect columns (including education-specific terms)
        prospect_columns = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['company', 'prospect', 'client', 'customer', 'name', 
                                         'school', 'district', 'organization', 'institution'])]
        
        print(f"🎯 Found prospect columns: {prospect_columns}")
        
        if not prospect_columns:
            return {"error": "No prospect columns found"}
        
        prospect_analysis = {}
        total_prospects = 0
        total_prospects = 0
        
        # Analyze each prospect
        for row_idx, row in df.iterrows():
            for col in prospect_columns:
                prospect_name = str(row[col]).strip()
                if prospect_name and prospect_name.lower() not in ['nan', 'none', '']:
                    total_prospects += 1
                    print(f"🏢 Processing prospect {total_prospects}: {prospect_name}")
                    
                    # Search for prospect-specific emails
                    prospect_emails = self.search_prospect_emails(prospect_name, emails)
                    print(f"  📧 Found {len(prospect_emails)} related emails")
                    print(f"  📧 Found {len(prospect_emails)} related emails")
                    
                    # Get row context
                    row_context = {k: v for k, v in row.items() if pd.notna(v)}
                    
                    # Claude analysis for this prospect
                    print(f"  🧠 Requesting Claude analysis...")
                    context = self.get_memory_context_for_prospect(prospect_name)
                    prompt = f"""
Analyze prospect: {prospect_name}
Project: {project_name}
Spreadsheet data: {row_context}
Recent emails: {len(prospect_emails)} found
Email subjects: {[e['subject'] for e in prospect_emails[:3]]}

Provide analysis on:
1. Communication frequency and quality
2. Missing follow-ups or gaps
3. Prospect engagement level
4. Next recommended actions
5. Risk factors
"""
                    
                    claude_analysis = self.ask_claude(prompt, context)
                    print(f"  ✅ Claude analysis complete ({len(claude_analysis)} chars)")
                    print(f"  ✅ Claude analysis complete ({len(claude_analysis)} chars)")
                    
                    try:
                        prospect_analysis[prospect_name] = {
                            'spreadsheet_data': row_context,
                            'email_count': len(prospect_emails),
                            'recent_emails': prospect_emails[:5],
                            'claude_analysis': claude_analysis,
                            'last_contact': prospect_emails[0]['date'] if prospect_emails else 'No recent contact'
                        }
                        
                        # Store in memory
                        self.conversation_memory['prospect_analysis'][prospect_name] = {
                            'last_analyzed': datetime.now().isoformat(),
                            'analysis': claude_analysis,
                            'email_count': len(prospect_emails)
                        }
                    except Exception as e:
                        prospect_analysis[prospect_name] = f"Analysis error: {e}"
        
        print(f"🏁 Completed analysis of {total_prospects} prospects")
        return prospect_analysis
    
    def search_prospect_emails(self, prospect_name, all_emails):
        """Search for emails related to specific prospect"""
        prospect_emails = []
        search_terms = [prospect_name.lower()]
        
        # Add variations
        if ' ' in prospect_name:
            search_terms.extend(prospect_name.lower().split())
        
        for email_data in all_emails:
            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()
            sender = email_data.get('from', '').lower()
            
            # Check if any search term appears in email
            if any(term in subject or term in body or term in sender for term in search_terms):
                prospect_emails.append(email_data)
        
        return prospect_emails
    
    def get_memory_context_for_prospect(self, prospect_name):
        """Get relevant memory context for a prospect"""
        context = ""
        
        # Previous analysis
        if prospect_name in self.conversation_memory.get('prospect_analysis', {}):
            prev_analysis = self.conversation_memory['prospect_analysis'][prospect_name]
            context += f"Previous analysis ({prev_analysis['last_analyzed']}): {prev_analysis['analysis'][:200]}...\n\n"
        
        # Related conversations
        related_conversations = [conv for conv in self.conversation_memory.get('conversations', []) 
                               if prospect_name.lower() in conv.get('prompt', '').lower()]
        
        if related_conversations:
            context += "Related previous conversations:\n"
            for conv in related_conversations[-2:]:  # Last 2 related conversations
                context += f"- {conv['timestamp']}: {conv['response'][:100]}...\n"
        
        return context
    
    def analyze_project_status(self, project_data, emails):
        """Enhanced project analysis with prospect deep dive"""
        print("🔍 Performing deep prospect analysis...")
        
        # Basic analysis
        analysis = {
            'project_name': project_data['name'],
            'spreadsheet_status': self.analyze_spreadsheet_status(project_data['data']),
            'email_status': self.analyze_email_status(emails),
            'last_communication': self.get_last_communication(emails),
            'recommendations': []
        }
        
        # Deep dive prospect analysis
        prospect_analysis = self.analyze_prospects_deep_dive(project_data, emails)
        analysis['prospect_analysis'] = prospect_analysis
        
        # Claude overall project analysis
        context = self.get_project_memory_context(project_data['name'])
        overall_prompt = f"""
Project: {project_data['name']}
Total prospects analyzed: {len(prospect_analysis)}
Total emails: {len(emails)}
Spreadsheet rows: {len(project_data['data'])}

Provide overall project health assessment and strategic recommendations.
"""
        
        analysis['claude_project_analysis'] = self.ask_claude(overall_prompt, context)
        
        # Save memory
        self.save_memory()
        
        return analysis
    
    def get_project_memory_context(self, project_name):
        """Get memory context for project-level analysis"""
        context = ""
        project_conversations = [conv for conv in self.conversation_memory.get('conversations', []) 
                               if project_name.lower() in conv.get('prompt', '').lower()]
        
        if project_conversations:
            context += f"Previous project analysis history ({len(project_conversations)} conversations):\n"
            for conv in project_conversations[-3:]:  # Last 3 conversations
                context += f"- {conv['timestamp']}: {conv['response'][:150]}...\n"
        
        return context
    
    def analyze_spreadsheet_status(self, df):
        """Analyze status from spreadsheet data"""
        if df.empty:
            return "No data available"
        
        status_info = {
            'total_rows': len(df),
            'columns': list(df.columns),
            'recent_updates': "Available" if len(df) > 0 else "None"
        }
        
        # Look for status-related columns
        status_columns = [col for col in df.columns if 'status' in col.lower()]
        if status_columns:
            status_info['status_column'] = status_columns[0]
            status_info['status_values'] = df[status_columns[0]].value_counts().to_dict()
        
        return status_info
    
    def analyze_email_status(self, emails):
        """Analyze communication status from emails"""
        if not emails:
            return "No recent emails"
        
        return {
            'total_emails': len(emails),
            'date_range': f"{emails[-1]['date']} to {emails[0]['date']}",
            'recent_subjects': [email['subject'] for email in emails[:3]]
        }
    
    def get_last_communication(self, emails):
        """Get last communication details"""
        if not emails:
            return "No recent communication"
        
        latest = emails[0]
        return {
            'date': latest['date'],
            'subject': latest['subject'],
            'from': latest['from']
        }
    
    def run_analysis(self):
        """Main method to run project analysis"""
        print("🦅 Hawk Agent - Project Status Monitor")
        print("=" * 40)
        
        # Check connection first
        if not self.connected:
            print("❌ Cannot proceed without Google Sheets connection")
            print("Run: python validate_credentials.py to diagnose issues")
            return
        
        # Display projects
        projects = self.display_projects()
        if not projects:
            print("No projects found")
            return
        
        # Get user selection
        try:
            choice = int(input("\nSelect project number: "))
            if choice not in projects:
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
        
        # Get project data
        project_data = self.get_project_data(choice)
        if not project_data:
            print("Failed to fetch project data")
            return
        
        print(f"\n📊 Analyzing project: {project_data['name']}")
        
        # Get email credentials from .env or prompt
        email_address = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')
        
        if not email_address:
            email_address = input("Enter email address: ")
        if not password:
            password = input("Enter email password (or app password): ")
        
        print(f"Using email: {email_address}")
        
        if not self.setup_email_connection(email_address, password):
            print("Proceeding with spreadsheet analysis only...")
            emails = []
        else:
            print(f"🔍 Searching emails for '{project_data['name']}'...")
            emails = self.search_project_emails(project_data['name'])
        
        # Analyze and display results
        analysis = self.analyze_project_status(project_data, emails)
        self.display_analysis(analysis)
    
    def display_analysis(self, analysis):
        """Display enhanced analysis results with prospect insights"""
        print(f"\n🦅 HAWK INTELLIGENCE REPORT")
        print("=" * 60)
        print(f"Project: {analysis['project_name']}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Powered by: Claude 4 + Memory Intelligence")
        
        # Project Overview
        print(f"\n📊 PROJECT OVERVIEW:")
        ss_status = analysis['spreadsheet_status']
        if isinstance(ss_status, dict):
            print(f"  • Total Records: {ss_status.get('total_rows', 0)}")
            print(f"  • Columns: {', '.join(ss_status.get('columns', [])[:5])}")
        
        email_status = analysis['email_status']
        if isinstance(email_status, dict):
            print(f"  • Total Emails Analyzed: {email_status['total_emails']}")
        
        # Claude Project Analysis
        if 'claude_project_analysis' in analysis:
            print(f"\n🧠 CLAUDE PROJECT INTELLIGENCE:")
            print(f"{analysis['claude_project_analysis']}")
        
        # Prospect Deep Dive
        if 'prospect_analysis' in analysis and analysis['prospect_analysis']:
            print(f"\n🎯 PROSPECT DEEP DIVE ANALYSIS:")
            print("=" * 40)
            
            for prospect_name, prospect_data in analysis['prospect_analysis'].items():
                print(f"\n🏢 PROSPECT: {prospect_name.upper()}")
                print("-" * 30)
                
                # Check if prospect_data is a string (error case)
                if isinstance(prospect_data, str):
                    print(f"  ❌ Error: {prospect_data}")
                    continue
                
                # Check if prospect_data is a dict
                if not isinstance(prospect_data, dict):
                    print(f"  ❌ Invalid data format")
                    continue
                
                # Basic stats
                print(f"  📧 Email Communications: {prospect_data.get('email_count', 0)}")
                print(f"  🕰️ Last Contact: {prospect_data.get('last_contact', 'Unknown')}")
                
                # Spreadsheet data
                if prospect_data.get('spreadsheet_data'):
                    print(f"  📊 Spreadsheet Data:")
                    for key, value in list(prospect_data['spreadsheet_data'].items())[:5]:
                        print(f"    - {key}: {value}")
                
                # Recent email subjects
                if prospect_data.get('recent_emails'):
                    print(f"  📬 Recent Email Subjects:")
                    for email_data in prospect_data['recent_emails'][:3]:
                        print(f"    - {email_data.get('subject', 'No subject')}")
                
                # Claude Analysis
                print(f"  🧠 CLAUDE INTELLIGENCE:")
                claude_text = prospect_data.get('claude_analysis', 'No analysis available')
                # Format Claude response for better readability
                formatted_analysis = claude_text.replace('\n', '\n    ')
                print(f"    {formatted_analysis}")
                
                print("\n" + "-" * 50)
        
        # Memory Stats
        memory_stats = self.get_memory_stats()
        print(f"\n🧠 MEMORY INTELLIGENCE:")
        print(f"  • Total Conversations: {memory_stats['total_conversations']}")
        print(f"  • Prospects Analyzed: {memory_stats['prospects_analyzed']}")
        print(f"  • Memory File Size: {memory_stats['memory_size']} KB")
    
    def get_memory_stats(self):
        """Get memory statistics"""
        stats = {
            'total_conversations': len(self.conversation_memory.get('conversations', [])),
            'prospects_analyzed': len(self.conversation_memory.get('prospect_analysis', {})),
            'memory_size': 0
        }
        
        try:
            if os.path.exists(self.memory_file):
                stats['memory_size'] = round(os.path.getsize(self.memory_file) / 1024, 2)
        except:
            pass
        
        return stats

if __name__ == "__main__":
    agent = HawkAgent()
    agent.run_analysis()