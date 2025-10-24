#!/usr/bin/env python3
"""
Setup script for Google Sheets API credentials
"""
import json
import os

def create_credentials_template():
    """Create a template for Google service account credentials"""
    template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }
    
    with open('credentials_template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("📝 Created credentials_template.json")
    print("\n🔧 Setup Instructions:")
    print("1. Go to Google Cloud Console")
    print("2. Create a new project or select existing")
    print("3. Enable Google Sheets API and Google Drive API")
    print("4. Create a service account")
    print("5. Download the JSON key file")
    print("6. Rename it to 'credentials.json' in this directory")
    print("7. Share your Google Sheet with the service account email")

def check_credentials():
    """Check if credentials file exists"""
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        return True
    else:
        print("❌ credentials.json not found")
        print("Please follow the setup instructions")
        return False

if __name__ == "__main__":
    print("🦅 Hawk Agent - Credentials Setup")
    print("=" * 35)
    
    if not check_credentials():
        create_credentials_template()
    else:
        print("Credentials are ready!")
        print("You can now run: python hawk_agent.py")