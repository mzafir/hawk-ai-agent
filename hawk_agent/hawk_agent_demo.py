#!/usr/bin/env python3
"""
Hawk Agent Demo - Works without real credentials for demonstration
"""
import pandas as pd
from datetime import datetime, timedelta
import random

class HawkAgentDemo:
    def __init__(self):
        self.spreadsheet_url = "https://docs.google.com/spreadsheets/d/1siruqibPS8fXtGiCvdhrSlcgsJPo4V5un2f-HpWt31M/edit?gid=0#gid=0"
        self.projects = {
            1: {"name": "Project Alpha - Mobile App Development", "status": "In Progress"},
            2: {"name": "Project Beta - Website Redesign", "status": "Planning"},
            3: {"name": "Project Gamma - Data Migration", "status": "Testing"}
        }
    
    def display_projects(self):
        """Display available projects"""
        print("\n🦅 Available Projects:")
        print("=" * 30)
        for num, project in self.projects.items():
            print(f"{num}. {project['name']}")
        return self.projects
    
    def generate_mock_spreadsheet_data(self, project_name):
        """Generate mock spreadsheet data"""
        tasks = [
            "Requirements Analysis", "Design Phase", "Development", 
            "Testing", "Deployment", "Documentation"
        ]
        statuses = ["Not Started", "In Progress", "Completed", "Blocked"]
        
        data = []
        for i, task in enumerate(tasks):
            data.append({
                "Task": task,
                "Status": random.choice(statuses),
                "Assigned To": f"Team Member {i+1}",
                "Due Date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "Priority": random.choice(["High", "Medium", "Low"])
            })
        
        return pd.DataFrame(data)
    
    def generate_mock_emails(self, project_name):
        """Generate mock email data"""
        subjects = [
            f"[{project_name}] Weekly Status Update",
            f"Re: {project_name} - Budget Approval",
            f"{project_name} - Timeline Discussion",
            f"Action Items from {project_name} Meeting",
            f"{project_name} - Risk Assessment"
        ]
        
        emails = []
        for i, subject in enumerate(subjects):
            emails.append({
                'subject': subject,
                'from': f'team.member{i+1}@company.com',
                'date': (datetime.now() - timedelta(days=i+1)).strftime("%a, %d %b %Y %H:%M:%S"),
                'body': f"This is a mock email about {project_name}. Status update and progress discussion..."
            })
        
        return emails
    
    def analyze_project_status(self, project_data, emails):
        """Analyze project status from spreadsheet and emails"""
        analysis = {
            'project_name': project_data['name'],
            'spreadsheet_status': self.analyze_spreadsheet_status(project_data['data']),
            'email_status': self.analyze_email_status(emails),
            'last_communication': self.get_last_communication(emails),
            'recommendations': []
        }
        
        # Generate recommendations based on analysis
        completed_tasks = len(project_data['data'][project_data['data']['Status'] == 'Completed'])
        total_tasks = len(project_data['data'])
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        if completion_rate < 0.3:
            analysis['recommendations'].append("⚠️ Low completion rate - consider resource reallocation")
        elif completion_rate > 0.8:
            analysis['recommendations'].append("🎉 High completion rate - project on track!")
        
        blocked_tasks = len(project_data['data'][project_data['data']['Status'] == 'Blocked'])
        if blocked_tasks > 0:
            analysis['recommendations'].append(f"🚫 {blocked_tasks} blocked tasks need attention")
        
        if len(emails) < 3:
            analysis['recommendations'].append("📧 Low email activity - consider follow-up")
        
        return analysis
    
    def analyze_spreadsheet_status(self, df):
        """Analyze status from spreadsheet data"""
        status_info = {
            'total_tasks': len(df),
            'status_distribution': df['Status'].value_counts().to_dict(),
            'completion_rate': f"{(len(df[df['Status'] == 'Completed']) / len(df) * 100):.1f}%"
        }
        return status_info
    
    def analyze_email_status(self, emails):
        """Analyze communication status from emails"""
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
        print("🦅 Hawk Agent Demo - Project Status Monitor")
        print("=" * 45)
        print("📝 Note: This is a demo version with mock data")
        print("   Real version connects to Google Sheets and Gmail")
        
        # Display projects
        projects = self.display_projects()
        
        # Get user selection
        try:
            choice = int(input("\nSelect project number: "))
            if choice not in projects:
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
        
        selected_project = projects[choice]
        print(f"\n📊 Analyzing project: {selected_project['name']}")
        
        # Generate mock data
        print("🔍 Fetching spreadsheet data...")
        spreadsheet_data = self.generate_mock_spreadsheet_data(selected_project['name'])
        
        print("📧 Searching emails...")
        emails = self.generate_mock_emails(selected_project['name'])
        
        # Prepare project data
        project_data = {
            'name': selected_project['name'],
            'data': spreadsheet_data
        }
        
        # Analyze and display results
        analysis = self.analyze_project_status(project_data, emails)
        self.display_analysis(analysis)
    
    def display_analysis(self, analysis):
        """Display analysis results"""
        print(f"\n🦅 HAWK ANALYSIS REPORT")
        print("=" * 50)
        print(f"Project: {analysis['project_name']}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 Spreadsheet Status:")
        ss_status = analysis['spreadsheet_status']
        print(f"  • Total Tasks: {ss_status['total_tasks']}")
        print(f"  • Completion Rate: {ss_status['completion_rate']}")
        print(f"  • Status Distribution:")
        for status, count in ss_status['status_distribution'].items():
            print(f"    - {status}: {count}")
        
        print(f"\n📧 Email Communication:")
        email_status = analysis['email_status']
        print(f"  • Total Emails: {email_status['total_emails']}")
        print(f"  • Date Range: {email_status['date_range']}")
        print(f"  • Recent Subjects:")
        for subject in email_status['recent_subjects']:
            print(f"    - {subject}")
        
        print(f"\n🕐 Last Communication:")
        last_comm = analysis['last_communication']
        print(f"  • Date: {last_comm['date']}")
        print(f"  • Subject: {last_comm['subject']}")
        print(f"  • From: {last_comm['from']}")
        
        if analysis['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n🔗 Spreadsheet URL: {self.spreadsheet_url}")

if __name__ == "__main__":
    agent = HawkAgentDemo()
    agent.run_analysis()