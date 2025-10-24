#!/usr/bin/env python3
"""
Check and diagnose credentials.json issues
"""
import json
import os

def check_credentials_file():
    """Check the credentials.json file for common issues"""
    print("🔍 Checking credentials.json...")
    
    # Check if file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        print("📝 Please follow CREDENTIALS_SETUP.md to create it")
        return False
    
    # Check file size
    file_size = os.path.getsize('credentials.json')
    if file_size < 1000:
        print(f"⚠️  credentials.json is very small ({file_size} bytes)")
        print("   This might indicate placeholder content")
    
    # Check JSON format
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    
    print("✅ JSON format is valid")
    
    # Check required fields
    required_fields = [
        'type', 'project_id', 'private_key_id', 'private_key', 
        'client_email', 'client_id'
    ]
    
    missing_fields = []
    placeholder_fields = []
    
    for field in required_fields:
        if field not in creds:
            missing_fields.append(field)
        elif isinstance(creds[field], str):
            # Check for placeholder text
            value = creds[field].lower()
            if any(placeholder in value for placeholder in [
                'your-project', 'your_project', 'your-key', 'your_key',
                'your-client', 'your_client', 'placeholder', 'example'
            ]):
                placeholder_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    
    if placeholder_fields:
        print(f"❌ Placeholder text found in: {placeholder_fields}")
        print("   Please replace with actual values from Google Cloud Console")
        return False
    
    # Check service account type
    if creds.get('type') != 'service_account':
        print(f"❌ Wrong credential type: {creds.get('type')}")
        print("   Must be 'service_account'")
        return False
    
    # Check private key format
    private_key = creds.get('private_key', '')
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("❌ Private key doesn't start with proper header")
        return False
    
    if not private_key.endswith('-----END PRIVATE KEY-----\n'):
        print("❌ Private key doesn't end with proper footer")
        return False
    
    if 'YOUR_PRIVATE_KEY' in private_key:
        print("❌ Private key contains placeholder text")
        print("   Please use the actual private key from Google Cloud Console")
        return False
    
    # Check email format
    client_email = creds.get('client_email', '')
    if not client_email.endswith('.iam.gserviceaccount.com'):
        print(f"❌ Invalid service account email format: {client_email}")
        return False
    
    print("✅ All credential fields look valid")
    print(f"📧 Service account email: {client_email}")
    print(f"🏗️  Project ID: {creds.get('project_id')}")
    
    return True

def show_next_steps():
    """Show next steps based on credential status"""
    print("\n📋 Next Steps:")
    print("1. Make sure Google Sheets API is enabled in your Google Cloud project")
    print("2. Make sure Google Drive API is enabled in your Google Cloud project")
    print("3. Share your spreadsheet with the service account email")
    print("4. Run: python validate_credentials.py")

if __name__ == "__main__":
    print("🦅 Hawk Agent - Credentials Checker")
    print("=" * 40)
    
    if check_credentials_file():
        print("\n🎉 Credentials look good!")
        show_next_steps()
    else:
        print("\n🔧 Please fix the issues above")
        print("📖 See CREDENTIALS_SETUP.md for detailed instructions")