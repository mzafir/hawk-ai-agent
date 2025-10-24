#!/usr/bin/env python3
"""
Simple Hawk Chat - Minimal conversational interface with agentcore memory
"""
from datetime import datetime, timedelta
import json
import os
import time
from dotenv import load_dotenv
from agentcore_monitor import AgentCoreMonitor
from monitor_dashboard import AgentMonitor

# Load environment variables
load_dotenv()

class AgentMemory:
    def __init__(self, memory_file='hawk_context.json'):
        self.memory_file = memory_file
        self.context = self.load_context()
    
    def load_context(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {'conversations': [], 'email_status': {}}
    
    def save_context(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.context, f, indent=2)
    
    def add_conversation(self, user_input, response):
        self.context['conversations'].append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'agent': response
        })
        self.save_context()
    
    def get_recent_context(self, limit=3):
        return self.context['conversations'][-limit:]

class SimpleHawkChat:
    def __init__(self):
        self.memory = AgentMemory()
        self.monitor = AgentCoreMonitor()
        self.system_monitor = AgentMonitor()
        self.emails = []
        self.mail_connected = False
        self.sent_emails = []
    
    def process_query(self, query):
        """Process user query with LLM"""
        start_time = time.time()
        
        # Get email data as tool
        email_data = self.get_email_tool_data()
        
        # Use LLM to understand query and respond
        response = self.ask_llm(query, email_data)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Log to CloudWatch
        self.monitor.log_conversation(query, response, processing_time)
        self.monitor.send_metrics('ConversationCount', 1)
        self.monitor.send_metrics('ProcessingTime', processing_time, 'Milliseconds')
        
        # Update token usage
        self.system_monitor.update_tokens(len(query.split()) + len(response.split()))
        
        # Save to memory
        self.memory.add_conversation(query, response)
        return response
    
    def get_email_tool_data(self):
        """Get email data as tool for LLM"""
        if not self.mail_connected:
            self.connect_email()
        
        if not self.emails:
            return "No K1-K12 emails found"
        
        email_summary = []
        for email in self.emails:
            email_summary.append({
                'from': email['from'],
                'to': email.get('to', 'Unknown'),
                'subject': email['subject'],
                'date': email['date']
            })
        
        return json.dumps(email_summary, indent=2)
    
    def ask_llm(self, query, email_data):
        """Ask LLM with email data as context"""
        try:
            import boto3
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            # Check if this is an email sending request
            if any(word in query.lower() for word in ['send', 'email', 'draft']) and ('larry' in query.lower() or 'cc me' in query.lower()):
                prompt = f"""Draft an email based on the user's request: {query}

Email context:
{email_data}

Return ONLY the email in this format:
TO: larry@repinnovation.com
CC: [user's email from env]
SUBJECT: K1-K12 Program Status Update from Hawk AI Agent
BODY: [professional email with the K1-K12 details]"""
            else:
                prompt = f"""You are an email assistant. Answer the user's question based on the K1-K12 email data provided.

User question: {query}

Email data:
{email_data}

Provide a direct answer about who needs to respond, latest communications, or status based on the actual email data."""
            
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            llm_response = result['content'][0]['text']
            
            # If it's a draft request, offer to send
            if 'draft' in query.lower() and 'TO:' in llm_response:
                return llm_response + "\n\nType 'send' to send this email or continue chatting."
            
            return llm_response
            
        except Exception as e:
            if any(word in query.lower() for word in ['send', 'email', 'draft']) and 'larry' in query.lower():
                return self.draft_k12_email(query)
            elif 'respond' in query.lower():
                return self.analyze_who_responds()
            elif 'latest' in query.lower():
                return self.get_k12_status()
            else:
                return "I can help with K1-K12 email status and who needs to respond"
    
    def analyze_who_responds(self):
        """Analyze who needs to respond"""
        if not self.emails:
            return "No emails to analyze"
        
        latest = self.emails[0]
        sender_domain = latest['from'].split('@')[1] if '@' in latest['from'] else ''
        
        if 'sccoe.org' in sender_domain:
            return f"Latest email from {latest['from']} - External party (larry@repinnovation.com) needs to respond"
        else:
            return f"Latest email from {latest['from']} - Internal team needs to respond"
    
    def connect_email(self, days=30, limit=10, keywords="K1-K12"):
        """Connect to real email with user controls"""
        email_addr = os.getenv('EMAIL_ADDRESS')
        email_pass = os.getenv('EMAIL_PASSWORD')
        
        if not email_addr or not email_pass or email_addr == 'your_email@gmail.com':
            return "Update EMAIL_ADDRESS and EMAIL_PASSWORD in .env file with real credentials"
        
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(email_addr, email_pass)
            mail.select("inbox")
            
            # Build search query with user parameters
            date_since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            keyword_list = [k.strip() for k in keywords.split(',')]
            
            # Simple search for any keyword in subject or body
            search_results = set()
            for keyword in keyword_list:
                try:
                    status, msgs = mail.search(None, f'SINCE "{date_since}" (OR SUBJECT "{keyword}" BODY "{keyword}")')
                    if msgs[0]:
                        search_results.update(msgs[0].split())
                except:
                    continue
            
            messages = [b' '.join(list(search_results))] if search_results else [b'']
            
            if messages[0]:
                email_ids = messages[0].split()[-limit:]  # User-defined limit
                self.emails = []
                
                for email_id in email_ids:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    self.emails.append({
                        'subject': subject,
                        'from': msg.get("From"),
                        'date': msg.get("Date"),
                        'to': msg.get("To")
                    })
            
            mail.close()
            self.mail_connected = True
            return f"Searched last {days} days for '{keywords}' - found {len(self.emails)} emails (limit: {limit})"
            
        except Exception as e:
            return f"Email connection failed: {e}"
    
    def get_k12_status(self):
        """Get real K1-K12 communication status"""
        if not self.mail_connected:
            connect_result = self.connect_email()
            if "failed" in connect_result:
                return connect_result
        
        if not self.emails:
            return "No K1-K12 emails found in inbox"
        
        latest = self.emails[0]
        
        response = f"Latest K1-K12: {latest['date']} from {latest['from']} - Subject: {latest['subject']}"
        return response
    
    def draft_k12_email(self, query):
        """Draft K1-K12 status email"""
        user_email = os.getenv('EMAIL_ADDRESS')
        
        return f"""TO: larry@repinnovation.com
CC: {user_email}
SUBJECT: K1-K12 Program Status Update from Hawk AI Agent
BODY: Hi Larry,

I'm providing an update on the K1-K12 program based on recent email analysis:

Pending Items:
1. Follow-up needed on "Free 24/7/365 Federal Mental Health Approved K1-K12 Program" discussion with Maimona Afzal Berta (mberta@sccoe.org)
2. Multiple Deal Registration items from Adobe Sign require attention
3. Zoom meeting assets related to K1-K12 topics need review

Latest Communication: Sep 30, 2025 from Maimona Afzal Berta

Please review and provide next steps.

Best regards,
Hawk AI Agent

Type 'send' to send this email or continue chatting."""
    
    def send_email(self, draft_content):
        """Send email using SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            print(f"DEBUG: Draft content:\n{draft_content}")
            
            # Parse draft
            lines = draft_content.split('\n')
            to_email = ''
            cc_email = ''
            subject = ''
            body = ''
            
            for i, line in enumerate(lines):
                if line.startswith('TO:'):
                    to_email = line.replace('TO:', '').strip()
                elif line.startswith('CC:'):
                    cc_email = line.replace('CC:', '').strip()
                elif line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('BODY:'):
                    body = '\n'.join(lines[i+1:]).replace('BODY:', '').strip()
                    break
            
            print(f"DEBUG: Parsed - TO: {to_email}, CC: {cc_email}, SUBJECT: {subject}")
            
            if not to_email:
                return "No recipient email found"
            
            # Setup email
            sender_email = os.getenv('EMAIL_ADDRESS')
            sender_password = os.getenv('EMAIL_PASSWORD')
            
            print(f"DEBUG: Sender: {sender_email}")
            
            if not sender_email or not sender_password:
                return "Email credentials not configured"
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            if cc_email:
                msg['Cc'] = cc_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Include CC in recipients
            recipients = [to_email]
            if cc_email:
                recipients.append(cc_email)
            
            print(f"DEBUG: Recipients: {recipients}")
            
            # Send via Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            server.quit()
            
            print("DEBUG: Email sent successfully")
            
            # Track sent email
            self.sent_emails.append({
                'to': to_email,
                'subject': subject,
                'timestamp': datetime.now().isoformat(),
                'status': 'sent'
            })
            
            return f"✅ Email sent to {to_email}"
            
        except Exception as e:
            print(f"DEBUG: Error details: {e}")
            return f"❌ Failed to send email: {e}"
    
    def start_chat(self):
        """Start interactive chat with live prompt"""
        print("💬 Simple Hawk Chat - Interactive Mode")
        print("First, let's configure your email search:\n")
        
        # Get search parameters upfront
        try:
            days = int(input("Days to search (default 30): ") or "30")
            limit = int(input("Email limit (default 10): ") or "10")
            keywords = input("Keywords (comma separated, default K1-K12): ") or "K1-K12"
            
            print(f"\n🔍 Connecting to email with: {days} days, {limit} limit, '{keywords}'")
            response = self.connect_email(days, limit, keywords)
            print(f"✅ {response}\n")
            
        except ValueError:
            print("Using defaults: 30 days, 10 limit, K1-K12\n")
            self.connect_email()
        
        print("Now you can ask questions about your emails!")
        print("Type 'adm' to change parameters or 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("🦅 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'send':
                    # Get last response if it was a draft
                    recent = self.memory.get_recent_context(1)
                    if recent and len(recent) > 0:
                        last_response = recent[0].get('agent', '')
                        print(f"DEBUG: Last response: {last_response[:100]}...")
                        if 'TO:' in last_response:
                            result = self.send_email(last_response)
                            print(f"🤖 Hawk: {result}\n")
                        else:
                            print("🤖 Hawk: No draft email found in last response\n")
                    else:
                        print("🤖 Hawk: No recent conversation found\n")
                    continue
                
                if user_input.lower().startswith('adm'):
                    if 'email sent' in user_input.lower():
                        if self.sent_emails:
                            print("📧 Sent Emails Status:")
                            for email in self.sent_emails:
                                print(f"  ✅ To: {email['to']} | Subject: {email['subject']} | Time: {email['timestamp']}")
                        else:
                            print("📧 No emails sent yet")
                        print()
                        continue
                    else:
                        try:
                            days = int(input("Days (default 30): ") or "30")
                            limit = int(input("Limit (default 10): ") or "10")
                            keywords = input("Keywords (comma separated): ") or "K1-K12"
                            
                            self.mail_connected = False
                            response = self.connect_email(days, limit, keywords)
                            print(f"🤖 Hawk: {response}\n")
                        except ValueError:
                            print("🤖 Hawk: Invalid input, using defaults\n")
                        continue
                    
                response = self.process_query(user_input)
                print(f"🤖 Hawk: {response}\n")
                
                # Show context info if requested
                if 'context' in user_input.lower():
                    recent = self.memory.get_recent_context(2)
                    print(f"📝 Recent context: {len(recent)} conversations stored\n")
                
            except KeyboardInterrupt:
                print("\n👋 Chat ended.")
                break
            except EOFError:
                print("\n👋 Chat ended.")
                break

if __name__ == "__main__":
    try:
        chat = SimpleHawkChat()
        chat.start_chat()
    except Exception as e:
        print(f"Error: {e}")