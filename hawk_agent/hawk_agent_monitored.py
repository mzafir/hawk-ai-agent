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

class HawkAgentMonitored:
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
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Memory management
        self.memory_file = 'hawk_memory.pkl'
        self.conversation_memory = self.load_memory()
        self.prospect_insights = {}
        
        # Cost and monitoring tracking
        self.session_id = str(uuid.uuid4())[:8]
        self.metrics = {
            'bedrock_calls': 0,
            'bedrock_tokens': 0,
            'email_processed': 0,
            'prospects_analyzed': 0,
            'session_start': datetime.now().isoformat(),
            'estimated_cost': 0.0
        }
        
        self.setup_logging()
        print(f"🧠 Hawk Agent initialized with monitoring (Session: {self.session_id})")
    
    def setup_logging(self):
        """Setup CloudWatch logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'HawkAgent-{self.session_id}')
        self.logger.info(f"Session {self.session_id} started")
    
    def send_cloudwatch_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """Send metrics to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='HawkAgent',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Dimensions': [
                        {'Name': 'SessionId', 'Value': self.session_id}
                    ],
                    'Timestamp': datetime.now()
                }]
            )
            self.logger.info(f"CloudWatch metric: {metric_name}={value}")
        except Exception as e:
            self.logger.error(f"CloudWatch metric failed: {e}")
    
    def calculate_bedrock_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate Bedrock cost (Claude 3 Sonnet pricing)"""
        input_cost = (input_tokens / 1000) * 0.003  # $3 per 1K input tokens
        output_cost = (output_tokens / 1000) * 0.015  # $15 per 1K output tokens
        return input_cost + output_cost
    
    def ask_claude(self, prompt: str, context: str = "") -> str:
        """Ask Claude with cost tracking"""
        start_time = time.time()
        self.metrics['bedrock_calls'] += 1
        
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
            
            # Estimate input tokens (rough approximation)
            input_tokens = len(full_prompt.split()) * 1.3
            
            self.logger.info(f"Bedrock call #{self.metrics['bedrock_calls']} - Est. input tokens: {input_tokens}")
            
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
            
            # Estimate output tokens
            output_tokens = len(claude_response.split()) * 1.3
            
            # Calculate cost
            call_cost = self.calculate_bedrock_cost(input_tokens, output_tokens)
            self.metrics['estimated_cost'] += call_cost
            self.metrics['bedrock_tokens'] += input_tokens + output_tokens
            
            response_time = time.time() - start_time
            
            # Send metrics to CloudWatch
            self.send_cloudwatch_metric('BedrockCalls', 1)
            self.send_cloudwatch_metric('BedrockTokens', input_tokens + output_tokens)
            self.send_cloudwatch_metric('BedrockCost', call_cost, 'None')
            self.send_cloudwatch_metric('BedrockResponseTime', response_time * 1000, 'Milliseconds')
            
            self.logger.info(f"Bedrock response: {len(claude_response)} chars, Cost: ${call_cost:.4f}, Time: {response_time:.2f}s")
            
            # Save to memory
            self.conversation_memory['conversations'].append({
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': claude_response,
                'cost': call_cost,
                'tokens': input_tokens + output_tokens
            })
            
            return claude_response
            
        except Exception as e:
            self.send_cloudwatch_metric('BedrockErrors', 1)
            self.logger.error(f"Bedrock call failed: {e}")
            return f"Claude analysis failed: {e}"
    
    def search_project_emails(self, project_name, days_back=90, batch_size=100):
        """Search emails with monitoring"""
        start_time = time.time()
        self.logger.info(f"Starting email search for {project_name}")
        
        try:
            self.mail.select("inbox")
            
            print(f"📧 Searching emails for '{project_name}' (last {days_back} days, batch size: {batch_size})")
            
            # Search terms
            date_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
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
            
            # Process emails
            email_ids = list(all_email_ids)
            email_ids.sort(key=int, reverse=True)
            emails_to_process = email_ids[:batch_size]
            
            print(f"📬 Processing {len(emails_to_process)} most recent emails...")
            
            emails = []
            for i, email_id in enumerate(emails_to_process):
                try:
                    if i % 10 == 0:
                        print(f"  Processing email {i+1}/{len(emails_to_process)}")
                    
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    body = self.get_email_body(msg)
                    
                    emails.append({
                        'subject': subject,
                        'from': msg.get("From"),
                        'date': msg.get("Date"),
                        'body': body[:500]
                    })
                    
                    self.metrics['email_processed'] += 1
                    
                except Exception as e:
                    print(f"  Error processing email {email_id}: {e}")
                    continue
            
            search_time = time.time() - start_time
            self.send_cloudwatch_metric('EmailsProcessed', len(emails))
            self.send_cloudwatch_metric('EmailSearchTime', search_time * 1000, 'Milliseconds')
            
            self.logger.info(f"Email search completed: {len(emails)} emails in {search_time:.2f}s")
            print(f"✅ Successfully processed {len(emails)} emails")
            
            return emails
            
        except Exception as e:
            self.send_cloudwatch_metric('EmailSearchErrors', 1)
            self.logger.error(f"Email search failed: {e}")
            return []
    
    def analyze_prospects_deep_dive(self, project_data, emails):
        """Prospect analysis with monitoring"""
        start_time = time.time()
        df = project_data['data']
        project_name = project_data['name']
        
        self.logger.info(f"Starting prospect analysis for {project_name}")
        print(f"🔍 Analyzing {len(df)} rows in {project_name}")
        print(f"📊 Available columns: {list(df.columns)}")
        
        # Find prospect columns
        prospect_columns = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['company', 'prospect', 'client', 'customer', 'name', 
                                         'school', 'district', 'organization', 'institution'])]
        
        print(f"🎯 Found prospect columns: {prospect_columns}")
        
        if not prospect_columns:
            return {"error": "No prospect columns found"}
        
        prospect_analysis = {}
        total_prospects = 0
        
        # Analyze each prospect
        for row_idx, row in df.iterrows():
            for col in prospect_columns:
                prospect_name = str(row[col]).strip()
                if prospect_name and prospect_name.lower() not in ['nan', 'none', '']:
                    total_prospects += 1
                    self.metrics['prospects_analyzed'] += 1
                    
                    print(f"🏢 Processing prospect {total_prospects}: {prospect_name}")
                    
                    # Search for prospect-specific emails
                    prospect_emails = self.search_prospect_emails(prospect_name, emails)
                    print(f"  📧 Found {len(prospect_emails)} related emails")
                    
                    # Get row context
                    row_context = {k: v for k, v in row.items() if pd.notna(v)}
                    
                    # Claude analysis
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
        
        analysis_time = time.time() - start_time
        self.send_cloudwatch_metric('ProspectsAnalyzed', total_prospects)
        self.send_cloudwatch_metric('ProspectAnalysisTime', analysis_time * 1000, 'Milliseconds')
        
        self.logger.info(f"Prospect analysis completed: {total_prospects} prospects in {analysis_time:.2f}s")
        print(f"🏁 Completed analysis of {total_prospects} prospects")
        
        return prospect_analysis
    
    def display_cost_summary(self):
        """Display cost and usage summary"""
        session_duration = (datetime.now() - datetime.fromisoformat(self.metrics['session_start'])).total_seconds()
        
        print(f"\n💰 COST & USAGE SUMMARY")
        print("=" * 30)
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {session_duration:.1f} seconds")
        print(f"Bedrock Calls: {self.metrics['bedrock_calls']}")
        print(f"Total Tokens: {self.metrics['bedrock_tokens']:.0f}")
        print(f"Emails Processed: {self.metrics['email_processed']}")
        print(f"Prospects Analyzed: {self.metrics['prospects_analyzed']}")
        print(f"Estimated Cost: ${self.metrics['estimated_cost']:.4f}")
        
        # Send final metrics
        self.send_cloudwatch_metric('SessionDuration', session_duration, 'Seconds')
        self.send_cloudwatch_metric('TotalCost', self.metrics['estimated_cost'], 'None')
        
        self.logger.info(f"Session {self.session_id} completed - Cost: ${self.metrics['estimated_cost']:.4f}")
    
    # Include all other methods from original HawkAgent
    def setup_google_sheets(self):
        """Setup Google Sheets connection"""
        try:
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json not found")
                return False
            
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.spreadsheet_id)
            print("✅ Connected to Google Sheets")
            return True
        except Exception as e:
            print(f"❌ Google Sheets connection failed: {e}")
            return False
    
    def get_project_tabs(self):
        """Get all project tabs from the spreadsheet"""
        try:
            if not hasattr(self, 'sheet') or self.sheet is None:
                return {}
            worksheets = self.sheet.worksheets()
            projects = {}
            for i, ws in enumerate(worksheets, 1):
                projects[i] = {'name': ws.title, 'worksheet': ws}
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
            return {'name': projects[project_num]['name'], 'data': df, 'worksheet': worksheet}
        except Exception as e:
            print(f"Error fetching project data: {e}")
            return None
    
    def setup_email_connection(self, email_address, password):
        """Setup email connection"""
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(email_address, password)
            print("✅ Connected to Gmail")
            return True
        except Exception as e:
            print(f"❌ Email connection failed: {e}")
            return False
    
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
    
    def search_prospect_emails(self, prospect_name, all_emails):
        """Search for emails related to specific prospect"""
        prospect_emails = []
        search_terms = [prospect_name.lower()]
        
        if ' ' in prospect_name:
            search_terms.extend(prospect_name.lower().split())
        
        for email_data in all_emails:
            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()
            sender = email_data.get('from', '').lower()
            
            if any(term in subject or term in body or term in sender for term in search_terms):
                prospect_emails.append(email_data)
        
        return prospect_emails
    
    def get_memory_context_for_prospect(self, prospect_name):
        """Get relevant memory context for a prospect"""
        context = ""
        
        if prospect_name in self.conversation_memory.get('prospect_analysis', {}):
            prev_analysis = self.conversation_memory['prospect_analysis'][prospect_name]
            context += f"Previous analysis ({prev_analysis['last_analyzed']}): {prev_analysis['analysis'][:200]}...\n\n"
        
        related_conversations = [conv for conv in self.conversation_memory.get('conversations', []) 
                               if prospect_name.lower() in conv.get('prompt', '').lower()]
        
        if related_conversations:
            context += "Related previous conversations:\n"
            for conv in related_conversations[-2:]:
                context += f"- {conv['timestamp']}: {conv['response'][:100]}...\n"
        
        return context
    
    def run_analysis(self):
        """Main method to run project analysis with monitoring"""
        print("🦅 Hawk Agent - Project Status Monitor (Monitored)")
        print("=" * 50)
        
        if not self.connected:
            print("❌ Cannot proceed without Google Sheets connection")
            return
        
        projects = self.display_projects()
        if not projects:
            print("No projects found")
            return
        
        try:
            choice = int(input("\nSelect project number: "))
            if choice not in projects:
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
        
        project_data = self.get_project_data(choice)
        if not project_data:
            print("Failed to fetch project data")
            return
        
        print(f"\n📊 Analyzing project: {project_data['name']}")
        
        # Get email credentials
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
            emails = self.search_project_emails(project_data['name'])
        
        # Run analysis
        print("🔍 Performing deep prospect analysis...")
        prospect_analysis = self.analyze_prospects_deep_dive(project_data, emails)
        
        # Save memory and display cost summary
        self.save_memory()
        self.display_cost_summary()

if __name__ == "__main__":
    agent = HawkAgentMonitored()
    agent.run_analysis()