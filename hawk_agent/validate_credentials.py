#!/usr/bin/env python3
"""
Validate Google Sheets credentials
"""
import json
import os
import gspread
from google.oauth2.service_account import Credentials

def validate_credentials():
    """Validate the credentials.json file"""
    print("🔍 Validating credentials...")
    
    # Check if file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        return False
    
    # Check JSON format
    try:
        with open('credentials.json', 'r') as f:
            cred_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    
    # Check required fields
    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if field not in cred_data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Check if it's a service account
    if cred_data.get('type') != 'service_account':
        print("❌ Credentials must be for a service account")
        return False
    
    print("✅ Credentials format is valid")
    
    # Test connection
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        gc = gspread.authorize(creds)
        
        # Try to access the spreadsheet
        spreadsheet_id = "1siruqibPS8fXtGiCvdhrSlcgsJPo4V5un2f-HpWt31M"
        sheet = gc.open_by_key(spreadsheet_id)
        worksheets = sheet.worksheets()
        
        print("✅ Successfully connected to Google Sheets")
        print(f"📊 Found {len(worksheets)} worksheets:")
        for i, ws in enumerate(worksheets, 1):
            print(f"  {i}. {ws.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n💡 Possible solutions:")
        print("1. Make sure the spreadsheet is shared with your service account email")
        print("2. Check if Google Sheets API is enabled in your Google Cloud project")
        print("3. Verify the service account has proper permissions")
        return False

if __name__ == "__main__":
    print("🦅 Hawk Agent - Credentials Validator")
    print("=" * 40)
    
    if validate_credentials():
        print("\n🎉 All good! You can now run: python hawk_agent.py")
    else:
        print("\n🔧 Please fix the issues above and try again")