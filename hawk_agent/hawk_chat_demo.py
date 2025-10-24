#!/usr/bin/env python3
"""
Hawk Chat Agent Demo - Works without real credentials
"""
import json
import re
from datetime import datetime, timedelta
import random

class HawkChatDemo:
    def __init__(self):
        self.chat_memory = []
        self.mock_emails = self.generate_mock_emails()
        self.mock_projects = {
            1: {"name": "TUSD K-12 Technology Initiative", "status": "In Progress"},
            2: {"name": "District Digital Transformation", "status": "Planning"},
            3: {"name": "School Safety Communication System", "status": "Testing"}
        }
        print("💬 Hawk Chat Demo initialized - Ready for conversation!")
    
    def generate_mock_emails(self):
        """Generate realistic mock email data"""
        emails = [
            {
                'subject': 'TUSD - Budget Approval Needed for Q4',
                'from': 'john.smith@tusd.edu',
                'date': (datetime.now() - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': 'Hi team, we need approval for the Q4 budget allocation for the technology initiative. Can someone from finance review this by Friday? Thanks, John'
            },
            {
                'subject': 'Re: TUSD Technology Rollout Timeline',
                'from': 'sarah.johnson@vendor.com',
                'date': (datetime.now() - timedelta(days=5)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': 'Following up on our discussion about the timeline. We are still waiting for confirmation on the deployment schedule. Please let us know your availability for next week.'
            },
            {
                'subject': 'TUSD - Network Infrastructure Questions',
                'from': 'mike.davis@tusd.edu',
                'date': (datetime.now() - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': 'I have some questions about the network infrastructure requirements. Could we schedule a call this week to discuss?'
            },
            {
                'subject': 'K12 Platform Integration Status',
                'from': 'lisa.wong@techpartner.com',
                'date': (datetime.now() - timedelta(days=7)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': 'The K12 platform integration is 80% complete. However, we need clarification on the authentication requirements before proceeding. Who should I contact for this?'
            },
            {
                'subject': 'URGENT: TUSD Security Compliance Review',
                'from': 'compliance@tusd.edu',
                'date': (datetime.now() - timedelta(days=10)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': 'We need to complete the security compliance review by end of month. Several items are still pending review from the IT team.'
            }
        ]
        return emails
    
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
        elif any(keyword in query_lower for keyword in ['stuck', 'blocked', 'waiting', 'pending', 'hung']):
            response = self.handle_bottleneck_query(user_query)
        elif any(keyword in query_lower for keyword in ['who', 'responsible', 'owner', 'respond']):
            response = self.handle_responsibility_query(user_query)
        elif any(keyword in query_lower for keyword in ['status', 'progress', 'update']):
            response = self.handle_status_query(user_query)
        else:
            response = self.handle_general_query(user_query)
        
        # Store response in chat memory
        self.chat_memory.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'assistant',
            'content': response
        })
        
        return response
    
    def extract_entities(self, query: str) -> list:
        """Extract potential company/project names from query"""
        entities = []
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted)
        
        # Look for specific terms
        words = query.split()
        for word in words:
            if (len(word) > 2 and 
                (word.lower() in ['tusd', 'k12', 'district', 'school'] or
                 word[0].isupper())):
                entities.append(word)
        
        return list(set(entities))
    
    def search_communications(self, entities: list, emails: list) -> list:
        """Search for communications related to specific entities"""
        if not entities:
            return emails[:5]  # Return recent emails if no specific entities
        
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
    
    def handle_communication_query(self, query: str) -> str:
        """Handle queries about communications and emails"""
        entities = self.extract_entities(query)
        relevant_emails = self.search_communications(entities, self.mock_emails)
        
        if not relevant_emails:
            entity_text = f" related to {', '.join(entities)}" if entities else ""
            return f"I don't see any recent communications{entity_text} in the email data."
        
        entity_text = f" related to {', '.join(entities)}" if entities else ""
        response = f"📧 I found {len(relevant_emails)} communications{entity_text}:\n\n"
        
        for i, email in enumerate(relevant_emails[:3], 1):
            response += f"{i}. **{email['subject']}**\n"
            response += f"   From: {email['from']}\n"
            response += f"   Date: {email['date']}\n"
            response += f"   Preview: {email['body'][:100]}...\n\n"
        
        # Analyze who needs to respond
        pending = self.analyze_pending_responses(relevant_emails)
        if pending:
            response += "⚠️ **Communications needing attention:**\n"
            for item in pending:
                response += f"• {item}\n"
        
        return response
    
    def handle_bottleneck_query(self, query: str) -> str:
        """Handle queries about stuck/blocked communications"""
        entities = self.extract_entities(query)
        stuck_communications = self.find_stuck_communications(entities)
        
        if not stuck_communications:
            return "✅ I don't see any obviously stuck communications in the recent data."
        
        response = f"🚫 Found {len(stuck_communications)} potentially stuck communications:\n\n"
        
        for stuck in stuck_communications:
            response += f"**{stuck['subject']}**\n"
            response += f"• Waiting {stuck['days_waiting']} days for response\n"
            response += f"• From: {stuck['from']}\n"
            response += f"• Needs attention from: {stuck['waiting_on']}\n\n"
        
        return response
    
    def handle_responsibility_query(self, query: str) -> str:
        """Handle queries about who is responsible for what"""
        entities = self.extract_entities(query)
        
        # Analyze current communications for responsibility
        response = "👥 **Communication Responsibility Analysis:**\n\n"
        
        # Find who's been most active
        senders = {}
        for email in self.mock_emails:
            sender = email['from']
            senders[sender] = senders.get(sender, 0) + 1
        
        response += "📊 **Most active in communications:**\n"
        for sender, count in sorted(senders.items(), key=lambda x: x[1], reverse=True):
            response += f"• {sender}: {count} emails\n"
        
        # Identify pending responses
        pending = self.analyze_pending_responses(self.mock_emails)
        if pending:
            response += "\n⏳ **Who needs to respond:**\n"
            for item in pending:
                response += f"• {item}\n"
        
        return response
    
    def handle_status_query(self, query: str) -> str:
        """Handle status-related queries"""
        response = "📊 **Project Status Overview:**\n\n"
        
        for num, project in self.mock_projects.items():
            response += f"{num}. **{project['name']}**\n"
            response += f"   Status: {project['status']}\n\n"
        
        response += f"📧 **Communication Summary:**\n"
        response += f"• Total emails analyzed: {len(self.mock_emails)}\n"
        response += f"• Most recent: {self.mock_emails[0]['date']}\n"
        response += f"• Oldest: {self.mock_emails[-1]['date']}\n"
        
        return response
    
    def handle_general_query(self, query: str) -> str:
        """Handle general queries"""
        return f"""I understand you're asking: "{query}"

I can help you with:
• Finding communications related to specific projects or companies
• Identifying who needs to respond to emails
• Spotting stuck or blocked communications
• Checking project status and progress

Try asking:
• "Do you see any communication related to TUSD?"
• "What communications are stuck?"
• "Who needs to respond?"
• "Show me the project status"

Currently loaded: {len(self.mock_emails)} mock emails for demonstration."""
    
    def analyze_pending_responses(self, emails: list) -> list:
        """Analyze which emails need responses"""
        pending = []
        
        for email in emails:
            subject = email['subject'].lower()
            body = email['body'].lower()
            
            # Look for indicators that a response is needed
            if any(indicator in subject or indicator in body 
                   for indicator in ['?', 'please', 'need', 'urgent', 'approval', 'confirm']):
                
                # Determine who should respond
                sender_domain = email['from'].split('@')[1] if '@' in email['from'] else ''
                if 'tusd.edu' in sender_domain:
                    waiting_on = "External vendor/partner"
                else:
                    waiting_on = "TUSD internal team"
                
                pending.append(f"'{email['subject']}' - waiting on {waiting_on}")
        
        return pending
    
    def find_stuck_communications(self, entities: list) -> list:
        """Find communications that appear to be stuck"""
        stuck = []
        
        for email in self.mock_emails:
            try:
                email_date = datetime.strptime(email['date'][:25], '%a, %d %b %Y %H:%M:%S')
                days_ago = (datetime.now() - email_date).days
                
                # If it's been more than 3 days and looks like it needs a response
                if days_ago > 3:
                    subject = email['subject'].lower()
                    body = email['body'].lower()
                    
                    if any(indicator in subject or indicator in body 
                           for indicator in ['?', 'please', 'need', 'urgent', 'waiting']):
                        
                        sender_domain = email['from'].split('@')[1] if '@' in email['from'] else ''
                        waiting_on = "TUSD team" if 'tusd.edu' not in sender_domain else "External party"
                        
                        stuck.append({
                            'subject': email['subject'],
                            'from': email['from'],
                            'days_waiting': days_ago,
                            'waiting_on': waiting_on
                        })
            except:
                continue
        
        return sorted(stuck, key=lambda x: x['days_waiting'], reverse=True)
    
    def start_chat(self):
        """Start the conversational chat interface"""
        print("\n💬 Hawk Chat Demo - Conversational Interface")
        print("=" * 50)
        print("🎭 Demo Mode: Using mock email data for TUSD project")
        print("\nAsk me about communications, project status, or who needs to respond!")
        print("\nExample queries:")
        print("  • 'Do you see any communication related to tusd?'")
        print("  • 'Who is the communication hung on?'")
        print("  • 'What communications are stuck?'")
        print("  • 'Show me the project status'")
        print("\nType 'help' for more commands or 'quit' to exit.\n")
        
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
💡 **Hawk Chat Demo Help**

**Example Queries:**
• "Do you see any communication related to tusd?"
• "Who is the communication hung on?"
• "What communications are stuck or blocked?"
• "Show me the project status"
• "Who should respond to the latest emails?"
• "Are there any pending responses?"

**Available Mock Data:**
• 5 sample emails related to TUSD project
• 3 mock projects with different statuses
• Realistic communication patterns

**Commands:**
• `help` - Show this help message
• `quit` - Exit the chat

**Note:** This is a demo version with mock data. The full version connects to real Google Sheets and Gmail.
        """)

if __name__ == "__main__":
    demo = HawkChatDemo()
    demo.start_chat()