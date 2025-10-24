#!/usr/bin/env python3
"""
Hawk Chat Agent - Conversational interface for email and project analysis
"""
import os
import json
import boto3
import pickle
from datetime import datetime
from hawk_agent import HawkAgent
import re

class HawkChatAgent(HawkAgent):
    def __init__(self):
        super().__init__()
        self.chat_memory = []
        self.current_project_data = None
        self.current_emails = []
        print("💬 Hawk Chat Agent initialized - Ready for conversation!")
    
    def process_query(self, user_query: str) -> str:
        """Process natural language query and return intelligent response"""
        query_lower = user_query.lower()
        
        # Store user query in chat memory
        self.chat_memory.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'user',
            'content': user_query
        })
        
        # Determine query type and route to appropriate handler
        if any(keyword in query_lower for keyword in ['communication', 'email', 'contact', 'message']):
            response = self.handle_communication_query(user_query)
        elif any(keyword in query_lower for keyword in ['status', 'progress', 'update']):
            response = self.handle_status_query(user_query)
        elif any(keyword in query_lower for keyword in ['who', 'responsible', 'owner', 'assigned']):
            response = self.handle_responsibility_query(user_query)
        elif any(keyword in query_lower for keyword in ['stuck', 'blocked', 'waiting', 'pending']):
            response = self.handle_bottleneck_query(user_query)
        else:
            response = self.handle_general_query(user_query)
        
        # Store response in chat memory
        self.chat_memory.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'assistant',
            'content': response
        })
        
        return response
    
    def handle_communication_query(self, query: str) -> str:
        """Handle queries about communications and emails"""
        # Extract potential project/company names from query
        entities = self.extract_entities(query)
        
        if not self.current_emails:
            return "I don't have any email data loaded. Please load a project first using 'load project [name]' or run a full analysis."
        
        # Search for relevant communications
        relevant_emails = self.search_communications(entities, self.current_emails)
        
        if not relevant_emails:
            entity_text = f" related to {', '.join(entities)}" if entities else ""
            return f"I don't see any recent communications{entity_text} in the loaded email data."
        
        # Analyze communication patterns
        analysis = self.analyze_communication_patterns(relevant_emails, entities)
        
        return self.format_communication_response(analysis, entities)
    
    def handle_bottleneck_query(self, query: str) -> str:
        """Handle queries about stuck/blocked communications"""
        entities = self.extract_entities(query)
        
        if not self.current_emails:
            return "I need email data to analyze bottlenecks. Please load a project first."
        
        # Find communications that might be stuck
        stuck_communications = self.find_stuck_communications(self.current_emails, entities)
        
        if not stuck_communications:
            return "I don't see any obviously stuck communications in the recent data."
        
        return self.format_bottleneck_response(stuck_communications)
    
    def extract_entities(self, query: str) -> list:
        """Extract potential company/project names from query"""
        # Look for quoted strings, capitalized words, or known patterns
        entities = []
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted)
        
        # Extract words that might be company/project names (capitalized, specific patterns)
        words = query.split()
        for word in words:
            # Skip common words but include potential company names
            if (len(word) > 2 and 
                (word[0].isupper() or 
                 any(char.isdigit() for char in word) or
                 word.lower() in ['tusd', 'k12', 'district', 'school'])):
                entities.append(word)
        
        return list(set(entities))  # Remove duplicates
    
    def search_communications(self, entities: list, emails: list) -> list:
        """Search for communications related to specific entities"""
        if not entities:
            return emails[:10]  # Return recent emails if no specific entities
        
        relevant_emails = []
        
        for email in emails:
            subject = email.get('subject', '').lower()
            body = email.get('body', '').lower()
            sender = email.get('from', '').lower()
            
            # Check if any entity appears in the email
            for entity in entities:
                entity_lower = entity.lower()
                if (entity_lower in subject or 
                    entity_lower in body or 
                    entity_lower in sender):
                    relevant_emails.append(email)
                    break
        
        return relevant_emails
    
    def analyze_communication_patterns(self, emails: list, entities: list) -> dict:
        """Analyze communication patterns to identify who needs to respond"""
        analysis = {
            'total_emails': len(emails),
            'entities_mentioned': entities,
            'communication_threads': {},
            'pending_responses': [],
            'last_activity': None
        }
        
        if not emails:
            return analysis
        
        # Group emails by thread/subject similarity
        threads = self.group_email_threads(emails)
        analysis['communication_threads'] = threads
        
        # Identify pending responses
        for thread_key, thread_emails in threads.items():
            if len(thread_emails) > 0:
                latest_email = thread_emails[0]  # Most recent
                
                # Simple heuristic: if latest email is a question or request
                if self.is_pending_response(latest_email):
                    analysis['pending_responses'].append({
                        'thread': thread_key,
                        'latest_email': latest_email,
                        'waiting_on': self.identify_who_should_respond(latest_email, thread_emails)
                    })
        
        analysis['last_activity'] = emails[0]['date'] if emails else None
        
        return analysis
    
    def group_email_threads(self, emails: list) -> dict:
        """Group emails into conversation threads"""
        threads = {}
        
        for email in emails:
            subject = email.get('subject', '')
            # Clean subject (remove Re:, Fwd:, etc.)
            clean_subject = re.sub(r'^(Re:|Fwd:|RE:|FWD:)\s*', '', subject, flags=re.IGNORECASE).strip()
            
            if clean_subject not in threads:
                threads[clean_subject] = []
            threads[clean_subject].append(email)
        
        # Sort each thread by date (most recent first)
        for thread_key in threads:
            threads[thread_key].sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return threads
    
    def is_pending_response(self, email: dict) -> bool:
        """Determine if an email is waiting for a response"""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        
        # Look for question indicators
        question_indicators = ['?', 'please', 'need', 'request', 'can you', 'could you', 'would you']
        
        return any(indicator in subject or indicator in body for indicator in question_indicators)
    
    def identify_who_should_respond(self, latest_email: dict, thread_emails: list) -> str:
        """Identify who should respond to the communication"""
        sender = latest_email.get('from', '')
        
        # Simple logic: if it's from external domain, internal team should respond
        if '@' in sender:
            domain = sender.split('@')[1] if '@' in sender else ''
            if any(internal_domain in domain for internal_domain in ['company.com', 'internal.com']):
                return "External party (client/prospect)"
            else:
                return "Internal team member"
        
        return "Unknown"
    
    def find_stuck_communications(self, emails: list, entities: list) -> list:
        """Find communications that appear to be stuck"""
        stuck = []
        
        # Group by threads and find old unanswered emails
        threads = self.group_email_threads(emails)
        
        for thread_key, thread_emails in threads.items():
            if len(thread_emails) > 0:
                latest_email = thread_emails[0]
                
                # Check if it's been a while since last activity
                try:
                    email_date = datetime.strptime(latest_email['date'][:25], '%a, %d %b %Y %H:%M:%S')
                    days_ago = (datetime.now() - email_date).days
                    
                    if days_ago > 3 and self.is_pending_response(latest_email):
                        stuck.append({
                            'thread': thread_key,
                            'days_waiting': days_ago,
                            'latest_email': latest_email,
                            'waiting_on': self.identify_who_should_respond(latest_email, thread_emails)
                        })
                except:
                    pass  # Skip if date parsing fails
        
        return sorted(stuck, key=lambda x: x['days_waiting'], reverse=True)
    
    def format_communication_response(self, analysis: dict, entities: list) -> str:
        """Format the communication analysis into a readable response"""
        entity_text = f" related to {', '.join(entities)}" if entities else ""
        
        response = f"📧 I found {analysis['total_emails']} communications{entity_text}.\n\n"
        
        if analysis['pending_responses']:
            response += "🔍 **Communications needing attention:**\n"
            for pending in analysis['pending_responses']:
                response += f"• **{pending['thread']}**\n"
                response += f"  - Waiting on: {pending['waiting_on']}\n"
                response += f"  - From: {pending['latest_email'].get('from', 'Unknown')}\n"
                response += f"  - Date: {pending['latest_email'].get('date', 'Unknown')}\n\n"
        else:
            response += "✅ No communications appear to be waiting for responses.\n\n"
        
        if analysis['last_activity']:
            response += f"🕐 Last activity: {analysis['last_activity']}"
        
        return response
    
    def format_bottleneck_response(self, stuck_communications: list) -> str:
        """Format stuck communications into a readable response"""
        if not stuck_communications:
            return "✅ No stuck communications found."
        
        response = f"⚠️ Found {len(stuck_communications)} potentially stuck communications:\n\n"
        
        for stuck in stuck_communications[:5]:  # Show top 5
            response += f"🚫 **{stuck['thread']}**\n"
            response += f"   - Waiting {stuck['days_waiting']} days\n"
            response += f"   - Needs response from: {stuck['waiting_on']}\n"
            response += f"   - From: {stuck['latest_email'].get('from', 'Unknown')}\n\n"
        
        return response
    
    def handle_status_query(self, query: str) -> str:
        """Handle status-related queries"""
        if not self.current_project_data:
            return "I don't have project data loaded. Please load a project first."
        
        # Use Claude for intelligent status analysis
        context = self.get_chat_context()
        prompt = f"""
        User is asking about project status: "{query}"
        
        Current project: {self.current_project_data.get('name', 'Unknown')}
        Recent emails: {len(self.current_emails)}
        
        Provide a concise status update based on available data.
        """
        
        return self.ask_claude(prompt, context)
    
    def handle_responsibility_query(self, query: str) -> str:
        """Handle queries about who is responsible for what"""
        entities = self.extract_entities(query)
        
        if not self.current_project_data and not self.current_emails:
            return "I need project or email data to identify responsibilities."
        
        # Analyze current data for responsibility information
        response = "👥 **Responsibility Analysis:**\n\n"
        
        if self.current_emails:
            # Find most active participants
            participants = {}
            for email in self.current_emails[:20]:  # Recent emails
                sender = email.get('from', '')
                if sender:
                    participants[sender] = participants.get(sender, 0) + 1
            
            if participants:
                response += "📊 **Most active in communications:**\n"
                sorted_participants = sorted(participants.items(), key=lambda x: x[1], reverse=True)
                for sender, count in sorted_participants[:5]:
                    response += f"• {sender}: {count} emails\n"
        
        return response
    
    def handle_general_query(self, query: str) -> str:
        """Handle general queries using Claude"""
        context = self.get_chat_context()
        
        prompt = f"""
        User query: "{query}"
        
        Available data:
        - Project: {self.current_project_data.get('name') if self.current_project_data else 'None loaded'}
        - Emails: {len(self.current_emails)} available
        - Chat history: {len(self.chat_memory)} messages
        
        Provide a helpful response based on available data. If you need more specific data, suggest what the user should load or ask for.
        """
        
        return self.ask_claude(prompt, context)
    
    def get_chat_context(self) -> str:
        """Get recent chat context for Claude"""
        context = ""
        
        # Include recent chat history
        recent_chats = self.chat_memory[-6:]  # Last 6 messages
        if recent_chats:
            context += "Recent conversation:\n"
            for chat in recent_chats:
                role = "User" if chat['type'] == 'user' else "Assistant"
                context += f"{role}: {chat['content'][:100]}...\n"
        
        return context
    
    def load_project_data(self, project_name: str = None) -> str:
        """Load project data for analysis"""
        try:
            if not self.connected:
                return "❌ Cannot load project data - Google Sheets not connected"
            
            projects = self.get_project_tabs()
            if not projects:
                return "❌ No projects found"
            
            # If no specific project name, show available projects
            if not project_name:
                response = "📋 Available projects:\n"
                for num, project in projects.items():
                    response += f"{num}. {project['name']}\n"
                response += "\nUse 'load project [number]' to load a specific project."
                return response
            
            # Try to find project by name or number
            project_num = None
            if project_name.isdigit():
                project_num = int(project_name)
            else:
                # Search by name
                for num, project in projects.items():
                    if project_name.lower() in project['name'].lower():
                        project_num = num
                        break
            
            if project_num and project_num in projects:
                self.current_project_data = self.get_project_data(project_num)
                if self.current_project_data:
                    return f"✅ Loaded project: {self.current_project_data['name']}"
                else:
                    return "❌ Failed to load project data"
            else:
                return f"❌ Project '{project_name}' not found"
                
        except Exception as e:
            return f"❌ Error loading project: {e}"
    
    def load_emails(self, project_name: str = None, days_back: int = 30) -> str:
        """Load emails for analysis"""
        try:
            # Get email credentials
            email_address = os.getenv('EMAIL_ADDRESS')
            password = os.getenv('EMAIL_PASSWORD')
            
            if not email_address or not password:
                return "❌ Email credentials not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file."
            
            if not self.setup_email_connection(email_address, password):
                return "❌ Failed to connect to email"
            
            search_term = project_name or (self.current_project_data['name'] if self.current_project_data else "")
            if not search_term:
                return "❌ No project specified for email search"
            
            self.current_emails = self.search_project_emails(search_term, days_back)
            return f"✅ Loaded {len(self.current_emails)} emails for '{search_term}'"
            
        except Exception as e:
            return f"❌ Error loading emails: {e}"
    
    def start_chat(self):
        """Start the conversational chat interface"""
        print("\n💬 Hawk Chat Agent - Conversational Interface")
        print("=" * 50)
        print("Ask me about communications, project status, or who needs to respond!")
        print("Commands:")
        print("  • 'load project [name/number]' - Load project data")
        print("  • 'load emails [project]' - Load email data")
        print("  • 'help' - Show available commands")
        print("  • 'quit' - Exit chat")
        print("\nExample queries:")
        print("  • 'Do you see any communication related to tusd?'")
        print("  • 'Who is the communication hung on?'")
        print("  • 'What communications are stuck?'")
        print("  • 'Show me the project status'")
        print()
        
        while True:
            try:
                user_input = input("🦅 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower().startswith('load project'):
                    project_name = user_input[12:].strip() if len(user_input) > 12 else None
                    response = self.load_project_data(project_name)
                    print(f"🤖 Hawk: {response}\n")
                    continue
                
                if user_input.lower().startswith('load emails'):
                    project_name = user_input[11:].strip() if len(user_input) > 11 else None
                    response = self.load_emails(project_name)
                    print(f"🤖 Hawk: {response}\n")
                    continue
                
                # Process the query
                response = self.process_query(user_input)
                print(f"🤖 Hawk: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def show_help(self):
        """Show help information"""
        print("""
💡 **Hawk Chat Agent Help**

**Commands:**
• `load project [name/number]` - Load project data from Google Sheets
• `load emails [project]` - Load email data for analysis
• `help` - Show this help message
• `quit` - Exit the chat

**Example Queries:**
• "Do you see any communication related to tusd?"
• "Who is the communication hung on?"
• "What communications are stuck or blocked?"
• "Show me the project status"
• "Who should respond to the latest emails?"
• "Are there any pending responses?"

**Tips:**
• Load project data first for better analysis
• Load emails to analyze communication patterns
• Be specific about company/project names in your queries
• Use quotes around specific terms: "tusd" or "K12"
        """)

if __name__ == "__main__":
    agent = HawkChatAgent()
    agent.start_chat()