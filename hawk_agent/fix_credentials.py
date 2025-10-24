#!/usr/bin/env python3
"""
Fix credentials.json private key formatting
"""
import json
import re

def fix_private_key():
    """Fix the private key formatting in credentials.json"""
    try:
        # Read the credentials file
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        # Check if private_key exists
        if 'private_key' not in creds:
            print("❌ No private_key found in credentials.json")
            return False
        
        private_key = creds['private_key']
        
        # Fix common formatting issues
        # Replace literal \n with actual newlines
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
            print("✅ Fixed \\n characters in private key")
        
        # Ensure proper BEGIN/END format
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key doesn't start with proper header")
            return False
        
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            print("❌ Private key doesn't end with proper footer")
            return False
        
        # Update the credentials
        creds['private_key'] = private_key
        
        # Write back to file
        with open('credentials.json', 'w') as f:
            json.dump(creds, f, indent=2)
        
        print("✅ Fixed credentials.json formatting")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing credentials: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing credentials.json formatting...")
    if fix_private_key():
        print("✅ Done! Try running the validator again.")
    else:
        print("❌ Could not fix credentials. Please check the file manually.")